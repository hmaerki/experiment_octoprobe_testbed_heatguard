Run heatguard without pytest
==============================

The commands require only `octoprobe` - `testbed_heatguard` is not used.

Show connected tentacles

.. code-block:: bash

    op query

Power on DUT, copy main.py and show output

.. code-block:: bash

    op power --on dut

    # Copy main.py and restart main.py: Blue led starts blinking
    mpremote a1 cp src/testbed_heatguard/mp_dut_main.py :main.py

    # Observe output
    mpremote a1

Run main.py directly from mpremote

.. code-block:: bash

    op power --on dut

    # Remove main.py and restart: blue led is off!
    mpremote a1 rm :main.py
    mpremote a1 reset

    # Run main from memory and observe output
    mpremote a1 run src/testbed_heatguard/mp_dut_main.py

Power on DUT but in programming mode and flash micropython

.. code-block:: bash

    op power --off dut; op power --on relay1; sleep 1;op power --on dut; sleep 1; op power --off relay1

    cd /media/$USER/RPI-RP2
    wget https://micropython.org/resources/firmware/RPI_PICO-20251209-v1.27.0.uf2

This corresponds to src/testbed_heatguard/util_ctx.py: `tentacle.flash_dut()`.
