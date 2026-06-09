Heatguard Hardware
===========================

:download:`Schematics v0.3 (Pdf) <../../kicad/heatguard_v0.3/production_v0.3/schematics_heatguard_v0.3.pdf>`.

.. image:: images/pcb_top_3D.png
   :width: 500px
   :align: center

To understand the hardware, just look at the silkscreen carefully. Note that I used a small fonts to describe what was added for the testinterface.

.. note:: 

  The implementation of the `Stimuly (inject)` and `Probes` only has very minimal impact on the `Final PCB`: We do not want to make the final PCB more expensive or bigger!

  The `Test Connector` would be typically implemented using flying probes or a solder pads as this requires minimal space on the PCB and no additional cost.


Assignements of the 8 pin testconnector and the relays
--------------------------------------------------------

.. list-table::
   :header-rows: 1

   * - Tentacle
     - DUT - heatguard
     - Signal
   * - relay 1
     - Boot button
     - Boot mode
   * - relay 2
     - pin 10, gpio 4
     - watchdog_disable
   * - relay 3
     - \-
     - inject_Tref_disconnect
   * - relay 4
     - \-
     - inject_Tguard_disconnect
   * - relay 5 
     - \-
     - inject_EEPROM_disconnect
   * - relay 6
     - pin 9, gpio 2
     - inject_T_limit (overwrite Tguard over temperature output)
   * - gpio 12
     - pin 5, gpio 6
     - SDA
   * - gpio 13
     - pin 6, gpio 7
     - SCL
   * - GPIO_PROBE_4
     - pin 8, gpio 1
     - DIAG_RX
   * - GPIO_PROBE_5
     - pin 7, gpio 0
     - DIAG_TX
