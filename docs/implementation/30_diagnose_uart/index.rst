Diagnose interface - UART
===========================

.. note:: 

  The implementation of the UART interface is a bit tricky:

  * PICO_INFRA does many different tasks but also handles the UART.
  * PICO_INFRA has to store the received lines.
  * pytest is use in a synchronous way - therefor polling for the UART is required which produces heavy mpremote communication to the PICO_INFRA.


.. mermaid::

   sequenceDiagram
      Pytest->>+PICO_INFRA: mpremote 'inject xx'
      PICO_INFRA->>-DUT: uart 'inject xx'
      DUT-->>+PICO_INFRA: uart 'probe ab'
      DUT-->>+PICO_INFRA: uart 'probe cd'


      Pytest->>+PICO_INFRA: mpremote 'get_lines()'
      PICO_INFRA-->>-Pytest: lines

The DUT may send to the UART any time.

The PICO_INFRA uses a interrupt handler to receive from the UART. This interrupt handler is active even wehn PICO_INFRA is in REPL mode and is waiting for commands from mpremote from pytest. PICO_INFRA stores the lines in a buffer.

pytest uses `mpremote get_lines()` to poll for lines in the buffer.

pytest maintains two lists

   * diag_lines_unprocessed
   * diag_lines_processed

This is how one may wait for a expected line:

.. code-block:: python

        tentacle.diag_infra_waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'",
            timeout_=10.0
        )

