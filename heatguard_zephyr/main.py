"""
This is micropython code for
the Raspberry Pi Pico (RP2040).
"""

import errno
import time

import machine  # type: ignore
import micropython  # type: ignore
import rp2  # type: ignore

# ab
micropython.alloc_emergency_exception_buf(100)

I2C_ADDRESS_Tguard = 0x48
I2C_ADDRESS_Tref = 0x49
I2C_ADDRESS_EEPROM = 0x50
I2C_ADDRESS_OFFSET_DISCONNECT = 4

BOOT_CAUSE = {
    machine.PWRON_RESET: "PWRON_RESET",
    machine.WDT_RESET: "WDT_RESET",
}.get(machine.reset_cause(), "UNKNOWN")


def print_error(error_text: str) -> None:
    assert isinstance(error_text, str)
    print("[ERROR]" + repr(error_text))


class Watchdog:
    TIMEOUT_MS = 3_000

    def __init__(self) -> None:
        self.wdt: machine.WDT | None = None

    def start(self) -> None:
        self.wdt = machine.WDT(timeout=self.TIMEOUT_MS)

    def feed(self) -> None:
        if self.wdt is None:
            return

        self.wdt.feed()

    @staticmethod
    def stop() -> None:
        """
        The watchdog should never be stopped.
        However, when starting a debug session, the watchdog is unwanted.
        """

        WATCHDOG_CTRL = 0x40058000
        "Address for the Watchdog Control Register"

        current_val = machine.mem32[WATCHDOG_CTRL]
        # Use a bitmask to clear bit 30 (the ENABLE bit)
        # 0x3FFFFFFF is a mask where all bits are 1 except bit 30
        machine.mem32[WATCHDOG_CTRL] = current_val & 0x3FFFFFFF


class Leds:
    def __init__(self) -> None:
        self.enable = machine.Pin("GPIO26", machine.Pin.OUT)
        self.ok = machine.Pin("GPIO27", machine.Pin.OUT)
        self.failure = machine.Pin("GPIO28", machine.Pin.OUT)
        self.guard = machine.Pin("GPIO29", machine.Pin.OUT)
        self.all = (self.enable, self.ok, self.failure, self.guard)
        # XIAO RP2040 onboard green LED (active LOW: 0=on, 1=off)
        self.xiao_inverse_green = machine.Pin("GPIO16", machine.Pin.OUT, value=1)
        self.xiao_inverse_red = machine.Pin("GPIO17", machine.Pin.OUT, value=1)
        self.xiao_inverse_blue = machine.Pin("GPIO25", machine.Pin.OUT, value=1)

    def set_all(self, on: bool = True) -> None:
        for pin in self.all:
            pin.value(on)

    def blink_leds(self) -> None:
        for pin in self.all:
            pin.value(1)
            time.sleep(0.2)
            pin.value(0)


class Diag:
    def __init__(self) -> None:
        self._uart = machine.UART(
            0,
            baudrate=9600,
            tx=machine.Pin("GPIO0"),
            rx=machine.Pin("GPIO1"),
            timeout=100,
        )

    def readline(self) -> str | None:
        if self._uart.any() == 0:
            return None
        return self._uart.readline().decode("utf-8", "replace").strip()

    def writeline(self, line) -> None:
        self._uart.write(line + "\n")

    def ping_forever(self) -> None:
        for i in range(1_000_000):
            msg = f"ping {i}"
            print(msg)
            self.writeline(msg)
            time.sleep(1.0)


