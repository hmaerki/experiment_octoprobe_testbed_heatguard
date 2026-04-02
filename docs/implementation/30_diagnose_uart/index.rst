Diagnose interface - UART
===========================

.. note:: 

  The implementation of the UART interface is a bit tricky:

  * PICO_INFRA does many different tasks but also handles the UART.
  * PICO_INFRA has to store the received lines.
  * pytest is use in a synchronous way - therefor polling for the UART is required which produces heavy mpremote communication to the PICO_INFRA.


.. mermaid::

   sequenceDiagram

      participant Pytest
      participant Diag@{ "type" : "queue" }
      participant PICO_PROBE
      participant DUT

      Pytest->>DUT: usb-uart 'inject xx'

      DUT->>+Diag: uart 'probe ab'

      DUT->>Diag: uart 'probe cd'

      Pytest->>Diag: 'get_lines()'

The mcu PICO_PROBE with the firmware `debugprobe` is used as a USB-CDC and connects to the uart on the DUT.

In `testbed_heatguard` the uart is handled by the class `Diag`. A thread listens from input from the DUT and stores it in a list of lines.

pytest uses `diag.get_lines()` to poll for lines in the buffer.

This is how one may wait for a expected line:

.. code-block:: python

        dut_power_up.diag.waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'",
            timeout_=10.0
        )

