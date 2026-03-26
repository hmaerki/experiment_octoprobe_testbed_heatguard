
Simulate I2C
==================

.. note:: 

  This page explains how simulate a certain temperature or EEPROM content.

Switch I2C address
-----------------------

The test connector gpio `inject_Tref_disconnect`, `inject_Tguard_disconnect`, `inject_eeprom_disconnect` may be used to manipulate the I2C address.

* This makes the sensor disappear which results in a I2C error.
* This allows to place a simulated I2C target on that address allowing to fake real values.

Simulate I2C target
-----------------------

Micropython allows to `write I2C targets <https://docs.micropython.org/en/latest/library/machine.I2CTarget.html>`_. Sadly only one address at the time.

This allows us to write tests simulation high temperatures or specific EEPROM content.
