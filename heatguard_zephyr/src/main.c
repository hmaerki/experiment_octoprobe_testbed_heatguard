/*
 * heatguard – Zephyr C port of the MicroPython heatguard application.
 *
 * Target: Raspberry Pi Pico (RP2040) / XIAO RP2040
 *
 * Peripherals
 *   UART0  115200 baud GPIO0/1  – diagnostic / stimulus interface
 *   I2C1   400 kHz    GPIO6/7  – LM75B temperature sensors + EEPROM
 *   GPIO26-29                  – status LEDs (enable / ok / failure / guard)
 *   GPIO16,17,25               – XIAO onboard LEDs (active-low)
 *   WDT                        – 3 s hardware watchdog
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/drivers/hwinfo.h>
#include <hardware/structs/watchdog.h>

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---------- constants ---------------------------------------------------- */

#define I2C_ADDRESS_TGUARD 0x48
#define I2C_ADDRESS_TREF   0x49
#define I2C_ADDRESS_EEPROM 0x50

#define TEMP_REG 0x00

#define EEPROM_START_BYTE 0x00
#define EEPROM_SIZE_BYTE  0x200
#define EEPROM_PAGE_SIZE  16

#define GUARD_RECOVERY_MS 60000
#define WATCHDOG_TIMEOUT_MS 3000

/* GPIO pin numbers (accent on gpio0 bank) */
#define LED_ENABLE_PIN     26
#define LED_OK_PIN         27
#define LED_FAILURE_PIN    28
#define LED_GUARD_PIN      29
#define LED_XIAO_GREEN_PIN 16 /* active-low */
#define LED_XIAO_RED_PIN   17 /* active-low */
#define LED_XIAO_BLUE_PIN  25 /* active-low */

/* ---------- state machine ------------------------------------------------ */

enum heatguard_state {
	STATE_INIT,
	STATE_OK,
	STATE_FAILURE,
	STATE_GUARD,
};

static const char *state_names[] = {
	[STATE_INIT]    = "INIT",
	[STATE_OK]      = "OK",
	[STATE_FAILURE] = "FAILURE",
	[STATE_GUARD]   = "GUARD",
};

/* ---------- devices ------------------------------------------------------ */

static const struct device *gpio0_dev;
static const struct device *i2c1_dev;
static const struct device *uart0_dev;
static const struct device *wdt_dev;
static int wdt_channel_id = -1;

/* ---------- heatguard state ---------------------------------------------- */

static struct {
	enum heatguard_state state;
	bool enable;
	enum heatguard_state before_state;
	bool before_enable;
	char last_reason[128];
	int64_t guard_end_ms;
} hg;

/* ---------- UART RX buffer ----------------------------------------------- */

#define UART_BUF_SIZE 256
static char uart_rx_buf[UART_BUF_SIZE];
static int  uart_rx_pos;

/* ========================================================================= */
/*  Boot cause                                                               */
/* ========================================================================= */

static const char *get_boot_cause(void)
{
	/*
	 * The Zephyr hwinfo driver for RP2040 does not map watchdog resets
	 * to RESET_WATCHDOG (only RP2350 does).  On RP2040 a WDT reset
	 * triggers a PSM restart which the driver reports as RESET_DEBUG.
	 *
	 * Use the RP2040 watchdog reason register directly: bit 0 (TIMER)
	 * is set after a watchdog timeout, bit 1 (FORCE) after a forced reset.
	 */
	if (watchdog_hw->reason & (WATCHDOG_REASON_TIMER_BITS |
				   WATCHDOG_REASON_FORCE_BITS)) {
		return "WDT_RESET";
	}

	uint32_t cause;

	if (hwinfo_get_reset_cause(&cause) < 0) {
		return "UNKNOWN";
	}

	if (cause & RESET_POR) {
		return "PWRON_RESET";
	}
	return "UNKNOWN";
}

/* ========================================================================= */
/*  Watchdog                                                                 */
/* ========================================================================= */

