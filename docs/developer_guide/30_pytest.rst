Run pytest on heatguard
==============================

Run pytest

.. code-block:: bash

    pytest

    =============================================================================================== test session starts ===============================================================================================
    collected 13 items                                                                                                                                                                                                

    tests/test_conditions_FAILURE.py ......                                                                                                                                                                     [ 46%]
    tests/test_conditions_GUARD.py ..                                                                                                                                                                           [ 61%]
    tests/test_conditions_OK.py .                                                                                                                                                                               [ 69%]
    tests/test_lowlevel.py ....                                                                                                                                                                                 [100%]

Run pytest with text output and verbose on a specific test

.. code-block:: bash

    pytest -s -v tests/test_conditions_FAILURE.py::test_Tdiff_high

    =============================================================================================== test session starts ===============================================================================================

    tests/test_conditions_FAILURE.py::test_Tdiff_high INFO     TEST SETUP  0s tests/test_conditions_FAILURE.py::test_Tdiff_high
    INFO     Tentacle DUT 4b35-MCU_HEADGUARD: Version installed: RPI_PICO;3.4.0; MicroPython v1.27.0 on 2025-12-09;Raspberry Pi Pico with RP2040
    INFO     Tentacle DUT 4b35-MCU_HEADGUARD: Firmware is already installed
    INFO     [COLOR_TEST_STATEMENT]conftest.py:129 load_mp_infra()  
    INFO     [COLOR_INFO]TEST BEGIN  1s tests/test_conditions_FAILURE.py::test_Tdiff_high
    INFO     [COLOR_TEST_STATEMENT]conftest.py:46 set_power_dut(on=True, start_dut_main=True)  
    ...
    INFO     [COLOR_TEST_STATEMENT]test_conditions_FAILURE.py:23 diag_waitfor(expected_line='probe state OK True', timeout_s=2.0, drain=True)  
    INFO     [COLOR_INFO]diag_waitfor(expected_line='probe state OK True')
    INFO     [COLOR_TEST_STATEMENT]tentacle_spec.py:289 diag_infra_get_lines(drain=True)  
    PASSEDINFO     [COLOR_SUCCESS]TEST TEARDOWN  5s tests/test_conditions_FAILURE.py::test_Tdiff_high
    INFO     TEST END  5s tests/test_conditions_FAILURE.py::test_Tdiff_high


    ================================================================================================ 1 passed in 4.70s ================================================================================================

Run pytest and observer the DUT output of main.py
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set breakpoint in conftest.py just after line `logger.info(f"DUT may be connected: mpremote connect {tty}")`.

Let pytest run into the breakpoint.

.. code-block:: bash

    mpremote a1