class I2C:
    TEMP_REG = 0x00
    "Temperature register address"

    def __init__(self) -> None:
        pin_sda = machine.Pin("GPIO6")
        pin_scl = machine.Pin("GPIO7")
        self._i2c = machine.I2C(1, sda=pin_sda, scl=pin_scl, freq=400_000)

    def scan_i2c(self) -> list[int]:
        """
        Scan for I2C devices
        """
        print("Scanning I2C bus...")
        devices = self._i2c.scan()

        if len(devices) == 0:
            print("No I2C devices found!")
        else:
            print(f"Found {len(devices)} device(s):")
            for device in devices:
                print(f"  - 0x{device:02x}")

        return devices

    def read_temperature(self, addr: int) -> float:
        """
        Read temperature from LM75B sensor.
        Throw an exception if failed.
        """
        # Read 2 bytes from temperature register
        data = self._i2c.readfrom_mem(addr, self.TEMP_REG, 2)

        # Convert to temperature (11-bit resolution)
        # Combine the two bytes and shift right by 5 bits
        temp_raw = (data[0] << 8 | data[1]) >> 5

        # Check if negative (bit 10 is sign bit)
        if temp_raw & 0x400:
            temp_raw = temp_raw - 0x800

        # Convert to Celsius (0.125°C per LSB)
        temperature = temp_raw * 0.125

        return temperature

    def read_temperature_remote(self, addr: int) -> float:
        """
        Read temperature from LM75B sensor.
        If failed, write 'print_error()'.
        This is useful for mpremote calls.
        """
        try:
            return self.read_temperature(addr=addr)
        except OSError as e:
            if e.errno == errno.EIO:
                print_error("I2C_EIO")
                return 0.0
            raise

    def read_EEPROM(self, addr: int) -> str:
        """
        Throw an exception if failed.
        """
        # Read 2 bytes from temperature register
        EEPROM_START_BYTE = 0x00
        EEPROM_SIZE_BYTE = 0x200
        "2 Kbit = 0x800 bits = 0x200 bytes"
        data = self._i2c.readfrom_mem(addr, EEPROM_START_BYTE, EEPROM_SIZE_BYTE)

        pos = data.find(b"\xff")
        if pos >= 0:
            data = data[0:pos]
        return data.decode("utf-8", "replace")

    def read_EEPROM_remote(self, addr: int) -> str:
        """
        If failed, write 'print_error()'.
        This is useful for mpremote calls.
        """
        try:
            return self.read_EEPROM(addr=addr)
        except OSError as e:
            if e.errno == errno.EIO:
                print_error("I2C_EIO")
                return ""
            raise

    def write_EEPROM(self, addr: int, data: str) -> None:
        """
        Write data string to EEPROM.
        Throw an exception if failed.
        """
        EEPROM_START_BYTE = 0x00
        PAGE_SIZE = 16
        encoded = data.encode("utf-8")
        offset = 0
        while offset < len(encoded):
            chunk = encoded[offset : offset + PAGE_SIZE]
            self._i2c.writeto_mem(addr, EEPROM_START_BYTE + offset, chunk)
            time.sleep(0.005)  # 5ms EEPROM write cycle
            offset += PAGE_SIZE


