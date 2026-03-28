from __future__ import annotations

from octoprobe import util_mcu_pico

from testbed_heatguard.constants import EnumFut, EnumTentacleType

from .tentacle_spec import TentacleSpecHeatguard

MCU_HEADGUARD = TentacleSpecHeatguard(
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="MCU_HEADGUARD",
    futs=[],
    doc="",
    mcu_usb_id=util_mcu_pico.RPI_PICO_USB_ID,
    tags="boards=RPI_PICO,mcu=rp2,programmer=picotool,probe=debugprobe",
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
    },
)
