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

