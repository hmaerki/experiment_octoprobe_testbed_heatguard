from __future__ import annotations

import logging
import threading
import time

import serial
from octoprobe.util_pytest.util_func_logger import func_logger
from octoprobe.util_pytest.util_logging_handler_color import EnumColors

logger = logging.getLogger(__file__)


class Diag:
    def __init__(self, tty: str) -> None:
        assert isinstance(tty, str)
        self.lines: list[str] = []
        self.lines_processed: int = 0
        self._lock = threading.Lock()
        self._reader_stop = threading.Event()
        self._reader_stop.clear()
        self._serial: serial.Serial | None = serial.Serial(
            tty,
            baudrate=115200,
            exclusive=True,
        )

        self._reader_thread: threading.Thread | None = threading.Thread(
            target=self._reader_loop,
            name="diag",
            daemon=False,
        )
        self._reader_thread.start()

    def stop_reader_thread(self) -> None:
        self._reader_stop.set()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=2.0)
            self._reader_thread = None
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def _reader_loop(self) -> None:
        try:
            while not self._reader_stop.is_set():
                if self._serial is None:
                    logger.error("self._serial is None")
                    return
                try:
                    line_bytes = self._serial.readline()
                except TypeError as e:
                    logger.debug(f"self._serial: {e!r}")
                    assert self._serial is None
                    return
                if not line_bytes:
                    continue
                line = line_bytes.strip(b"\x00").decode("utf-8", "ignore").strip()
                logger.debug(f"diag rx: >{line}<")
                if line:
                    with self._lock:
                        self.lines.append(line)
        except serial.SerialException as e:
            logger.error(f"self._serial: {e!r}")
            return
        except Exception as e:
            logger.error(f"self._serial: {e!r}")
            raise
        finally:
            self._reader_thread = None

    @func_logger
    def write(self, line: str) -> None:
        assert self._serial is not None
        self._serial.write(f"{line}\r".encode())

    @func_logger
    def drain(self) -> None:
        with self._lock:
            self.lines = []
            self.lines_processed = 0

    @func_logger
    def waitfor(self, expected_line: str, timeout_s: float = 2.0) -> None:
        """
        Wait for expected line.
        """
        begin_s = time.monotonic()
        while True:
            time.sleep(0.1)
            with self._lock:
                duration_s = time.monotonic() - begin_s

                # Consume lines which have not been processed yet
                while self.lines_processed < len(self.lines):
                    actual_line = self.lines[self.lines_processed]
                    self.lines_processed += 1
                    if actual_line.startswith(expected_line):
                        logger.debug(
                            f"{EnumColors.COLOR_TEST_STATEMENT.with_brackets}diag_waitfor: after {duration_s:0.1f}s of {timeout_s:0.1f}s received: {actual_line}"
                        )
                        return

                # Handle timeout
                if duration_s > timeout_s:
                    elems = [
                        f"Timeout of {timeout_s:0.1f}s while waiting for: {expected_line}",
                        f"    lines ({self.lines_processed=}):",
                        *["    " + line for line in self.lines],
                    ]
                    raise TimeoutError("\n".join(elems))
