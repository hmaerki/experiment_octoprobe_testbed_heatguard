import logging

import pytest

from testbed_heatguard.tentacle_spec import Inject, TentacleHeatguard

logger = logging.getLogger(__file__)


def test_Tguard_high(dut_power_up: TentacleHeatguard) -> None:
    """
    Rationale: Behaviour when the guard sensor measures a high temperature
    Simulation: i2c Tguard 85C
    Expected transitons: INIT -> OK -> GUARD -> OK
    """
    # disconnect Tguard and simulate 85C
    with dut_power_up.inject(
        Inject(inject_Tguard_disconnect=True, sim_temperature_C=85.0)
    ):
        dut_power_up.diag.waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'"
        )

    # The guard condition has gone, bug the guard state must remain
    with pytest.raises(TimeoutError):
        dut_power_up.diag.waitfor("probe state OK", timeout_s=2.0)

    dut_power_up.diag.write("inject timeover")

    dut_power_up.diag.waitfor("probe state OK", timeout_s=70.0)


def test_Tguard_high_EEPROM(dut_power_up: TentacleHeatguard) -> None:
    """
    Rationale: GUARD state must be written into the EEPROM
    Simulation: i2c EEPROM
    Expected transitons: INIT -> OK -> GUARD
    Expected behaviour: EEPROM written
    """
    with dut_power_up.inject(
        Inject(inject_EEPROM_disconnect=True, sim_EEPROM_data=repr({"state": "OK"}))
    ):
        dut_power_up.diag.write(
            "stimulus heatguard.update_temperatures(temperature_Tguard_C=90.0, diff_C=0.0)"
        )
        dut_power_up.diag.waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=90.000C'"
        )
        data_EEPROM = dut_power_up.get_EEPROM_infra_sim()
        assert data_EEPROM == repr({"state": "GUARD"})
