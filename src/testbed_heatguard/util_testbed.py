from __future__ import annotations

import logging
import pathlib
import shutil

from octoprobe.usb_tentacle.usb_tentacle import UsbTentacles
from octoprobe.util_baseclasses import (
    TentacleNotFoundInInventory,
)
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_logging import Logs
from octoprobe.util_pyudev import UdevPoller

from .constants import DIRECTORY_TESTRESULTS_DEFAULT, EnumFut
from .tentacle_spec import TentacleHeatguard
from .util_diag import Diag

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


class Testbed:
    """
    A minimal testbed just contains tentacles.
    However, it might also include usb-hubs, wlan-accesspoints, etc.
    """

    def __init__(
        self,
        tentacles: list[TentacleHeatguard],
        logs: Logs,
    ) -> None:
        assert isinstance(tentacles, list)
        assert isinstance(logs, Logs)
        for tentacle in tentacles:
            assert isinstance(tentacle, TentacleHeatguard)

        self.tentacles = tentacles
        self.logs = logs
        self.udev = UdevPoller()

    @property
    def description_short(self) -> str:
        return TentacleHeatguard.tentacles_description_short(tentacles=self.tentacles)

    def session_setup(self) -> None:
        for tentacle in self.tentacles:
            tentacle.infra.load_base_code_if_needed()
            tentacle.infra.setup_infra(udev=self.udev)
            tentacle.verify_hw_version()
            tentacle.switches.dut = False
            tentacle.switches.proberun = False
            tentacle.switches.probeboot = True
            tentacle.switches.led_error = False

            tentacle.debugprobe.power_on(udev=self.udev)
            tentacle.init_diag(Diag(tentacle.debugprobe.tty))

            tentacle.load_mp_infra()

    def session_teardown(self) -> None:
        for tentacle in self.tentacles:
            tentacle.stop_diag()
            tentacle.infra.mp_remote_close()

        self.udev.close()
        self.logs.close()

    def function_setup(self, tentacle: TentacleHeatguard) -> None:
        tentacle.switches.led_active = True

        tentacle.set_relays_by_FUT(
            fut=EnumFut.FUT_MCU_ONLY,
            open_others=True,
        )

    def function_teardown(self, tentacle: TentacleHeatguard) -> None:
        try:
            tentacle.dut.mp_remote_close()
            tentacle.switches.led_active = False
            tentacle.switches.led_error = False

        except Exception as e:
            logger.error(e)

    @staticmethod
    def factory(powercycle_tentacles: bool) -> Testbed:
        # pylint: disable=import-outside-toplevel
        from octoprobe import lib_tentacle_infra

        lib_tentacle_infra.DUT_POWER_OFF_TIME_MIN_S = 0.0  # type: ignore

        if DIRECTORY_TESTRESULTS_DEFAULT.exists():
            shutil.rmtree(DIRECTORY_TESTRESULTS_DEFAULT, ignore_errors=False)
        DIRECTORY_TESTRESULTS_DEFAULT.mkdir(parents=True, exist_ok=True)

        util_logging.init_logging()
        logs = util_logging.Logs(DIRECTORY_TESTRESULTS_DEFAULT)

        # We have to reset the power for all pico-infra to become visible
        usb_tentacles = UsbTentacles.query(poweron=powercycle_tentacles)
        tentacles: list[TentacleHeatguard] = []
        for usb_tentacle in usb_tentacles:
            try:
                tentacle = TentacleHeatguard.factory_usb_tentacle(
                    usb_tentacle=usb_tentacle
                )
            except TentacleNotFoundInInventory as e:
                logger.warning(e)
                continue

            tentacles.append(tentacle)

        if len(tentacles) == 0:
            raise ValueError("No tentacles are connected!")

        return Testbed(tentacles=tentacles, logs=logs)
