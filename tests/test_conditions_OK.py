import logging

import pytest

from testbed_heatguard.tentacle_spec import Inject
from testbed_heatguard.util_ctx import CtxTestrunHeatguard

logger = logging.getLogger(__file__)


def test_ok(dut_power_up: CtxTestrunHeatguard):
    """
    Rationale: Behaviour when the temperature difference of both sensor get too high
    Expected transitons: INIT -> OK
    """
    pass
