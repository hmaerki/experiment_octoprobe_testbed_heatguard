
Testresults
==================

.. note:: 

  This page is about the python logging framework. It is not imporant in any means to `testbed_heatguard`. You may skip this page.


Using the python logging framework, the logs are written to the filesystem too:


.. code-block:: shell
      
   $ tree testresults/
   testresults/
   ├── logger_10_debug.color
   ├── logger_10_debug.log
   ├── logger_20_info.color
   ├── logger_20_info.log
   ├── logger_40_error.color
   ├── logger_40_error.log
   └── tests
      ├── test_conditions_FAILURE
      │   ├── test_reboot_eeprom_guard_state
      │   │   ├── logger_10_debug.color
      │   │   ├── logger_10_debug.log
      │   │   ├── logger_20_info.color
      │   │   ├── logger_20_info.log
      │   │   ├── logger_40_error.color
      │   │   └── logger_40_error.log
      │   ├── test_reboot_eerom_scrambled
      │   │   ├── logger_10_debug.color
      │   │   ├── logger_10_debug.log
      │   │   ├── logger_20_info.color
      │   │   ├── logger_20_info.log
      │   │   ├── logger_40_error.color
      │   │   └── logger_40_error.log


The directorystructure corresponds to the structure of the tests.

The logs in the top folder are all logs of the subfolders together.

**Log levels**

* logger_40_error.log Just contains the errors
* logger_20_info.log contains ERRORS and INFO
* logger_10_debug.log contains ERRORS, INFO and logger_10_debug

**Colors**

* Extension '.log': Normal testfiles
* Extension '.color': Using `ANSI/VT100 color codes <https://rich.readthedocs.io/en/latest/appendix/colors.html#standard-colors>`_.  Colors are visible on the console or with this `vscode extension <https://marketplace.visualstudio.com/items?itemName=iliazeus.vscode-ansi>`_.

**Color scheme**

* Brightness (dimmed, normal, bright) corresponds to the severity DEBUG, INFO, ERROR.
* Color corresponds to the component. For example testcode is yello. pytest outcomes are green or red. All other are white.
