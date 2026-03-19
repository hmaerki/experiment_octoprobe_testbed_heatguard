import logging
from collections.abc import Iterator

import pytest

from testbed_heatguard.tentacle_spec import Inject
from testbed_heatguard.util_ctx import CtxTestrunHeatguard

logger = logging.getLogger(__file__)


@pytest.fixture
def dut_power_up(ctx: CtxTestrunHeatguard) -> Iterator[CtxTestrunHeatguard]:
    """
    Powers the dut.
    Waits till the dut is ready, eg 'state OK'.
    """
    ctx.set_power_dut(on=True)

    ctx.tentacle.diag_infra_waitfor(
        "probe state OK True 'Initial state after power up'"
    )

    yield ctx


def test_Tref_error(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when a temperature sensor fails
    Expected behaviour: Error state
    """
    tentacle = dut_power_up.tentacle

    # disconnect Tguard
    with tentacle.inject(Inject(inject_Tguard_disconnect=True)):
        tentacle.diag_infra_waitfor(
            "probe state FAILURE False 'I2C failed for sensor Tguard!"
        )

    tentacle.diag_infra_waitfor("probe state OK True")


def test_Tdiff_high(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected behaviour: Error state
    """
    tentacle = dut_power_up.tentacle

    # disconnect Tguard and simulate 50C
    with tentacle.inject(Inject(inject_Tguard_disconnect=True, sim_temperature_C=50.0)):
        tentacle.diag_infra_waitfor(
            "probe state FAILURE False 'Temperature difference too high: diff_C="
        )

    tentacle.diag_infra_waitfor("probe state OK True")


def test_Tguard_high(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when the guard sensor measures a high temperature
    Expected behaviour: Alarm state
    """
    tentacle = dut_power_up.tentacle

    # disconnect Tguard and simulate 85C
    with tentacle.inject(Inject(inject_Tguard_disconnect=True, sim_temperature_C=85.0)):
        tentacle.diag_infra_waitfor(
            "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'"
        )

    tentacle.diag_infra_write("stimuly state write")
    tentacle.diag_infra_waitfor("probe state GUARD False 'response to stimuly'")


def test_Tguard_high_eeprom_error_write():
    """
    Rationale: As test_Tguard_high() but writing EEPROM fails
    Expected result: error state
    """


def test_sw_locked_up_watchdog(dut_power_up: CtxTestrunHeatguard):
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
