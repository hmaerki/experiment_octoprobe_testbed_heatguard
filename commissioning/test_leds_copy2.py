import machine
import time


LED_ENABLE = "GPIO12"
LED_OK = "GPIO13"

gpiosa = ("GPIO10", "GPIO12", "GPIO14", "GPIO16")
gpiosb = ("GPIO11", "GPIO13", "GPIO15", "GPIO17")

a, b = gpiosa, gpiosb
while True:
    print(a)
    for gpio in a:
        pin = machine.Pin(gpio, machine.Pin.OUT)
        pin.value(1)
    for gpio in b:
        pin = machine.Pin(gpio, machine.Pin.OUT)
        pin.value(0)
    time.sleep(2.0)
    a, b = b, a
