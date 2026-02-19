# DS18B20 Sensor Simulator for Raspberry Pi Pico

A complete MicroPython simulator for the Analog Devices DS18B20 temperature sensor, implementing the authentic 1-Wire protocol as specified in the datasheet.

## Features

- **Full 1-Wire Protocol Support**: ROM search, matching, temperature conversion
- **Accurate Sensor Simulation**: Scratchpad memory, CRC-8 validation, configurable resolution
- **Multiple Sensors**: Support for multiple DS18B20 sensors on the same 1-Wire bus
- **Configurable Resolution**: 9-12 bit temperature resolution (0.5°C to 0.0625°C)
- **Alarm Thresholds**: Programmable TH (high) and TL (low) temperature thresholds
- **Realistic Behavior**: Conversion times based on resolution (93.75ms to 750ms)
- **MicroPython Compatible**: Pure MicroPython, no external library dependencies
- **Educational**: Learn 1-Wire protocol and DS18B20 operation

## Hardware Setup

### GPIO Pin Configuration (Raspberry Pi Pico)

| Purpose | Pin | GPIO |
|---------|-----|------|
| 1-Wire Data Line | 0 | GPIO0 |
| Ground | N/A | GND |

### Wiring Diagram

```
Pico GPIO0 ----[4.7k]---- 3.3V
           |
        DS18B20 (DQ pin)
           |
        GND
```

Note: The 4.7k pull-up resistor is required for 1-Wire operation (open-drain protocol).

## Files

- **main.py** - Core simulator implementation
  - `DS18B20Sensor` - Single sensor simulation with full 1-Wire command support
  - `OneWireSimulator` - 1-Wire bus management for multiple sensors
  - Comprehensive 1-Wire command handling
  - CRC-8 calculation and validation
  - Realistic sensor behavior

- **example_usage.py** - Practical usage examples
  - Single sensor reading
  - Multiple sensor discovery and reading
  - Alarm threshold configuration
  - Resolution settings comparison
  - Continuous monitoring
  - Real hardware code examples

- **README.md** - This file

## Quick Start

### Basic Temperature Reading

```python
from main import DS18B20Sensor, OneWireSimulator, CONVERT_TEMP, READ_SCRATCHPAD
import time

# Create simulator
bus = OneWireSimulator()
sensor = DS18B20Sensor(current_temp=25.0)
bus.add_sensor(sensor)

# Use skip ROM for single sensor
bus.skip_rom()

# Convert temperature
bus.execute_command(CONVERT_TEMP)
time.sleep(0.8)  # Wait for conversion (12-bit mode)

# Read result
scratchpad = bus.execute_command(READ_SCRATCHPAD)
temp = sensor.get_temperature_celsius()
print("Temperature: {:.4f}C".format(temp))
```

### Multiple Sensors with Discovery

```python
from main import DS18B20Sensor, OneWireSimulator, CONVERT_TEMP, READ_SCRATCHPAD
import time

# Create bus with multiple sensors
bus = OneWireSimulator()
bus.add_sensor(DS18B20Sensor(current_temp=20.0))
bus.add_sensor(DS18B20Sensor(current_temp=25.0))

# Discover all devices
roms = bus.search_rom()

# Read from each sensor
for rom in roms:
    bus.reset()
    bus.match_rom(rom)
    bus.execute_command(CONVERT_TEMP)
    time.sleep(0.8)
    scratchpad = bus.execute_command(READ_SCRATCHPAD)
    # Extract temperature from RTC
    temp = (scratchpad[1] << 8 | scratchpad[0]) / 16.0
    print("Temperature: {:.4f}C".format(temp))
```

## 1-Wire Commands

All commands are implemented according to the DS18B20 datasheet:

### ROM Commands (for device addressing)
- `0xF0` - **SEARCH_ROM** - ROM search (device discovery)
- `0x33` - **READ_ROM** - Read ROM code (single device)
- `0x55` - **MATCH_ROM** - Select device by ROM code
- `0xCC` - **SKIP_ROM** - Select all devices (single device on bus)

### Memory & Sensor Commands
- `0x44` - **CONVERT_TEMP** - Initiate temperature conversion
- `0xBE` - **READ_SCRATCHPAD** - Read sensor data (9 bytes)
- `0x4E` - **WRITE_SCRATCHPAD** - Write TH, TL, CONFIG registers
- `0x48` - **COPY_SCRATCHPAD** - Write scratchpad to EEPROM
- `0xB8` - **RECALL_E2** - Copy EEPROM to scratchpad
- `0xB4` - **READ_POWER_SUPPLY** - Check power mode

## Scratchpad Memory Map

| Byte | Name | R/W | Description |
|------|------|-----|-------------|
| 0 | TEMP_LSB | R | Temperature LSB |
| 1 | TEMP_MSB | R | Temperature MSB |
| 2 | TH | R/W | High temperature alarm threshold |
| 3 | TL | R/W | Low temperature alarm threshold |
| 4 | CONFIG | R/W | Configuration register |
| 5-7 | Reserved | R | Reserved (always 0xFF, 0x00, 0x00) |
| 8 | CRC | R | CRC-8 of bytes 0-7 |

### Temperature Encoding

Temperature is stored as a 16-bit signed value:
- **Format**: [MSB] = sign and integer part, [LSB] = fractional part
- **Resolution**: LSB = 0.0625°C in 12-bit mode
- **Formula**: T = (MSB << 8 | LSB) / 16.0

