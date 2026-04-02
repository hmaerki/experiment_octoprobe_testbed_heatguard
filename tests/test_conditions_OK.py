import logging

from testbed_heatguard.tentacle_spec import TentacleHeatguard

logger = logging.getLogger(__file__)


def test_ok(dut_power_up: TentacleHeatguard) -> None:
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected transitons: INIT -> OK
    """
    # The fixture 'dut_power_up' already tests this...
