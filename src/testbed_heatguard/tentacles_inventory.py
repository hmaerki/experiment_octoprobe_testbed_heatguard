from octoprobe.usb_tentacle.usb_constants import HwVersion
from octoprobe.util_baseclasses import TentaclesCollector

from testbed_heatguard.constants import TESTBED_NAME

from . import tentacle_specs

TENTACLES_INVENTORY = (
    TentaclesCollector(testbed_name=TESTBED_NAME).add_testbed_instance(
        testbed_instance="ch_hans_1",
        tentacles=[
            (
                # HeatGuart v0.1
                "de6528b3cb68-3836",
                HwVersion.V06,
                "v1.0",
                tentacle_specs.MCU_HEADGUARD,
            ),
            (
                # HeatGuart v0.2
                "de6528b3cb64-6938",
                HwVersion.V06,
                "v1.0-zephyr",
                tentacle_specs.MCU_HEADGUARD,
            ),
            (
                # Demo Teqable
                # HeatGuart v0.1
                "de6528b3cb4a-4b35",
                HwVersion.V06,
                "v1.0",
                tentacle_specs.MCU_HEADGUARD,
            ),
        ],
    )
).inventory