class HeatGuardState:
    STATE_INIT = "INIT"
    STATE_OK = "OK"
    STATE_FAILURE = "FAILURE"
    STATE_GUARD = "GUARD"

    GUARD_RECOVERY_MS = 60_000

    def __init__(self) -> None:
        self.state: str = self.STATE_INIT
        self.enable: bool = False
        self.before_state = self.state
        self.before_enable = self.enable
        self.leds_state = (leds.ok, leds.failure, leds.guard)
        self.last_reason: str = "Initial state after power up"
        self.guard_end_ms: int = time.ticks_ms()  # type: ignore

    def _guard_end_reset(self):
        self.guard_end_ms: int = time.ticks_add(time.ticks_ms(), self.GUARD_RECOVERY_MS)  # type: ignore

    @property
    def guard_remaining_ms(self) -> int:
        return time.ticks_diff(self.guard_end_ms, time.ticks_ms())  # type: ignore

    def sensor_failed(self, sensor: str) -> None:
        self._guard_end_reset()
        if self.state == (self.STATE_INIT, self.STATE_GUARD):
            return
        self.last_reason = f"I2C failed for sensor {sensor}!"
        self.state = self.STATE_FAILURE

    def update_temperatures(self, temperature_Tguard_C: float, diff_C: float) -> None:
        if self.state in (self.STATE_INIT, self.STATE_GUARD):
            return

        if temperature_Tguard_C >= 80.0:
            # Guard condition
            self._guard_end_reset()
            if self.state in (self.STATE_OK, self.STATE_FAILURE):
                self.last_reason = f"Too hot! Activate guard: temperature_Tguard_C={temperature_Tguard_C:0.3f}C"
                self.state = self.STATE_GUARD
                return

        if diff_C >= 3.0:
            # Failure condition
            self.last_reason = f"Temperature difference too high: diff_C={diff_C:0.3f}C"
            self.state = self.STATE_FAILURE
            return

        self.last_reason = ""
        self.state = self.STATE_OK

    def handle_diag(self, diag: Diag) -> None:
        line_diag = diag.readline()
        if line_diag is None:
            return
        self._handle_diag_line(line_diag=line_diag)

    def _handle_diag_line(self, line_diag: str) -> None:
        assert isinstance(line_diag, str)
        STIMULUS_HEATGUARD = "stimulus heatguard."
        if line_diag.startswith(STIMULUS_HEATGUARD):
            # Example line_diag:
            # stimulus heatguard.update_temperatures(temperature_Tguard_C=90.0, diff_C=0.0)
            cmd = line_diag.replace(STIMULUS_HEATGUARD, "heatguard.")
            eval(cmd, {"heatguard": self})
            self.update()
            return
        if line_diag == "inject timeover":
            self.guard_end_ms: int = time.ticks_ms()  # type: ignore
            self.update()
            return
        if line_diag == "inject endless_loop":
            # This will force the watchdog to fire
            while True:
                pass
        if line_diag == "ping":
            diag.writeline("pong 'response to ping'")
            return
        raise ValueError(f"line_diag not recognized: {line_diag}")

    def update(self) -> None:
        def update_state() -> None:
            if self.state == self.STATE_INIT:
                self.state = self.STATE_OK
            if self.state == self.STATE_GUARD:
                if self.guard_remaining_ms < 0:
                    # After some timeout we recover
                    self.state = self.STATE_OK

            self.enable = self.state == self.STATE_OK
            leds.enable.value(self.enable)
            leds.ok.value(self.state == self.STATE_OK)
            leds.failure.value(self.state == self.STATE_FAILURE)
            leds.guard.value(self.state == self.STATE_GUARD)

        update_state()
        if (self.enable, self.state) != (self.before_enable, self.before_state):
            self.before_enable, self.before_state = self.enable, self.state
            self.write_state(reason=self.last_reason)
            self.last_reason = ""
            if self.state == self.STATE_GUARD:
                i2c.write_EEPROM(addr=I2C_ADDRESS_EEPROM, data=repr({"state": "GUARD"}))

    def write_state(self, reason: str) -> None:
        msg = f"probe state {self.state} {self.enable} '{reason}'"
        print(msg)
        diag.writeline(msg)


watchdog = Watchdog()
i2c = I2C()
diag = Diag()
leds = Leds()
heatguard = HeatGuardState()


def main() -> None:
    print("main()")
    watchdog.start()
    leds.set_all(on=True)
    time.sleep(0.01)
    leds.set_all(on=False)

    diag.writeline(f"probe boot {BOOT_CAUSE}")

    while True:
        heatguard.handle_diag(diag=diag)
        heatguard.update()
        watchdog.feed()
        time.sleep(1)
        leds.xiao_inverse_blue.toggle()
        try:
            temperature_Tguard_C = i2c.read_temperature(addr=I2C_ADDRESS_Tguard)
        except OSError:
            heatguard.sensor_failed("Tguard")
            continue
        try:
            temperature_Tref_C = i2c.read_temperature(addr=I2C_ADDRESS_Tref)
        except OSError:
            heatguard.sensor_failed("Tref")
            continue
        try:
            _ = i2c.read_EEPROM(addr=I2C_ADDRESS_EEPROM)
        except OSError:
            heatguard.sensor_failed("eeprom")
            continue

        diff_C = abs(temperature_Tguard_C - temperature_Tref_C)
        elements = [
            f"Tguard={temperature_Tguard_C:0.3f}C",
            f"Tref={temperature_Tref_C:0.3f}C",
            f"diff={diff_C:0.3f}",
            f"state={heatguard.state}",
            f"enable={heatguard.enable}",
            f"guard_remaining_ms={max(-1, heatguard.guard_remaining_ms)}",
        ]
        print(" ".join(elements))
        heatguard.update_temperatures(
            temperature_Tguard_C=temperature_Tguard_C,
            diff_C=diff_C,
        )


RUN_MAIN = True
try:
    rp2.SKIP_MAIN  # noqa: B018
    RUN_MAIN = False
    # The watchdog might still be active
    Watchdog.stop()
except AttributeError:
    pass

if RUN_MAIN:
    main()