**Examples**:
- 25°C   = 0x0190 (0x01, 0x90)
- -10°C  = 0xFFF6 (0xFF, 0xF6)

### Configuration Register (Byte 4)

```
Bit 7-6: Resolution
  00 = 9-bit  (0.5°C)      - 93.75ms conversion
  01 = 10-bit (0.25°C)     - 187.5ms conversion
  10 = 11-bit (0.125°C)    - 375ms conversion
  11 = 12-bit (0.0625°C)   - 750ms conversion [default]

Bit 5-4: Reserved (always 0)
Bit 3-0: Reserved (always 0)
```

## Temperature Specifications

| Parameter | Value |
|-----------|-------|
| Operating Range | -55°C to +125°C |
| Accuracy | ±0.5°C |
| Temp Coefficient | 0.0625°C/LSB |
| Conversion Time (9-bit) | 93.75ms |
| Conversion Time (10-bit) | 187.5ms |
| Conversion Time (11-bit) | 375ms |
| Conversion Time (12-bit) | 750ms |

## Usage Patterns

### Pattern 1: Single Sensor (SKIP_ROM)
```python
bus.skip_rom()
bus.execute_command(CONVERT_TEMP)
time.sleep(0.75)
scratchpad = bus.execute_command(READ_SCRATCHPAD)
```

Use when only one sensor is on the bus - saves time by skipping ROM addressing.

### Pattern 2: Multiple Sensors (MATCH_ROM)
```python
for rom in bus.search_rom():
    bus.reset()
    bus.match_rom(rom)
    bus.execute_command(CONVERT_TEMP)
    time.sleep(0.75)
    scratchpad = bus.execute_command(READ_SCRATCHPAD)
```

Use when multiple sensors are on the bus - discover all devices first, then address each individually.

### Pattern 3: Configure Alarms
```python
bus.match_rom(rom)
# TH=28°C, TL=20°C, 12-bit resolution
bus.execute_command(WRITE_SCRATCHPAD, bytes([28, 20, 0x7F]))
# Optionally copy to EEPROM
bus.execute_command(COPY_SCRATCHPAD)
```

Set temperature thresholds for alarm functionality.

## API Reference

### DS18B20Sensor Class

```python
sensor = DS18B20Sensor(rom_code=None, current_temp=20.0)

# Set simulated temperature
sensor.set_temperature(25.5)

# Get current temperature reading
temp = sensor.get_temperature_celsius()

# Get resolution in bits
bits = sensor.get_resolution_bits()  # Returns 9, 10, 11, or 12

# Access scratchpad directly
sensor.scratchpad.config = 0x7F
sensor.scratchpad.th = 28
sensor.scratchpad.tl = 20
```

### OneWireSimulator Class

```python
bus = OneWireSimulator()

# Add sensors
bus.add_sensor(sensor1)
bus.add_sensor(sensor2)

# ROM operations
roms = bus.search_rom()
bus.match_rom(rom)
bus.skip_rom()
bus.reset()

# Execute commands
result = bus.execute_command(CONVERT_TEMP)
scratchpad = bus.execute_command(READ_SCRATCHPAD)
bus.execute_command(WRITE_SCRATCHPAD, bytes([th, tl, config]))
```

## Constants

```python
# GPIO Pins
GPIO_ONEWIRE_1 = 0      # Primary 1-Wire sensor
GPIO_ONEWIRE_2 = 1      # Secondary 1-Wire sensor (optional)

# 1-Wire Timing (microseconds)
ONEWIRE_RESET_TIME = 480
ONEWIRE_PRESENCE_TIME = 60
ONEWIRE_BIT_TIME = 60

# Command Codes
CONVERT_TEMP = 0x44
READ_SCRATCHPAD = 0xBE
WRITE_SCRATCHPAD = 0x4E
# ... etc

# Resolution Bits
RES_9BIT = 0b00
RES_10BIT = 0b01
RES_11BIT = 0b10
RES_12BIT = 0b11
```

## Testing

Run the main simulator:
```bash
python3 main.py          # CPython (for testing)
micropython main.py      # On Raspberry Pi Pico
```

Run usage examples:
```bash
python3 example_usage.py
```

## Real Hardware Integration

To use with real DS18B20 sensors on a Raspberry Pi Pico:

```python
import onewire
import ds18x20
import machine
import time

# Create 1-Wire bus
ow = onewire.OneWire(machine.Pin(0))

# Create DS18X20 object
ds = ds18x20.DS18X20(ow)

# Scan for devices
roms = ds.scan()

# Convert and read temperature
ds.convert_temp()
time.sleep(0.8)
for rom in roms:
    temp = ds.read_temp(rom)
    print("Temperature: {:.4f}C".format(temp))
```

## References

- [DS18B20 Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf) - Official Analog Devices documentation
- [1-Wire Protocol](https://en.wikipedia.org/wiki/1-Wire) - Wikipedia overview
- [Raspberry Pi Pico Datasheet](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf)
- MicroPython Documentation: `onewire` and `ds18x20` libraries

## License

See LICENSE file in workspace

## Notes

- This simulator is designed for testing and educational purposes
- Timing is simulated and not cycle-accurate; use for logic validation
- For hardware timing-critical applications, use real 1-Wire library
- ROM codes are randomly generated; set specific codes for deterministic testing
- Scratchpad CRC is calculated automatically on reads
