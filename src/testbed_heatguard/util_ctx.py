from __future__ import annotations

import logging
import pathlib
import typing

from octoprobe.usb_tentacle.usb_tentacle import UsbTentacles
from octoprobe.util_baseclasses import OctoprobeAppExitException
from octoprobe.util_pytest.util_func_logger import func_logger
from octoprobe.util_pyudev import UdevPoller

from testbed_heatguard.tentacle_spec import TentacleHeatguard

logger = logging.getLogger(__file__)


class CtxTestrunHeatguard:
    """
    The context of a test run
    """

    def __init__(self, connected_tentacles: typing.Sequence[TentacleHeatguard]) -> None:
        assert isinstance(connected_tentacles, list)

        self.first_time_in_session = True
        self.udev_poller = UdevPoller()

        assert len(connected_tentacles) >= 1
        self.tentacle: TentacleHeatguard = connected_tentacles[0]

        self.connected_tentacles = connected_tentacles

    @staticmethod
    def session_powercycle_tentacles(poweron: bool) -> UsbTentacles:
        """
        Powers all Pico infra.
        Finds all tentacle by finding pico_unique_id of the Pico infra.
        """
        # We have to reset the power for all pico-infra to become visible
        return UsbTentacles.query(poweron=poweron)

    def session_teardown(self) -> None:
        self.udev_poller.close()

    def function_setup_infra(
        self,
        udev_poller: UdevPoller,
        tentacle: TentacleHeatguard,
    ) -> None:
        """
        Power off all other known usb power switchs.

        For each active tentacle:

        * Power on infa
        * Flash firmware
        * Get serial numbers and assert if it does not match the config
        * Return tty
        """

        # Instantiate poller BEFORE switching on power to avoid a race condition
        tentacle.infra.setup_infra(udev_poller)
        # tentacle.infra.mcu_infra.active_led(on=False)
        tentacle.infra.switches.dut = False
        tentacle.verify_hw_version()

    def session_debugprobe_power_on(
        self,
        udev_poller: UdevPoller,
        tentacle: TentacleHeatguard,
        directory_logs: pathlib.Path,
    ) -> None:
        tentacle.debugprobe.power_on(udev=udev_poller, directory_logs=directory_logs)

    def session_setup_dut_flash(
        self,
        udev_poller: UdevPoller,
        tentacle: TentacleHeatguard,
        directory_logs: pathlib.Path,
    ) -> None:
        if not tentacle.is_mcu:
            return

        # Flash the MCU
        tentacle.flash_dut(
            udev_poller=udev_poller,
            directory_logs=directory_logs,
            firmware_spec=tentacle.tentacle_state.firmware_spec,
        )

    def function_teardown(
        self,
        active_tentacles: typing.Sequence[TentacleHeatguard],
    ) -> None:
        for tentacle in active_tentacles:
            try:
                tentacle.dut.mp_remote_close()
                tentacle.switches.led_error = False

                # Free mp_remote
                if not tentacle.is_mcu:
                    continue

                # Before we can switch the relays: Connect to infra, power off and free mp_remote
                tentacle.infra.load_base_code_if_needed()
                try:
                    tentacle.infra.switches.relays(
                        relays_open=tentacle.infra.list_all_relays
                    )
                except Exception as e:
                    raise OctoprobeAppExitException(
                        f"{tentacle.infra.label}: Failed to control relays: {e!r}"
                    ) from e
                tentacle.infra.mp_remote_close()
            except Exception as e:
                logger.error(e)

    @func_logger
    def set_power_dut(self, on: bool, start_dut_main: bool = True) -> None:
        logger.info(f"[COLOR_INFO]set_power_dut({on=} {start_dut_main=})")

        if on:
            # Power on DUT
            self.tentacle.dut_boot_and_init_mp_remote(udev=self.udev_poller)
            # Drain the diag buffer in the PICO_INFRA as the following line will reboot the DUT!
            self.tentacle.diag_infra_drain_obsolete()
            # Load main.py into DUT
            self.tentacle.load_dut_main_and_start_obsolete(
                start_dut_main=start_dut_main
            )
        else:
            self.tentacle.infra.power_dut_off_and_wait()
