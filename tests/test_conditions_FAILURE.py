import logging
import time

from testbed_heatguard.tentacle_spec import Inject, TentacleHeatguard

logger = logging.getLogger(__file__)


def test_Tdiff_high(dut_power_up: TentacleHeatguard) -> None:
    """
    Rationale: Behaviour when the temperature difference of both sensors get too high
    Simulation: i2c Tguard (diff_C too high)
    Expected transitons: INIT -> OK -> FAILURE -> OK
    """
    # disconnect Tguard and simulate 50C
    with dut_power_up.inject(
        Inject(inject_Tguard_disconnect=True, sim_temperature_C=50.0)
    ):
        dut_power_up.diag.waitfor(
            "probe state FAILURE False 'Temperature difference too high: diff_C="
        )

    dut_power_up.diag.waitfor("probe state OK True")


def test_Tguard_i2c_error(dut_power_up: TentacleHeatguard) -> None:
    """
    Rationale: Behaviour when a temperature sensor fails
    Simulation: i2c-error Tguard
    Expected transitons: INIT -> OK -> FAILURE -> OK
    """
    if dut_power_up.is_zephyr:
        # Bug in zephyr version
        time.sleep(1.0)

    # disconnect Tguard
    with dut_power_up.inject(Inject(inject_Tguard_disconnect=True)):
        dut_power_up.diag.waitfor(
            "probe state FAILURE False 'I2C failed for sensor Tguard!",
            timeout_s=5.0,
        )

    dut_power_up.diag.waitfor("probe state OK True")


def test_Tguard_high_eeprom_error_write() -> None:
    """
    Rationale: As test_Tguard_high() but writing EEPROM fails
    Expected result: error state
    """


def test_sw_locked_up_watchdog(dut_power_up: TentacleHeatguard) -> None:
    """
    Rationale: Behaviour when the software fires
    Stimulus: inject endless loop
    Expected transitons: INIT -> OK --(WDT_RESET)-> OK
    Expected result: Watchdog fires
    """
    dut_power_up.diag.write("inject endless_loop")

    dut_power_up.diag.waitfor(
        "probe boot WDT_RESET",
        timeout_s=5.0,
    )
    dut_power_up.diag.waitfor("probe state OK True 'Initial state after power up'")


def test_reboot_eeprom_guard_state() -> None:
    """
    Rationale: Power on with EEPROM containing guard state
    Expected result: guard state
    """


def test_reboot_eerom_scrambled() -> None:
    """
    Rationale: Power on with EEPROM with scrambled data
    Expected result: guard state
    """
