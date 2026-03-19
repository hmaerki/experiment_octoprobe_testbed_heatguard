import _thread
import time

import machine


class Uart:
    def __init__(self) -> None:
        self._uart = machine.UART(
            0,
            baudrate=9600,
            tx=machine.Pin("GPIO16"),
            rx=machine.Pin("GPIO17"),
        )
        self._rx_line: bytes = b""
        self._rx_queue: list[str] = []
        self._uart.irq(handler=self._irq_handler, trigger=machine.UART.IRQ_RXIDLE)

    def _irq_handler(self, uart_obj) -> None:
        data = uart_obj.read()
        if data is None:
            return
        self._rx_line += data
        while b"\n" in self._rx_line:
            line, self._rx_line = self._rx_line.split(b"\n", 1)
            self._rx_queue.append(line.rstrip(b"\r").decode("utf-8", "replace"))

    def get_lines(self) -> list[str]:
        lines = self._rx_queue
        self._rx_queue = []
        return lines


uart = Uart()
