from __future__ import annotations

import logging
import pathlib
import time
from collections.abc import Generator, Iterator

import pytest
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_logging_handler_color import EnumColors
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pytest.util_vscode import break_into_debugger_on_exception
from octoprobe.util_testbed_lock import TestbedLock
from pytest import fixture

from testbed_heatguard.constants import (
    DIRECTORY_TESTRESULTS_DEFAULT,
    FILENAME_TESTBED_LOCK,
)
from testbed_heatguard.tentacle_spec import TentacleHeatguard
from testbed_heatguard.util_testbed import Testbed

logger = logging.getLogger(__file__)

TESTBED: Testbed | None = None
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
ATTRIBUTES_COLOR_OUTCOME = "color_outcome"


_TESTBED_LOCK = TestbedLock()

# Uncomment to following line
# to stop tests on exceptions
break_into_debugger_on_exception(globals())


@pytest.fixture
def dut_power_up(tentacle: TentacleHeatguard) -> Iterator[TentacleHeatguard]:  # pylint: disable=redefined-outer-name
    """
    Powers the dut.
    Waits till the dut is ready, eg 'state OK'.
    """
    assert TESTBED is not None

    if tentacle.is_zephyr:
        tentacle.switches.dut = False
        time.sleep(0.5)
        tentacle.diag.drain()
        tentacle.switches.dut = True
    else:
        tentacle.set_power_dut(on=True, udev=TESTBED.udev)

    tentacle.diag.waitfor("probe state OK True 'Initial state after power up'")

    yield tentacle


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    This is a pytest hook https://docs.pytest.org/en/7.1.x/reference/reference.html?highlight=pytest_generate_tests#std-hook-pytest_generate_tests

    Give a test function like 'test_i2c()' in 'metafunc', this function will create test calls for possible combinations of tentacles and firmware versions.

    Calls `metafunc.parametrize` which defines the tests that have been be collected.

    :param metafunc: See https://docs.pytest.org/en/7.1.x/reference/reference.html#metafunc
    :type metafunc: pytest.Metafunc
    """
    assert TESTBED is not None

    if "tentacle" in metafunc.fixturenames:
        if len(TESTBED.tentacles) == 0:
            msg = "Not tentacles connected"
            logger.error(msg)
            raise ValueError(msg)

        metafunc.parametrize("tentacle", TESTBED.tentacles, ids=lambda t: t.pytest_id)


@fixture(scope="function", autouse=True)
def setup_tentacles(
    request: pytest.FixtureRequest,
    tentacle: TentacleHeatguard,  # pylint: disable=W0621:redefined-outer-name
    testresults_directory: ResultsDir,  # pylint: disable=W0621:redefined-outer-name
) -> Iterator[None]:
    """
    Runs setup and teardown for every single test:

    * Setup

      * powercycle the tentacles
      * Turns on the 'active' LED on the tentacles involved
      * Flash firmware
      * Set the relays according to `@pytest.mark.required_futs(EnumFut.FUT_I2C)`.

    * yields to the test function
    * Teardown

      * Resets the relays.

    :param testrun: The structure created by `testrun()`
    :type testrun: CtxTestrunHeatguard
    """
    assert TESTBED is not None

    with util_logging.Logs(testresults_directory.directory_test):
        begin_s = time.monotonic()

        def duration_text(duration_s: float | None = None) -> str:
            if duration_s is None:
                duration_s = time.monotonic() - begin_s
            return f"{duration_s:2.0f}s"

        try:
            logger.info(
                f"TEST SETUP {duration_text(0.0)} {testresults_directory.test_nodeid}"
            )
            TESTBED.function_setup(tentacle=tentacle)
            logger.info(
                f"[COLOR_INFO]TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
            )
            yield

        except Exception as e:
            logger.warning(
                f"{EnumColors.COLOR_ERROR.with_brackets}Exception during test: {e!r}"
            )
            logger.exception(e)
            raise

        finally:
            color_outcome = getattr(
                request.node,
                ATTRIBUTES_COLOR_OUTCOME,
                EnumColors.COLOR_ERROR.with_brackets,
            )
            logger.info(
                f"{color_outcome}TEST TEARDOWN {duration_text()} {testresults_directory.test_nodeid}"
            )
            try:
                TESTBED.function_teardown(tentacle=tentacle)
            except Exception as e:
                logger.exception(e)
            logger.info(
                f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
            )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Function,
    call: pytest.CallInfo[None],
) -> Generator[None, pytest.TestReport, None]:
    """
    This hook is just required for the coloring out the debug log.
    """
    outcome = yield
    report = outcome.get_result()
    assert isinstance(report, pytest.TestReport)
    if report.when != "call":
        return

    def get_color_outcome() -> str:
        if report.passed:
            return EnumColors.COLOR_SUCCESS.with_brackets
        if report.failed:
            return EnumColors.COLOR_FAILED.with_brackets
        if report.skipped:
            return EnumColors.COLOR_SKIPPED.with_brackets
        return EnumColors.COLOR_ERROR.with_brackets

    setattr(item, ATTRIBUTES_COLOR_OUTCOME, get_color_outcome())


@pytest.fixture(scope="function")
def testresults_directory(request: pytest.FixtureRequest) -> ResultsDir:
    """
    Returns the log directory for the test function referencing this fixture.
    """
    return ResultsDir(
        directory_top=DIRECTORY_TESTRESULTS_DEFAULT,
        test_name=request.node.name,
        test_nodeid=request.node.nodeid,
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    _TESTBED_LOCK.acquire(FILENAME_TESTBED_LOCK)

    global TESTBED  # pylint: disable=W0603:global-statement
    assert TESTBED is None
    TESTBED = Testbed.factory(powercycle_tentacles=False)
    TESTBED.session_setup()


def pytest_sessionfinish(session: pytest.Session) -> None:
    assert TESTBED is not None
    TESTBED.session_teardown()
    _TESTBED_LOCK.unlink()
