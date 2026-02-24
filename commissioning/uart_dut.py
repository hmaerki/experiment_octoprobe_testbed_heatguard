""" """

import time

import machine

uart = machine.UART(
    0,
    baudrate=9600,
    tx=machine.Pin("GPIO0"),
    rx=machine.Pin("GPIO1"),
)

while True:
    uart.write("Hello from DUT\n")
    msg = uart.read()
    if msg is not None:
        print(msg.decode(), end="")
    time.sleep(1)
