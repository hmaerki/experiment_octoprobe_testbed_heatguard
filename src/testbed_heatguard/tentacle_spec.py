from __future__ import annotations

import contextlib
import dataclasses
import logging
import pathlib
import typing

from octoprobe import util_mcu_pico
from octoprobe.lib_mpremote import ExceptionCmdFailed
from octoprobe.lib_tentacle import TentacleBase
from octoprobe.lib_tentacle_debugprobe import TentacleDebugprobe
from octoprobe.usb_tentacle.usb_tentacle import UsbTentacle
from octoprobe.util_baseclasses import TentacleInstance, TentacleSpecBase
from octoprobe.util_constants import TAG_MCU
from octoprobe.util_firmware_spec import FirmwareDownloadSpec
from octoprobe.util_pytest.util_func_logger import func_logger
from octoprobe.util_pyudev import UdevPoller

from .constants import (
    FILENAME_DUT_MAIN,
    TAG_BOARD,
    TAG_BUILD_VARIANTS,
)
from .util_diag import Diag

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_DUT_FIRWARE_SPEC = DIRECTORY_OF_THIS_FILE / "util_tentacle_dut_firmware.json"

I2C_ADDRESS_Tguard = 0x48
I2C_ADDRESS_Tref = 0x49
I2C_ADDRESS_EEPROM = 0x50
I2C_ADDRESS_OFFSET_DISCONNECT = 4


@dataclasses.dataclass(frozen=True, repr=True, eq=True, order=True)
class TentacleSpecHeatguard(TentacleSpecBase):
    @property
    def micropython_board(self) -> str:
        """
        If
          tags="board=ESP8266_GENERIC, ..."
        is defined, it will be used.
        Fallback to 'tentacle_tag'.
        """
        board = self.get_tag(TAG_BOARD)
        if board is not None:
            return board
        return self.tentacle_tag

    @property
    def description(self) -> str:
        mcu = self.get_tag(TAG_MCU)
        if mcu is None:
            return self.micropython_board
        return mcu + "/" + self.micropython_board

    @property
    def build_variants(self) -> list[str]:
        """
        Example for PICO: ["", "RISCV"]
        Example for ESP8266_GENERIC: [""]
        """
        variants = self.get_tag(TAG_BUILD_VARIANTS)
        if variants is None:
            return [""]
        return variants.split(":")


@dataclasses.dataclass
class Inject:
    inject_Tguard_disconnect: bool = False
    """
    True: Change the I2C address of Tguard to make it 'invisible'
    """
    inject_Tref_disconnect: bool = False
    """
    True: Change the I2C address of Tref to make it 'invisible'
    """
    inject_EEPROM_disconnect: bool = False
    """
    True: Change the I2C address of EEPROM to make it 'invisible'
    """
    inject_T_limit: bool = False
    """
    Open collector.
    False: open
    True: closed
    """
    sim_temperature_C: float | None = None
    """
    Start a LM75B I2C target simulator.
    Simulates Tguard/Tref wether on 'inject_Tgard/Tref_disconnect' is set.
    """
    sim_EEPROM_data: str | None = None
    """
    Start a EEPROM I2C target simulator
    """

    def __post_init__(self) -> None:
        assert isinstance(self.inject_Tguard_disconnect, bool)
        assert isinstance(self.inject_Tref_disconnect, bool)
        assert isinstance(self.inject_EEPROM_disconnect, bool)
        assert isinstance(self.inject_T_limit, bool)
        assert isinstance(self.sim_temperature_C, float | None)
        assert isinstance(self.sim_EEPROM_data, str | None)
        i2c_target_count = sum(
            (
                self.inject_Tguard_disconnect,
                self.inject_Tref_disconnect,
                self.inject_EEPROM_disconnect,
            )
        )
        assert i2c_target_count <= 1, "Only one I2C target may be simulated."
        if self.sim_temperature_C is not None:
            assert self.inject_Tguard_disconnect or self.inject_Tref_disconnect, (
                "If sim_temperature_C is given, a real sensor must be disconnected too."
            )
        if self.sim_EEPROM_data is not None:
            assert self.inject_EEPROM_disconnect, (
                "If sim_EEPROM_data is given, the real eeprom must be disconnected tool."
            )


