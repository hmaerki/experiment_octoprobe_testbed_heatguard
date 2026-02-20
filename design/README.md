# Design

## Task

* simulate OneWire
* simulate I2C

* diag protocol
* Write testenvironement, pytest, fixtures
* diag protocol & pytest

## Simulate OneWire

* https://www.raspberrypi.com/documentation/microcontrollers/images/pico2w-pinout.svg
* https://www.elektronik-kompendium.de/sites/praxis/bauteil_ds18b20.htm

| Signal | Pico A | Pico B | Comment |
| - | - | - | - |
| OneWire | GP16 | GP16 | Pullup |
| SDA | GP14 | GP14 | Pullup |
| SCL | GP15 | GP15 | Pullup |