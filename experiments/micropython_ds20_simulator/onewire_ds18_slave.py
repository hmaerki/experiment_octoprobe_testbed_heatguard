"""
DS18B20 1-Wire Slave Implementation for Raspberry Pi Pico (PIO-based)

This file contains MicroPython code running on a Raspberry Pi Pico.

GPIO Configuration:
- GPIO16: Connected to a 1-Wire bus (open-drain with 4.7k pull-up)

This Pico acts as a 1-WIRE SLAVE and emulates two DS18B20 temperature sensors:
- Sensor 1: ROM 28 5A 3F 7B 05 00 00 0F → 18°C
- Sensor 2: ROM 28 5A 3F 7B 05 00 00 00 → 12°C

IMPLEMENTATION: Uses PIO (Programmable I/O) for microsecond-precision timing
instead of bit-banging, eliminating garbage collector jitter.

Reference: https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf

The implementation handles:
- 1-Wire reset and presence pulse detection (PIO)
- Bit-level read/write with timer-based pulse discrimination (PIO)
- ROM identification and matching (SEARCH_ROM, MATCH_ROM, SKIP_ROM)
- Temperature conversion requests
- Scratchpad memory read/write operations
"""

import time

import machine
import rp2
from micropython import const

# ============================================================================
# GPIO Configuration
# ============================================================================

ONEWIRE_PIN = 16  # 1-Wire data line (GPIO16)

# ============================================================================
# 1-Wire Timing Constants (microseconds)
# ============================================================================

RESET_LOW_TIME = const(480)  # Master reset pulse duration (480-960 µs)
RESET_THRESHOLD = const(240)  # Threshold to distinguish reset from write pulses
PRESENCE_DELAY = const(30)  # Delay before responding with presence
PRESENCE_PULSE_TIME = const(60)  # Our presence pulse duration
READ_SAMPLE_TIME = const(15)  # Time to read bit during read slot
WRITE_0_TIME = const(60)  # Hold time for writing 0
WRITE_1_TIME = const(15)  # Hold time for writing 1 (minimal)
BIT_SLOT_TIME = const(60)  # Total time per bit slot


# @rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH)
@rp2.asm_pio()
def onewire_read_byte():
    """
    Read one byte from 1-Wire bus by measuring pulse durations.

    Loop 8 times - read one byte 'data':
    - Wait for master to pull line low (read slot initiated)
    - Count instruction cycles while line is low
    - If counter exhausted (>30µs): bit = 1, otherwise bit = 0
    - Accumulate bit into 'data'

    After 8 bits: Push complete byte to RX FIFO for Python
    """
    mov(y, 7)  # Loop counter: read 8 bits (0-7)
    mov(isr, 0)  # Clear input shift register for bit accumulation

    label("read_bit")
    # Wait for falling edge (master initiates bit slot)
    wait(0, pin, 0)

    # Measure pulse duration using instruction counter
    # At 125MHz: 30µs ≈ 3750 instruction cycles
    mov(x, 3750)

    label("count_while_low")
    # If pin went high, end timing measurement
    jmp(pin, "end_measurement")
    # Otherwise decrement counter and continue
    jmp(x_dec, "count_while_low")

    label("end_measurement")
    # x == 0: counter exhausted, pulse >= 30µs → bit = 1
    # x > 0: pin went high before counter exhausted, pulse < 30µs → bit = 0

    # Jump if x is zero (counter exhausted, pulse was long)
    jmp(not_x, "bit_is_one")

    # x > 0: counter still had value, so pulse was short → bit = 0
    mov(osr, 0)
    jmp("shift_bit")

    label("bit_is_one")
    # x == 0: counter exhausted → bit = 1
    mov(osr, 1)

    label("shift_bit")
    # Shift bit into input shift register (accumulates LSB first)
    in_(osr, 1)

    # Decrement y and loop if more bits to read
    jmp(y_dec, "read_bit")

    # All 8 bits accumulated in ISR, push byte to FIFO
    push()


@rp2.asm_pio()
def onewire_sample_byte():
    """
    Read one byte from 1-Wire bus by sampling bits at 30µs after falling edge.
    
    Loop 8 times:
    1. Wait for pin HIGH (idle)
    2. Wait for pin LOW (slot starts)
    3. Delay 30µs
    4. Sample pin value and accumulate into byte
    
    After 8 bits: Push complete byte to RX FIFO
    """
    label("start_byte")
    # Initialize loop counter for 8 bits (0-7)
    set(y, 7)

    label("read_bit")
    # 1. Wait for pin to go HIGH (idle state between bit slots)
    wait(1, pin, 0)

    # 2. Wait for pin to go LOW (master initiates bit slot)
    wait(0, pin, 0)

    # 3. Delay for 30µs to sample point
    # At 1MHz: 1 cycle = 1µs, need 30 cycles total
    # set(x, N) = 1 cycle, loop runs N+1 cycles
    # Total = 1 + (N+1) = N+2 cycles
    # For 30 cycles: N = 28
    set(x, 28)
    label("delay")
    jmp(x_dec, "delay")  # Loop 29 times (1 cycle each)

    # 4. Sample the pin value (1 bit) and shift into ISR (LSB first)
    in_(pins, 1)

    # Decrement bit counter and loop if more bits to read
    jmp(y_dec, "read_bit")

    # All 8 bits accumulated in ISR, push byte to FIFO
    push()

    # Loop back to read next byte
    jmp("start_byte")


