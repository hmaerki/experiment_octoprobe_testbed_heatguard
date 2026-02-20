def test_Tref_error():
    """
    Rationale: Behaviour when a temperature sensor fails
    Expected behaviour: Error state
    """


def test_Tdiff_high():
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected behaviour: Error state
    """


def test_Tguard_high():
    """
    Rationale: Behaviour when the guard sensor measures a high temperature
    Expected behaviour: Alarm state
    """


def test_Tguard_high_eeprom_error_write():
    """
    Rationale: As test_Tguard_high() but writing EEPROM fails
    Expected result: error state
    """


def test_sw_locked_up_watchdog():
    """
    Rationale: Behaviour when the software fires
    Expected result: Watchdog fires
    """


def test_reboot_after_watchdog():
    """
    Rationale: Power on after watchdog
    Expected result: error state
    """


def test_reboot_eeprom_error_state():
    """
    Rationale: Power on with EEPROM containing error state
    Expected result: error state
    """


def test_reboot_eerom_scrambled():
    """
    Rationale: Power on with EEPROM with scrambled data
    Expected result: error state
    """
