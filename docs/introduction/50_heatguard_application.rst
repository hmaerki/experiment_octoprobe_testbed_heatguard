Heatguard Application
===========================

.. note:: 

    The headguard application is implemented in micropython.

    All concepts demonstrated in `testbed_headguard` would be the same if the application would be written in C++.

.. mermaid::

   stateDiagram-v2
       [*] --> INIT

       INIT --> OK : init ok
       INIT --> FAILURE : i2c read error
       INIT --> GUARD : eeprom (GUARD)

       OK --> FAILURE : diff_C > 3C, i2c read error
       OK --> GUARD : Tguard_C > 80C

       FAILURE --> OK : *
       FAILURE --> GUARD : Tguard_C > 80C

       GUARD --> OK : timeout(60s)

This state diagram describes the application. The states are visible on the LED's.

The application itself is written in micropython:
`mp_dut_main.py <https://github.com/octoprobe/testbed_heatguard/blob/main/src/testbed_heatguard/mp_dut_main.py>`_
All concepts described here would be the same if the application would be written in C++!

Summary of the functionality
------------------------------

State `OK`
^^^^^^^^^^^^

If everything is working fine. `LED_OK` is on. `LED_ENABLE` will be on the the heater is powered and controlled by the Controller.

State `FAILURE`
^^^^^^^^^^^^^^^^^^

Minor errors like i2c errors, temperature difference too high. `LED_FAILURE` is on. `LED_ENABLE` is off and the heater is off.

State `GUARD`
^^^^^^^^^^^^^^^^^^

We have overtemperature. This is an emergency! `LED_GUARD` is on. `LED_ENABLE` is off and the heater is off.

Even if the temperature is low again, we have to wait for a timeout.

EEPROM
^^^^^^^^^^^^^^^^^^

The state is stored in the EEPROM: So we may stay in `GUARD` even after a watchdog reset or a powercycle.


Watchdog
^^^^^^^^^^^^^^^^^^

We ensure a reboot if the application crashes.
