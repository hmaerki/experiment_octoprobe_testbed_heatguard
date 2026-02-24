from __future__ import annotations

import copy
import logging
import pathlib
import time
import typing
from collections.abc import Iterator

import pytest
from octoprobe import lib_tentacle_infra
from octoprobe.octoprobe import CtxTestRun
from octoprobe.util_firmware_spec import FirmwareNoFlashingSpec, FirmwareSpecBase
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pytest.util_vscode import break_into_debugger_on_exception
from octoprobe.util_pyudev import UdevPoller
from octoprobe.util_testbed_lock import TestbedLock
from pytest import fixture
from testbed_micropython.constants import SUBDIR_MPBUILD
from testbed_micropython.util_firmware_mpbuild_interface import ArgsFirmware

import testbed_heatguard.util_testbed
from testbed_heatguard import util_ctx
from testbed_heatguard.constants import (
    DIRECTORY_GIT_CACHE,
    DIRECTORY_TESTRESULTS_DEFAULT,
    EnumFut,
    EnumTentacleType,
    FILENAME_TESTBED_LOCK,
)
from testbed_heatguard.tentacle_spec import TentacleHeatguard
from testbed_heatguard.util_ctx import CtxTestrunHeatguard
from testbed_heatguard.util_firmware_specs import (
    DEFAULT_PYTEST_OPT_FIRMWARE,
    PYTEST_OPT_FIRMWARE,
    get_firmware_specs,
)
from testbed_heatguard.util_testbed import Testbed, get_testbed

logger = logging.getLogger(__file__)

TESTBED: Testbed | None = None
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

DEFAULT_FIRMWARE_SPEC = (
    testbed_heatguard.constants.DIRECTORY_REPO
    / "pytest_args_firmware_RPI_PICO2_v1.24.0.json"
)


_TESTBED_LOCK = TestbedLock()

# Uncomment to following line
# to stop tests on exceptions
break_into_debugger_on_exception(globals())


@pytest.fixture
def required_futs(request: pytest.FixtureRequest) -> list[EnumFut]:
    """
    Returns all FUTS (Feature Under Test) which are required
    by the test function referencing this fixture.
    """
    for m in request.node.own_markers:
        assert isinstance(m, pytest.Mark)
        if m.name == "required_futs":
            return list(m.args)
    return []


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

    # TODO: See also: get_firmware_specs()
    # Support: Noflash
    # Support: xy.json
    # Support: git://
    # Support: local directory
    firmware_git_url = request.config.getoption(PYTEST_OPT_FIRMWARE)

    args_firmware = ArgsFirmware(
        firmware_build=firmware_git_url,
        flash_skip=False,
        flash_force=False,
        git_clean=False,
        directory_git_cache=DIRECTORY_GIT_CACHE,
    )
    args_firmware.setup()

    _testrun = util_ctx.CtxTestrunHeatguard(
        connected_tentacles=TESTBED.tentacles,
        args_firmware=args_firmware,
    )

    assert _testrun.tentacle.is_mcu

    # _testrun.session_powercycle_tentacles()

    yield _testrun

    _testrun.session_teardown()


@fixture(scope="function", autouse=True)
def setup_tentacles(
    ctx: CtxTestrunHeatguard,  # pylint: disable=W0621:redefined-outer-name
    required_futs: tuple[EnumFut],  # pylint: disable=W0621:redefined-outer-name
    # active_tentacles: list[TentacleHeatguard],  # pylint: disable=W0621:redefined-outer-name
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
            mpbuild_artifacts = testresults_directory.directory_top / SUBDIR_MPBUILD
            mpbuild_artifacts.mkdir(parents=True, exist_ok=True)
            ctx.tentacle.infra.load_base_code_if_needed()
            ctx.args_firmware.build_firmware(
                tentacle=ctx.tentacle,
                mpbuild_artifacts=mpbuild_artifacts,
            )
            ctx.function_prepare_dut(tentacle=ctx.tentacle)
            ctx.function_setup_infra(
                udev_poller=ctx.udev_poller,
                tentacle=ctx.tentacle,
            )
            if False:
                ctx.function_setup_dut_flash(
                    udev_poller=ctx.udev_poller,
                    tentacle=ctx.tentacle,
                    directory_logs=mpbuild_artifacts,
                )

            ctx.tentacle.load_mp_infra()

            ctx.tentacle.set_relays_by_FUT(
                fut=EnumFut.FUT_MCU_ONLY,
                open_others=True,
            )
            logger.info(
                f"TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
            )
            yield

        except Exception as e:
            logger.warning(f"Exception during test: {e!r}")
            logger.exception(e)
            raise
        finally:
            logger.info(
                f"TEST TEARDOWN {duration_text()} {testresults_directory.test_nodeid}"
            )
            try:
                ctx.function_teardown(active_tentacles=[ctx.tentacle])
            except Exception as e:
                logger.exception(e)
            logger.info(
                f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
            )


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


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    This function name is reserved by pytest.
    See https://docs.pytest.org/en/7.1.x/reference/reference.html#initialization-hooks.

    It will be called to determine the program arguments.

    When calling :code:`pytest --help`, below arguments will be listed!
    """
    parser.addoption(
        PYTEST_OPT_FIRMWARE,
        action="store",
        default=None,
        help=f"The url to a git repo to be cloned and compiled, a path to a source directory. Or a json file with a download location. Syntax: {DEFAULT_PYTEST_OPT_FIRMWARE}.",
    )
