from __future__ import annotations

import enum
import logging
import pathlib
import time
import typing

from octoprobe.usb_tentacle.usb_constants import Switch
from octoprobe.usb_tentacle.usb_tentacle import UsbTentacles
from octoprobe.util_baseclasses import OctoprobeAppExitException
from octoprobe.util_pyudev import UdevPoller
from testbed_micropython.util_firmware_mpbuild_interface import ArgsFirmware

from testbed_heatguard.tentacle_spec import TentacleHeatguard

logger = logging.getLogger(__file__)

FULL_POWERCYCLE_ALL_TENTACLES = False


class CtxTestrunHeatguard:
    """
    The context of a test run
    """

    def __init__(
        self,
        connected_tentacles: typing.Sequence[TentacleHeatguard],
        args_firmware: ArgsFirmware,
    ) -> None:
        assert isinstance(connected_tentacles, list)
        assert isinstance(args_firmware, ArgsFirmware)

        self.args_firmware = args_firmware
        self.udev_poller = UdevPoller()

        assert len(connected_tentacles) >= 1
        self.tentacle: TentacleHeatguard = connected_tentacles[0]

        self.connected_tentacles = connected_tentacles

        self.load_dut_main = self.tentacle.load_dut_main

    # def load_dut_main(self)->None:
    #     """
    #     Loads main.py but does NOT call main().
    #     This method assumes that main.py is present on the device.
    #     """
    #     self.tentacle.load_dut_main()

    @staticmethod
    def session_powercycle_tentacles() -> UsbTentacles:
        """
        Powers all Pico infra.
        Finds all tentacle by finding pico_unique_id of the Pico infra.
        """
        # We have to reset the power for all pico-infra to become visible
        return UsbTentacles.query(poweron=FULL_POWERCYCLE_ALL_TENTACLES)

    def session_teardown(self) -> None:
        self.udev_poller.close()

    def function_setup_infa_and_dut(
        self,
        udev_poller: UdevPoller,
        tentacle: TentacleHeatguard,
        directory_logs: pathlib.Path,
    ) -> None:
        self.function_setup_infra(udev_poller=udev_poller, tentacle=tentacle)
        self.function_prepare_dut(tentacle=tentacle)
        self.function_setup_dut_flash(
            udev_poller=udev_poller,
            tentacle=tentacle,
            directory_logs=directory_logs,
        )

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

        if not FULL_POWERCYCLE_ALL_TENTACLES:
            # As the tentacle infra has NOT been powercycled, we
            # have to reset the relays
            tentacle.infra.switches.relays(
                relays_close=[],
                relays_open=tentacle.infra.list_all_relays,
            )

    def function_prepare_dut(self, tentacle: TentacleHeatguard) -> None:
        # Why close the infra mp_remote?
        if tentacle.is_mcu:
            tentacle.dut.mp_remote_close()

        changed = tentacle.switches[Switch.DUT].set(on=False)
        if changed:
            # Give the DUT some time to power off
            time.sleep(0.5)

    def function_setup_dut_flash(
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
        self, active_tentacles: typing.Sequence[TentacleHeatguard]
    ) -> None:
        if False:
            for tentacle in active_tentacles:
                tentacle.power_dut_off_and_wait()

        def ping_tentacle_infra(tentacle: TentacleHeatguard, tag: str) -> None:
            try:
                tentacle.infra.mp_remote.read_bool("True")
                logger.debug(f"{tentacle.label_short}: {tag}: Ping succeeded")
            except Exception as e:
                logger.warning(
                    f"{tentacle.label_short}: {tag}: Ping failed!", exc_info=e
                )

        do_ping = False
        for tentacle in active_tentacles:
            try:
                tentacle.dut.mp_remote_close()
                if do_ping:
                    ping_tentacle_infra(tentacle=tentacle, tag="a")
                if False:
                    # It may be conventient if the DUT will remain powered
                    tentacle.switches.dut = False
                if do_ping:
                    ping_tentacle_infra(tentacle=tentacle, tag="b")
                tentacle.switches.led_error = False
                if do_ping:
                    ping_tentacle_infra(tentacle=tentacle, tag="c")

                # Free mp_remote
                if not tentacle.is_mcu:
                    continue
                if do_ping:
                    ping_tentacle_infra(tentacle=tentacle, tag="d")

                # Before we can switch the relays: Connect to infra, power off and free mp_remote
                tentacle.infra.load_base_code_if_needed()
                ping_tentacle_infra(tentacle=tentacle, tag="e")
                try:
                    tentacle.infra.switches.relays(
                        relays_open=tentacle.infra.list_all_relays
                    )
                except Exception as e:
                    raise OctoprobeAppExitException(
                        f"{tentacle.infra.label}: Failed to control relays: {e!r}"
                    ) from e
                ping_tentacle_infra(tentacle=tentacle, tag="f")
                tentacle.infra.mp_remote_close()
            except Exception as e:
                logger.error(e)

    def setup_relays(
        self,
        tentacles: typing.Sequence[TentacleHeatguard],
        futs: tuple[enum.StrEnum],
    ) -> None:
        assert isinstance(tentacles, list | tuple)
        assert isinstance(futs, list | tuple)
        assert len(futs) == 1
        fut = futs[0]
        for tentacle in tentacles:
            tentacle.set_relays_by_FUT(fut=fut)

    def set_power_dut(self, on: bool) -> None:
        if on:
            self.tentacle.dut_boot_and_init_mp_remote(udev=self.udev_poller)
            self.tentacle.load_dut_main_and_start()
        else:
            self.tentacle.infra.power_dut_off_and_wait()
