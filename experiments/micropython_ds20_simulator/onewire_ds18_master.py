"""
DS18B20 Temperature Sensor Reader

MicroPython example for Raspberry Pi Pico that reads temperature
from a DS18B20 sensor connected to GPIO16.

Hardware Setup:
- GPIO16: 1-Wire data line
- Pull-up resistor: 4.7kΩ to 3.3V
- DS18B20 sensor with:
  - DQ pin (data) → GPIO16
  - GND → GND
  - VDD (optional for parasitic power) → 3.3V

Wiring:
  Pico 3.3V ----[4.7k]---- GPIO16
                             |
                          DS18B20
                          (DQ pin)
                             |
                           GND
"""

import time

import ds18x20
import machine
import onewire

# Configuration
ONEWIRE_PIN = "GPIO16"
READING_INTERVAL = 2  # Seconds between readings


def setup_onewire():
    """Initialize the 1-Wire bus"""
    pin = machine.Pin(ONEWIRE_PIN)
    ow = onewire.OneWire(pin)
    ds = ds18x20.DS18X20(ow)
    return ow, ds


def scan_sensors(ds):
    """Scan for DS18B20 sensors on the bus"""
    roms = ds.scan()
    if not roms:
        print("No DS18B20 sensors found!")
        return None

    print(f"Found {len(roms)} sensor(s):")
    for i, rom in enumerate(roms, 1):
        rom_hex = rom.hex() if hasattr(rom, "hex") else "".join(f"{b:02X}" for b in rom)
        print(f"  Sensor {i}: {rom_hex}")

    return roms


def read_temperatures(ds, roms):
    """Read temperature from all sensors"""
    if not roms:
        return

    # Trigger conversion on all sensors
    ds.convert_temp()

    # Wait for conversion to complete (750ms for 12-bit resolution)
    time.sleep_ms(750)

    # Read temperature from each sensor
    for i, rom in enumerate(roms, 1):
        temp = ds.read_temp(rom)
        print(f"  Sensor {i}: {temp:.2f}°C")


def main():
    """Main loop - continuously read and display temperatures"""
    print("=" * 50)
    print("DS18B20 Temperature Reader")
    print("=" * 50)
    print(f"GPIO{ONEWIRE_PIN}: 1-Wire Bus")
    print(f"Reading interval: {READING_INTERVAL}s")
    print()

    try:
        # Setup 1-Wire bus
        ow, ds = setup_onewire()

        # Scan for sensors
        if True:
            roms = scan_sensors(ds)
            print(f"{roms=}")
            time.sleep_ms(1000)

        if not roms:
            print("Cannot proceed without sensors. Exiting.")
            return

        print("\nStarting temperature readings...\n")

        # Main loop
        count = 0
        while True:
            count += 1
            timestamp = time.time()

            print(f"[{count}] Reading at {timestamp}:")
            read_temperatures(ds, roms)
            print()

            # Wait for next reading
            time.sleep(READING_INTERVAL)

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
