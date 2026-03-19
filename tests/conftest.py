from __future__ import annotations

import logging
import pathlib
import time
from collections.abc import Iterator

import pytest
from octoprobe import lib_tentacle_infra
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_logging_handler_color import EnumColors
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pytest.util_vscode import break_into_debugger_on_exception
from octoprobe.util_testbed_lock import TestbedLock
from pytest import fixture

from testbed_heatguard import util_ctx
from testbed_heatguard.constants import (
    DIRECTORY_TESTRESULTS_DEFAULT,
    EnumFut,
    FILENAME_TESTBED_LOCK,
)
from testbed_heatguard.util_ctx import CtxTestrunHeatguard
from testbed_heatguard.util_testbed import Testbed, get_testbed

logger = logging.getLogger(__file__)

TESTBED: Testbed | None = None
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
ATTRIBUTES_COLOR_OUTCOME = "color_outcome"


_TESTBED_LOCK = TestbedLock()

# Uncomment to following line
# to stop tests on exceptions
break_into_debugger_on_exception(globals())


@fixture(scope="session", autouse=True)
def ctx(request: pytest.FixtureRequest) -> Iterator[CtxTestrunHeatguard]:
    """
    Setup and teardown octoprobe and all connected tentacles.

    Now we loop over all tests an return for every test a `CtxTestrunHeatguard` structure.
    Using this structure, the test find there tentacles, git-repos etc.
    """
    assert TESTBED is not None

    # To be removed when flakyness testing is resolved
    lib_tentacle_infra.ENABLE_DUT_POWER_OFF_TIME_MIN = False  # type: ignore

    _ctx = util_ctx.CtxTestrunHeatguard(connected_tentacles=TESTBED.tentacles)

    assert _ctx.tentacle.is_mcu

    # _testrun.session_powercycle_tentacles()

    yield _ctx

    _ctx.session_teardown()


@fixture(scope="function", autouse=True)
def setup_tentacles(
    request: pytest.FixtureRequest,
    ctx: CtxTestrunHeatguard,  # pylint: disable=W0621:redefined-outer-name
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
            ctx.tentacle.infra.load_base_code_if_needed()
            ctx.function_setup_infra(
                udev_poller=ctx.udev_poller,
                tentacle=ctx.tentacle,
            )
            if ctx.first_time_in_session:
                ctx.session_setup_dut_flash(
                    udev_poller=ctx.udev_poller,
                    tentacle=ctx.tentacle,
                    directory_logs=testresults_directory.directory_top,
                )
            ctx.tentacle.load_mp_infra()
            ctx.tentacle.set_relays_by_FUT(
                fut=EnumFut.FUT_MCU_ONLY,
                open_others=True,
            )
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
                ctx.function_teardown(active_tentacles=[ctx.tentacle])
            except Exception as e:
                logger.exception(e)
            logger.info(
                f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
            )
            ctx.first_time_in_session = False


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    This hook is just required for the coloring out the debug log.
    """
    outcome = yield
    report = outcome.get_result()
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
    TESTBED = get_testbed()


def pytest_sessionfinish(session: pytest.Session) -> None:
    assert TESTBED is not None
    TESTBED.close()

    _TESTBED_LOCK.unlink()
