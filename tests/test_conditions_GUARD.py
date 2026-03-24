import logging

import pytest

from testbed_heatguard.tentacle_spec import Inject
from testbed_heatguard.util_ctx import CtxTestrunHeatguard

logger = logging.getLogger(__file__)


def test_Tguard_high(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when the guard sensor measures a high temperature
    Simulation: i2c Tguard 85C
    Expected transitons: INIT -> OK -> GUARD -> OK
    """
    tentacle = dut_power_up.tentacle

    # disconnect Tguard and simulate 85C
    with tentacle.inject(Inject(inject_Tguard_disconnect=True, sim_temperature_C=85.0)):
        tentacle.diag_infra_waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'"
        )

    # The guard condition has gone, bug the guard state must remain
    with pytest.raises(TimeoutError):
        tentacle.diag_infra_waitfor("probe state OK", timeout_s=2.0)

    tentacle.diag_infra_write("inject timeover")

    tentacle.diag_infra_waitfor("probe state OK", timeout_s=22.0)


def test_Tguard_high_EEPROM(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: GUARD state must be written into the EEPROM
    Simulation: i2c EEPROM
    Expected transitons: INIT -> OK -> GUARD
    Expected behaviour: EEPROM written
    """
    tentacle = dut_power_up.tentacle

    with tentacle.inject(
        Inject(inject_EEPROM_disconnect=True, sim_EEPROM_data=repr({"state": "OK"}))
    ):
        tentacle.diag_infra_write(
            "stimulus heatguard.update_temperatures(temperature_Tguard_C=90.0, diff_C=0.0)"
        )
        tentacle.diag_infra_waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=90.000C'"
        )
        data_EEPROM = tentacle.get_EEPROM_infra_sim()
        assert data_EEPROM == repr({"state": "GUARD"})
