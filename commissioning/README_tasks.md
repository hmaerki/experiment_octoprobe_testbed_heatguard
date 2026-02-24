
# Task

* pytest

  * write tests

* PICO_INFRA: UART with DUT

* DUT
  * UART with PICO_INFRA
  * Write application

* Define DIAG protocol

* src/fixture

  * flash DUT
  * DONE: copy src to DUT
  * DONE: Emulate eeprom
  * DONE: Emulate Tguard


## Design

main.py

  * Watchdog
  * Controller Logic
  * HeatGuard Logic
  * Protocol

* How to know if main.py has to be loaded?
* Parallelimsm:
  * main.py runs on second thread.
  * main.py runs on idle/interrupts.

* main.py includes mp_dut.py
  * main.py 