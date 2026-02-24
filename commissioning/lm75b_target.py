"""
Simple MicroPython program to simulate an LM75B temperature sensor
using I2CTarget (I2C slave mode) on Raspberry Pi Pico
"""

import machine
import time

LM75B_ADDR = 0x4C


class Lm75B:
    def __init__(self, addr: int, sda: machine.Pin, scl: machine.Pin) -> None:
        self.mem = bytearray(8)

        self.i2c = machine.I2CTarget(
            0,
            sda=sda,
            scl=scl,
            mem=self.mem,
            addr=addr,
        )

    def set_temperature(self, temperature_C: float) -> None:
        """Convert temperature to LM75B format (11-bit, 0.125°C resolution)"""
        temperature_raw = int(temperature_C / 0.125)

        if temperature_raw < 0:
            temperature_raw = temperature_raw + 0x800

        # Shift left by 5 bits (11-bit value in upper bits of 16-bit word)
        temperature_raw = temperature_raw << 5

        # Split into two bytes (MSB first)
        msb = (temperature_raw >> 8) & 0xFF
        lsb = temperature_raw & 0xFF

        self.mem[0] = msb
        self.mem[1] = lsb


lm75b = Lm75B(addr=LM75B_ADDR, sda=machine.Pin("GPIO12"), scl=machine.Pin("GPIO13"))
while True:
    for offset_C in range(10):
        temperature_C = 20.0 + offset_C
        lm75b.set_temperature(temperature_C)
        print(f"{temperature_C:0.3f}C")
        time.sleep(1.0)
