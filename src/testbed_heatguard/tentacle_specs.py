from __future__ import annotations

import dataclasses

from octoprobe import util_mcu_pico, util_mcu_pyboard

from testbed_heatguard.constants import EnumFut, EnumTentacleType

from .tentacle_spec import TentacleSpecHeatguard


DOC_TENTACLE_RPI_PICO = """
See: https://github.com/octoprobe/testbed_heatguard/tree/main/docs/tentacle_MCU_RPI_PICO
"""
MCU_RPI_PICO = TentacleSpecHeatguard(
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="MCU_RPI_PICO",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_I2C,
        EnumFut.FUT_UART,
        EnumFut.FUT_ONEWIRE,
        EnumFut.FUT_TIMER,
    ],
    doc=DOC_TENTACLE_RPI_PICO,
    mcu_usb_id=util_mcu_pico.RPI_PICO_USB_ID,
    tags="boards=RPI_PICO,mcu=rp2,programmer=picotool",
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
        EnumFut.FUT_I2C: [2, 3, 4, 5],
        EnumFut.FUT_ONEWIRE: [2, 3, 4],
    },
)