class TentacleHeatguard(TentacleBase):  # pylint: disable=too-many-public-methods
    def __init__(
        self,
        tentacle_instance: TentacleInstance,
        usb_tentacle: UsbTentacle,
    ) -> None:
        super().__init__(
            tentacle_instance=tentacle_instance,
            usb_tentacle=usb_tentacle,
        )

        self._diag: Diag | None = None

    @property
    def diag(self) -> Diag:
        assert self._diag is not None, "Need to call 'init_diag()' first!"
        return self._diag

    def init_diag(self, diag: Diag) -> None:
        assert self._diag is None
        self._diag = diag

    def stop_diag(self) -> None:
        if self._diag is None:
            return
        self._diag.stop_reader_thread()
        self._diag = None

    @staticmethod
    def factory_usb_tentacle(usb_tentacle: UsbTentacle) -> TentacleHeatguard:
        """
        Create a temporary TentacleInfra
        """
        assert isinstance(usb_tentacle, UsbTentacle)
        # pylint: disable=import-outside-toplevel
        from .tentacles_inventory import TENTACLES_INVENTORY

        tentacle_instance = TENTACLES_INVENTORY.get_by_serial_delimited(
            usb_tentacle.serial_delimited
        )
        tentacle = TentacleHeatguard(
            tentacle_instance=tentacle_instance,
            usb_tentacle=usb_tentacle,
        )
        tentacle.tentacle_state.firmware_spec = FirmwareDownloadSpec.factory2(
            FILENAME_DUT_FIRWARE_SPEC
        )
        return tentacle

    @property
    def is_zephyr(self) -> bool:
        return self.tentacle_instance.solder_version.endswith("-zephyr")

    @property
    def debugprobe(self) -> TentacleDebugprobe:
        assert isinstance(self._probe, TentacleDebugprobe)
        return self._probe

    @property
    @typing.override
    def pytest_id(self) -> str:
        """
        Example: 1831
        """
        return f"{self.tentacle_serial_short}-{self.tentacle_instance.solder_version}"

    @property
    def tentacle_spec(self) -> TentacleSpecHeatguard:
        """TentacleHeatguard
        Just does typcasting from TentacleSpecBase to TentacleSpecHeatguard
        """
        tentacle_spec_base = self.tentacle_spec_base
        assert isinstance(tentacle_spec_base, TentacleSpecHeatguard)
        return tentacle_spec_base

    def copy_micropython_main(self, restart_dut: bool) -> None:
        src = FILENAME_DUT_MAIN
        logger.info(f"{self.dut.label}: Copy {src}")
        self.dut.mp_remote.cp(src=src, dest=":", multiple=False)
        if restart_dut:
            # Restart main
            self.dut.mp_remote.exec_raw(
                cmd="import machine; machine.reset()",
                follow=False,
            )

    def flash_dut_zephyr(
        self,
        udev: UdevPoller,
        firmware: pathlib.Path,
        directory_logs: pathlib.Path,
    ) -> None:
        assert self.dut is not None
        assert self.is_zephyr

        assert isinstance(udev, UdevPoller)
        assert isinstance(firmware, pathlib.Path)
        assert isinstance(directory_logs, pathlib.Path)

        if not firmware.is_file():
            logger.error(f"Firmware does not exist: {firmware}")
            return

        programmer = util_mcu_pico.DutProgrammerPicotool()
        event = programmer.enter_boot_mode(tentacle=self, udev=udev)
        util_mcu_pico.picotool_flash_micropython(
            event=event,
            directory_logs=directory_logs,
            filename_firmware=firmware,
        )

    @func_logger
    def set_power_dut(
        self,
        on: bool,
        udev: UdevPoller,
        start_dut_main: bool = True,
    ) -> None:
        logger.info(f"[COLOR_INFO]set_power_dut({on=} {start_dut_main=})")

        if on:
            # Power on DUT
            self.infra.power_dut_off_and_wait()

            # Drain the diag buffer
            self.diag.drain()

            tty = self.dut.dut_mcu.application_mode_power_up(tentacle=self, udev=udev)
            logger.info(f"{self.dut.label}: Powered up: {tty}")

        else:
            self.infra.power_dut_off_and_wait()

    @func_logger
    def load_mp_infra(self) -> None:
        """
        Load testbed_heatguard specific micropython source into pico_infra.
        """
        self.infra.mp_remote.exec_file(filename=DIRECTORY_OF_THIS_FILE / "mp_infra.py")

    @func_logger
    def load_dut_main_and_start_obsolete(self, start_dut_main: bool = True) -> None:
        """
        Copy main.py to the dut.
        Return True if the file has been copied and the dut must be powercycled.
        Return False if the file is already there and equal. No restart is needed.
        """
        src = FILENAME_DUT_MAIN
        dest = ":main.py"
        if not self.dut.mp_remote.file_equal(src=src, dest=dest):
            # Local file 'src' has changed: copy to device
            self.dut.mp_remote.cp(src=src, dest=dest, multiple=False)
            try:
                self.dut.mp_remote.exec_raw("import sys; sys.modules.pop('main', None)")
            except ExceptionCmdFailed as e:
                logger.debug(
                    f"{self.label}: Failed to remove main.py from the module cache: {e!r}"
                )

        # follow=False: send the command and return immediately; main() runs forever on the device
        if start_dut_main:
            self.dut.mp_remote.exec_raw("import main", follow=False)
            # Hack: The following line is required to avoid next 'exec_raw()' to hang.
            self.dut.mp_remote.state._auto_soft_reset = True  # pylint: disable=protected-access

        else:
            # Only load 'main.py' but does not start 'main()'.
            # This is helpful for testing logic without having the main-loop running
            self.dut.mp_remote.exec_raw("import rp2; rp2.SKIP_MAIN=True; import main")

    @func_logger
    def scan_i2c(self) -> list[int]:
        i2c_addresses = self.dut.mp_remote.read_list("main.i2c.scan_i2c()")
        return i2c_addresses

    @func_logger
    def set_inject(self, inject: Inject) -> None:
        dict_inject = dataclasses.asdict(inject)
        self.infra.mp_remote.read_None(f"set_inject({dict_inject!r})")

    @func_logger
    @contextlib.contextmanager
    def inject(self, inject: Inject) -> typing.Iterator[None]:
        self.set_inject(inject=inject)
        try:
            yield
        finally:
            self.set_inject(Inject())

    def _read_temperature_C(self, i2c_address: int, disconnect: bool) -> float:
        assert isinstance(i2c_address, int)
        assert isinstance(disconnect, bool)

        offset_disconnect = I2C_ADDRESS_OFFSET_DISCONNECT if disconnect else 0
        return self.dut.mp_remote.read_float(
            f"main.i2c.read_temperature_remote(addr={i2c_address + offset_disconnect})"
        )

    @func_logger
    def read_Tref_C(self, disconnect: bool = False) -> float:
        return self._read_temperature_C(I2C_ADDRESS_Tref, disconnect=disconnect)

    @func_logger
    def read_Tguard_C(self, disconnect: bool = False) -> float:
        return self._read_temperature_C(I2C_ADDRESS_Tguard, disconnect=disconnect)

    @func_logger
    def set_sim_temperature_C(self, temperature_C: float) -> None:
        """
        Set the temperature of the previously sim_Tref_enable/sim_Tguard_enable.
        """
        self.infra.mp_remote.read_None(
            f"simulation_i2c.set_temperature_C(temperature_C={temperature_C})"
        )

    @func_logger
    def read_EEPROM(self, disconnect: bool = False) -> str:
        assert isinstance(disconnect, bool)

        i2c_address = I2C_ADDRESS_EEPROM
        if disconnect:
            i2c_address += I2C_ADDRESS_OFFSET_DISCONNECT

        return self.dut.mp_remote.read_str(
            f"main.i2c.read_EEPROM_remote(addr={i2c_address})"
        )

    @func_logger
    def get_EEPROM_infra_sim(self) -> str:
        return self.infra.mp_remote.read_str("simulation_i2c.get_EEPROM()")
