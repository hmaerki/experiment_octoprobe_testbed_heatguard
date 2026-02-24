""" """

import time

import machine

uart = machine.UART(
    0,
    baudrate=9600,
    tx=machine.Pin("GPIO16"),
    rx=machine.Pin("GPIO17"),
)

while True:
    uart.write("Hello from PICO_INFRA\n")
    msg = uart.read()
    if msg is not None:
        print(msg.decode(), end="")
    time.sleep(1)
