import logging

from testbed_heatguard.tentacle_spec import Inject
from testbed_heatguard.util_ctx import CtxTestrunHeatguard

logger = logging.getLogger(__file__)


def test_Tdiff_high(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when the temperature difference of both sensors get too high
    Simulation: i2c Tguard (diff_C too high)
    Expected transitons: INIT -> OK -> FAILURE -> OK
    """
    tentacle = dut_power_up.tentacle

    # disconnect Tguard and simulate 50C
    with tentacle.inject(Inject(inject_Tguard_disconnect=True, sim_temperature_C=50.0)):
        tentacle.diag_infra_waitfor(
            "probe state FAILURE False 'Temperature difference too high: diff_C="
        )

    tentacle.diag_infra_waitfor("probe state OK True")


def test_Tguard_i2c_error(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when a temperature sensor fails
    Simulation: i2c-error Tguard
    Expected transitons: INIT -> OK -> FAILURE -> OK
    """
    tentacle = dut_power_up.tentacle

    # disconnect Tguard
    with tentacle.inject(Inject(inject_Tguard_disconnect=True)):
        tentacle.diag_infra_waitfor(
            "probe state FAILURE False 'I2C failed for sensor Tguard!"
        )

    tentacle.diag_infra_waitfor("probe state OK True")


def test_Tguard_high_eeprom_error_write():
    """
    Rationale: As test_Tguard_high() but writing EEPROM fails
    Expected result: error state
    """


def test_sw_locked_up_watchdog(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when the software fires
    Stimulus: inject endless loop
    Expected transitons: INIT -> OK --(WDT_RESET)-> OK
    Expected result: Watchdog fires
    """
    tentacle = dut_power_up.tentacle

    tentacle.diag_infra_write("inject endless_loop")

    tentacle.diag_infra_waitfor(
        "probe boot WDT_RESET",
        timeout_s=5.0,
    )
    tentacle.diag_infra_waitfor("probe state OK True 'Initial state after power up'")


def test_reboot_eeprom_guard_state():
    """
    Rationale: Power on with EEPROM containing guard state
    Expected result: guard state
    """


def test_reboot_eerom_scrambled():
    """
    Rationale: Power on with EEPROM with scrambled data
    Expected result: guard state
    """
