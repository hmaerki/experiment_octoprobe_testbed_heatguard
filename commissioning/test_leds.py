import time

import machine

LED_ENABLE = "GPIO26"
LED_OK = "GPIO27"
LED_FAILURE = "GPIO28"
LED_GUARD = "GPIO29"

while True:
    for gpio in (LED_ENABLE, LED_OK, LED_FAILURE, LED_GUARD):
        print(gpio)
        pin = machine.Pin(gpio, machine.Pin.OUT)
        pin.value(1)
        time.sleep(0.5)
        pin.value(0)
