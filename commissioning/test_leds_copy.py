import machine
import time


LED_ENABLE = "GPIO6"
LED_OK = "GPIO7"


while True:
    for gpio in (LED_ENABLE, LED_OK):
        print(gpio)
        pin = machine.Pin(gpio, machine.Pin.OUT)
        pin.value(1)
        time.sleep(2.0)
        pin.value(0)
