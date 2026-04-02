Commissioning
==============================

Flash PICO_INFRA and selftest
-------------------------------

.. code-block:: bash

    op commissioning

Check if all LEDs toggle.


Flash PICO_PROBE with firmware `debugprobe`
---------------------------------------------

.. code-block:: bash

    op flash-probe --firmware-url=https://github.com/raspberrypi/debugprobe/releases/download/debugprobe-v2.3.0/debugprobe_on_pico.uf2

Flash DUT with firmware `micropython` or `zephyr`
--------------------------------------------------

.. code-block:: bash

    # Flash micropython / zephyr
    heatguard dut-flash
    # Copy main.py
    heatguard dut-copy-main
    # Verify if tests run successfully
    pytest


Note: `heatgurad dut-flash` corresponds to these commands:

.. code-block:: bash

    op power --off dut; op power --on relay1; sleep 1; op power --on dut; sleep 1; op power --off relay1

    # For microptyhon
    wget https://micropython.org/resources/firmware/RPI_PICO-20251209-v1.27.0.uf2 --output-file=/media/$USER/RPI-RP2/fw.uf2

    # For zephyr
    picotool load ... --update --execute ../zephyr.uf2