@rp2.asm_pio()
def low_pulse_counter():
    """
    Continuously measure negative pulse durations on 1-Wire bus.
    Pushes pulse duration (in PIO cycles) to RX FIFO for each pulse.
    """

    # 1. Wait for pin to go LOW (negative pulse starts)
    label("wait_low")
    wait(0, pin, 0)

    # 2. Initialize Y register to 0, then invert to get 0xFFFFFFFF (max counter)
    set(y, 0)
    mov(y, invert(y))

    # 3. Counting Loop: count cycles while pin stays LOW
    label("loop")
    jmp(pin, "pulse_ended")  # 1 cycle. If pin goes HIGH, the pulse is over
    jmp(y_dec, "loop")  # 1 cycle. Decrement Y and keep looping if pin is still LOW

    label("pulse_ended")
    # 4. Push the pulse duration (0xFFFFFFFF - Y) to the RX FIFO
    mov(isr, invert(y))
    push(noblock)  # Use noblock to avoid stalling if FIFO is full

    # 5. Wait for pin to go HIGH before looking for next pulse
    wait(1, pin, 0)

    # 6. Loop back to wait for next LOW pulse
    jmp("wait_low")


@rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH)
def onewire_reset_presence():
    """
    Detect a reset pulse (>= 300us low) and generate presence pulse.

    Sequence:
    - Wait for line to be HIGH (idle)
    - Wait for line to go LOW
    - Count LOW time and confirm >= 300us
    - Wait 60us
    - Pull LOW for 240us
    - Release line and repeat
    """
    label("wait_high")
    wait(1, pin, 0)

    label("wait_low")
    wait(0, pin, 0)

    # Count at least 300us low (1MHz => 1 cycle = 1us)
    set(x, 300)
    label("count_low")
    jmp(pin, "wait_high")
    jmp(x_dec, "count_low")

    # Reset detected, wait 60us before presence
    set(x, 59)
    label("delay_60")
    jmp(x_dec, "delay_60")  # Decrement Y and jump if Y != 0 (60 iterations)

    push(noblock)  # Use noblock to avoid stalling if FIFO is full




    # # Pull low for 240us presence pulse
    # set(pins, 0)
    # set(y, 239)
    # label("hold_240")
    # jmp(y_dec, "hold_240")
    # set(pins, 1)

    # jmp("wait_high")
    # label("not_reset")
    # jmp("wait_high")





# ============================================================================
# 1-Wire Slave Implementation (Hardware-Backed)
# ============================================================================


class OneWireSlave:
    """1-Wire Slave implementation using PIO for precise timing"""

    def __init__(self, pin_num):
        self.pin_num = pin_num
        # self.pin = machine.Pin(pin_num, machine.Pin.OPEN_DRAIN, machine.Pin.PULL_UP)
        self.pin = machine.Pin(pin_num, machine.Pin.OPEN_DRAIN, None)

        # Initialize PIO
        self.sm = None
        self.init_pio()

    def init_pio(self):
        """
        Initialize PIO state machine for 1-Wire protocol

        https://docs.micropython.org/en/latest/library/rp2.html
        https://docs.micropython.org/en/latest/library/rp2.StateMachine.html
        """
        # Use PIO block 0, state machine 0
        # Use GPIO pin number (not Pin object) to preserve open-drain configuration
        self.sm = rp2.StateMachine(
            0,
            low_pulse_counter,
            freq=10_000_000,  # 1 MHz: 1 cycle = 1 µs
            set_base=self.pin,
            in_base=self.pin,
            jmp_pin=self.pin,
        )
        self.sm.active(1)

    def run(self):
        print(f"\n1-Wire Reset/Presence on GPIO{self.pin_num}")
        print("Listening for reset pulses and generating presence...\n")

        while True:
            # Read byte value from PIO (blocks until complete byte arrives)
            byte_value = self.sm.get()
            print(f"Byte: 0x{byte_value:02X} ({byte_value}) bin:{byte_value:08b}")
            time.sleep(1)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    slave = OneWireSlave(ONEWIRE_PIN)
    slave.run()
