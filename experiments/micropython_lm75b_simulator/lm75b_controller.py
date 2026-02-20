"""
Simple MicroPython program to read temperature from LM75B sensor
on Raspberry Pi Pico using I2C
SDA: GPIO16
SCL: GPIO17
"""

from machine import Pin, I2C
import time


# Temperature register address
TEMP_REG = 0x00

# Initialize I2C (I2C0 with SDA on GPIO16, SCL on GPIO17)
pin_sda=Pin(16)
pin_scl=Pin(17)
i2c = I2C(0, sda=pin_sda, scl=pin_scl, freq=400000)
# Pin(pin_scl, Pin.OPEN_DRAIN, Pin.PULL_UP)
# Pin(pin_sda, Pin.OPEN_DRAIN, Pin.PULL_UP)


def scan_i2c():
    """Scan for I2C devices"""
    print("Scanning I2C bus...")
    devices = i2c.scan()

    if len(devices) == 0:
        print("No I2C devices found!")
    else:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(f"  - 0x{device:02x}")

    return devices


def read_temperature(addr: int):
    """Read temperature from LM75B sensor"""
    # Read 2 bytes from temperature register
    data = i2c.readfrom_mem(addr, TEMP_REG, 2)

    # Convert to temperature (11-bit resolution)
    # Combine the two bytes and shift right by 5 bits
    temp_raw = (data[0] << 8 | data[1]) >> 5

    # Check if negative (bit 10 is sign bit)
    if temp_raw & 0x400:
        temp_raw = temp_raw - 0x800

    # Convert to Celsius (0.125°C per LSB)
    temperature = temp_raw * 0.125

    return temperature


# Main loop
print("LM75B Temperature Sensor Reader")
print("SDA: GPIO16, SCL: GPIO17")
print("-" * 30)

# Scan for I2C devices
devices = scan_i2c()


print("\nStarting temperature readings...")
print("-" * 30)

while True:
    for addr in (0x4B, 0x4F):
        try:
            temp = read_temperature(addr=addr)
            print(f"Temperature 0x{addr:02X}: {temp:.3f} °C")
        except Exception as e:
            print(f"Temperature 0x{addr:02X}: {e}")

    time.sleep(1)
