import logging

from testbed_heatguard.util_ctx import CtxTestrunHeatguard

logger = logging.getLogger(__file__)


def test_ok(dut_power_up: CtxTestrunHeatguard) -> None:
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected transitons: INIT -> OK
    """
    pass