static int watchdog_start(void)
{
	struct wdt_timeout_cfg cfg = {
		.window.min = 0,
		.window.max = WATCHDOG_TIMEOUT_MS,
		.callback   = NULL,
		.flags      = WDT_FLAG_RESET_SOC,
	};

	wdt_dev = DEVICE_DT_GET(DT_NODELABEL(wdt0));
	if (!device_is_ready(wdt_dev)) {
		printk("Watchdog device not ready\n");
		return -1;
	}

	wdt_channel_id = wdt_install_timeout(wdt_dev, &cfg);
	if (wdt_channel_id < 0) {
		printk("Watchdog install failed: %d\n", wdt_channel_id);
		return wdt_channel_id;
	}

	return wdt_setup(wdt_dev, WDT_OPT_PAUSE_HALTED_BY_DBG);
}

static void watchdog_feed(void)
{
	if (wdt_channel_id >= 0) {
		wdt_feed(wdt_dev, wdt_channel_id);
	}
}

/* ========================================================================= */
/*  LEDs                                                                     */
/* ========================================================================= */

static void leds_init(void)
{
	gpio0_dev = DEVICE_DT_GET(DT_NODELABEL(gpio0));
	if (!device_is_ready(gpio0_dev)) {
		printk("GPIO0 device not ready\n");
		return;
	}

	gpio_pin_configure(gpio0_dev, LED_ENABLE_PIN,     GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure(gpio0_dev, LED_OK_PIN,         GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure(gpio0_dev, LED_FAILURE_PIN,    GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure(gpio0_dev, LED_GUARD_PIN,      GPIO_OUTPUT_INACTIVE);
	/* XIAO onboard LEDs are active-low → start OFF (pin high) */
	gpio_pin_configure(gpio0_dev, LED_XIAO_GREEN_PIN, GPIO_OUTPUT_ACTIVE);
	gpio_pin_configure(gpio0_dev, LED_XIAO_RED_PIN,   GPIO_OUTPUT_ACTIVE);
	gpio_pin_configure(gpio0_dev, LED_XIAO_BLUE_PIN,  GPIO_OUTPUT_ACTIVE);
}

static void leds_set_all(bool on)
{
	int v = on ? 1 : 0;

	gpio_pin_set(gpio0_dev, LED_ENABLE_PIN,  v);
	gpio_pin_set(gpio0_dev, LED_OK_PIN,      v);
	gpio_pin_set(gpio0_dev, LED_FAILURE_PIN, v);
	gpio_pin_set(gpio0_dev, LED_GUARD_PIN,   v);
}

/* ========================================================================= */
/*  UART diagnostics                                                         */
/* ========================================================================= */

static void diag_init(void)
{
	uart0_dev = DEVICE_DT_GET(DT_NODELABEL(uart0));
	if (!device_is_ready(uart0_dev)) {
		printk("UART0 device not ready\n");
	}
	uart_rx_pos = 0;
}

static void diag_writeline(const char *line)
{
	while (*line) {
		uart_poll_out(uart0_dev, *line++);
	}
	uart_poll_out(uart0_dev, '\n');
}

static bool diag_readline(char *buf, size_t buf_size)
{
	unsigned char c;

	while (uart_poll_in(uart0_dev, &c) == 0) {
		if (c == '\n' || c == '\r') {
			if (uart_rx_pos > 0) {
				uart_rx_buf[uart_rx_pos] = '\0';
				strncpy(buf, uart_rx_buf, buf_size - 1);
				buf[buf_size - 1] = '\0';
				uart_rx_pos = 0;
				return true;
			}
		} else if (uart_rx_pos < UART_BUF_SIZE - 1) {
			uart_rx_buf[uart_rx_pos++] = (char)c;
		}
	}
	return false;
}

/* ========================================================================= */
/*  I2C helpers                                                              */
/* ========================================================================= */

static void i2c_bus_init(void)
{
	i2c1_dev = DEVICE_DT_GET(DT_NODELABEL(i2c1));
	if (!device_is_ready(i2c1_dev)) {
		printk("I2C1 device not ready\n");
	}
}

static int i2c_read_temperature(uint8_t addr, float *temp_out)
{
	uint8_t reg = TEMP_REG;
	uint8_t data[2];
	int ret;

	ret = i2c_write_read(i2c1_dev, addr, &reg, 1, data, 2);
	if (ret < 0) {
		return ret;
	}

	/* LM75B: 11-bit two's-complement, upper 11 bits of 16-bit register */
	int raw = ((data[0] << 8) | data[1]) >> 5;

	if (raw & 0x400) {
		raw -= 0x800;
	}

	*temp_out = raw * 0.125f;
	return 0;
}

static int i2c_read_eeprom(uint8_t addr, char *buf, size_t buf_size)
{
	uint8_t reg = EEPROM_START_BYTE;
	uint8_t data[EEPROM_SIZE_BYTE];
	int ret;

	ret = i2c_write_read(i2c1_dev, addr, &reg, 1, data, sizeof(data));
	if (ret < 0) {
		return ret;
	}

	/* Trim at first 0xFF byte */
	size_t len = sizeof(data);

	for (size_t i = 0; i < sizeof(data); i++) {
		if (data[i] == 0xFF) {
			len = i;
			break;
		}
	}

	if (len >= buf_size) {
		len = buf_size - 1;
	}
	memcpy(buf, data, len);
	buf[len] = '\0';
	return 0;
}

static int i2c_write_eeprom(uint8_t addr, const char *str)
{
	size_t total  = strlen(str);
	size_t offset = 0;

	while (offset < total) {
		size_t chunk = total - offset;

		if (chunk > EEPROM_PAGE_SIZE) {
			chunk = EEPROM_PAGE_SIZE;
		}

		uint8_t buf[EEPROM_PAGE_SIZE + 1];

		buf[0] = (uint8_t)(EEPROM_START_BYTE + offset);
		memcpy(&buf[1], &str[offset], chunk);

		int ret = i2c_write(i2c1_dev, buf, chunk + 1, addr);

		if (ret < 0) {
			return ret;
		}

		k_msleep(5); /* EEPROM write-cycle time */
		offset += EEPROM_PAGE_SIZE;
	}
	return 0;
}

/* ========================================================================= */
/*  HeatGuard state machine                                                  */
/* ========================================================================= */

static void guard_end_reset(void)
{
	hg.guard_end_ms = k_uptime_get() + GUARD_RECOVERY_MS;
}

static int64_t guard_remaining_ms(void)
{
	return hg.guard_end_ms - k_uptime_get();
}

static void write_state(const char *reason)
{
	char msg[256];

	snprintf(msg, sizeof(msg), "probe state %s %s '%s'",
		 state_names[hg.state], hg.enable ? "True" : "False", reason);
	diag_writeline(msg);
}

static void heatguard_init(void)
{
	hg.state        = STATE_INIT;
	hg.enable       = false;
	hg.before_state = STATE_INIT;
	hg.before_enable = false;
	strncpy(hg.last_reason, "Initial state after power up",
		sizeof(hg.last_reason));
	hg.guard_end_ms = k_uptime_get();
}

static void heatguard_update(void)
{
	if (hg.state == STATE_INIT) {
		hg.state = STATE_OK;
	}
	if (hg.state == STATE_GUARD && guard_remaining_ms() < 0) {
		hg.state = STATE_OK;
	}

	hg.enable = (hg.state == STATE_OK);

	gpio_pin_set(gpio0_dev, LED_ENABLE_PIN,  hg.enable);
	gpio_pin_set(gpio0_dev, LED_OK_PIN,      hg.state == STATE_OK);
	gpio_pin_set(gpio0_dev, LED_FAILURE_PIN, hg.state == STATE_FAILURE);
	gpio_pin_set(gpio0_dev, LED_GUARD_PIN,   hg.state == STATE_GUARD);

	if (hg.enable != hg.before_enable || hg.state != hg.before_state) {
		hg.before_enable = hg.enable;
		hg.before_state  = hg.state;
		write_state(hg.last_reason);
		hg.last_reason[0] = '\0';

		if (hg.state == STATE_GUARD) {
			i2c_write_eeprom(I2C_ADDRESS_EEPROM,
					 "{'state': 'GUARD'}");
		}
	}
}

static void heatguard_sensor_failed(const char *sensor)
{
	guard_end_reset();

	if (hg.state == STATE_INIT || hg.state == STATE_GUARD) {
		return;
	}

	snprintf(hg.last_reason, sizeof(hg.last_reason),
		 "I2C failed for sensor %s!", sensor);
	hg.state = STATE_FAILURE;
}

static void heatguard_update_temperatures(float t_guard, float diff)
{
	if (hg.state == STATE_INIT || hg.state == STATE_GUARD) {
		return;
	}

	if (t_guard >= 80.0f) {
		guard_end_reset();
		if (hg.state == STATE_OK || hg.state == STATE_FAILURE) {
			snprintf(hg.last_reason, sizeof(hg.last_reason),
				 "Too hot! Activate guard: "
				 "temperature_Tguard_C=%.3fC",
				 (double)t_guard);
			hg.state = STATE_GUARD;
			return;
		}
	}

	if (diff >= 3.0f) {
		snprintf(hg.last_reason, sizeof(hg.last_reason),
			 "Temperature difference too high: diff_C=%.3fC",
			 (double)diff);
		hg.state = STATE_FAILURE;
		return;
	}

	hg.last_reason[0] = '\0';
	hg.state = STATE_OK;
}

/* ========================================================================= */
/*  Diagnostic command handler                                               */
/* ========================================================================= */

static void handle_diag_line(const char *line)
{
	float tguard, diff;

	if (sscanf(line,
		   "stimulus heatguard.update_temperatures("
		   "temperature_Tguard_C=%f, diff_C=%f)",
		   &tguard, &diff) == 2) {
		heatguard_update_temperatures(tguard, diff);
		heatguard_update();
		return;
	}

	if (strncmp(line, "stimulus heatguard.sensor_failed(", 33) == 0) {
		char sensor[32] = {0};

		if (sscanf(line,
			   "stimulus heatguard.sensor_failed(\"%31[^\"]\")",
			   sensor) == 1) {
			heatguard_sensor_failed(sensor);
			heatguard_update();
		}
		return;
	}

	if (strcmp(line, "inject timeover") == 0) {
		hg.guard_end_ms = k_uptime_get();
		heatguard_update();
		return;
	}

	if (strcmp(line, "inject endless_loop") == 0) {
		/* Deliberate infinite loop – the watchdog will reset the MCU */
		for (;;) {
		}
	}

	if (strcmp(line, "ping") == 0) {
		diag_writeline("pong 'response to ping'");
		return;
	}

	printk("diag line not recognised: %s\n", line);
}

static void handle_diag(void)
{
	char buf[UART_BUF_SIZE];

	if (diag_readline(buf, sizeof(buf))) {
		handle_diag_line(buf);
	}
}

/* ========================================================================= */
/*  main                                                                     */
/* ========================================================================= */

int main(void)
{
	printk("main()\n");

	leds_init();
	diag_init();
	i2c_bus_init();
	heatguard_init();
	watchdog_start();

	/* Brief flash of all status LEDs */
	leds_set_all(true);
	k_msleep(10);
	leds_set_all(false);

	char boot_msg[64];

	snprintf(boot_msg, sizeof(boot_msg), "probe boot %s",
		 get_boot_cause());
	diag_writeline(boot_msg);

	while (1) {
		handle_diag();
		heatguard_update();

		watchdog_feed();
		k_msleep(1000);
		watchdog_feed();

		gpio_pin_toggle(gpio0_dev, LED_XIAO_BLUE_PIN);

		float t_guard, t_ref;
		char eeprom_buf[EEPROM_SIZE_BYTE + 1];

		if (i2c_read_temperature(I2C_ADDRESS_TGUARD, &t_guard) < 0) {
			heatguard_sensor_failed("Tguard");
			heatguard_update();
			continue;
		}
		if (i2c_read_temperature(I2C_ADDRESS_TREF, &t_ref) < 0) {
			heatguard_sensor_failed("Tref");
			heatguard_update();
			continue;
		}
		if (i2c_read_eeprom(I2C_ADDRESS_EEPROM,
				    eeprom_buf, sizeof(eeprom_buf)) < 0) {
			heatguard_sensor_failed("eeprom");
			heatguard_update();
			continue;
		}

		float diff = fabsf(t_guard - t_ref);
		int64_t remaining = guard_remaining_ms();

		if (remaining < -1) {
			remaining = -1;
		}

		char telemetry[256];

		snprintf(telemetry, sizeof(telemetry),
			 "Tguard=%.3fC Tref=%.3fC diff=%.3f "
			 "state=%s enable=%d guard_remaining_ms=%lld",
			 (double)t_guard, (double)t_ref, (double)diff,
			 state_names[hg.state], hg.enable,
			 (long long)remaining);
		diag_writeline(telemetry);

		heatguard_update_temperatures(t_guard, diff);
	}

	return 0;
}
