import pathlib
import time

import pytest
from octoprobe.lib_mpremote import ExceptionCmdError, ExceptionCmdFailed

from testbed_heatguard import util_ctx
from testbed_heatguard.constants import EnumFut
from testbed_heatguard.tentacle_spec import Inject

# pylint: disable=W0613:unused-argument

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


# @pytest.mark.required_futs(EnumFut.FUT_I2C)
def test_uart_test(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    """ """
    dut = ctx.tentacle.dut
    infra = ctx.tentacle.infra

    ctx.set_power_dut(on=True)

    ctx.load_dut_main()
    dut.mp_remote.exec_raw(cmd='main.uart.writeline("Hello from DUT")', timeout=10)

    msg = infra.mp_remote.read_str(expr="uart.readline()")
    assert msg.strip() == "Hello from DUT"

    # mcu.dut.inspection_exit()
    pass


def test_read_Tguard(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    """ """
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True)

    ctx.load_dut_main()
    i2c_addresses = tentacle.scan_i2c()
    i2c_addresses = [f"0x{addr:02X}" for addr in i2c_addresses]
    print(f"{i2c_addresses=}")

    Tguard_C = tentacle.read_Tguard_C()
    print(f"{Tguard_C=}")

    # mcu.dut.inspection_exit()
    pass


def test_read_Tguard_sim(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    """ """
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True)

    ctx.load_dut_main()
    with tentacle.inject(Inject(inject_Tref_disconnect=True, sim_temperature_C=82.25)):
        print(f"Tguard_C={tentacle.read_Tguard_C():0.6f}")
        print(f"Tref_C={tentacle.read_Tref_C():0.6f}")

        tentacle.set_sim_temperature_C(43.0)
        print(f"Tguard_C={tentacle.read_Tguard_C():0.6f}")
        print(f"Tref_C={tentacle.read_Tref_C():0.6f}")

    print(f"Tguard_C={tentacle.read_Tguard_C():0.6f}")
    print(f"Tref_C={tentacle.read_Tref_C():0.6f}")


def test_read_EEPROM(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    """ """
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True)

    ctx.load_dut_main()

    with tentacle.inject(
        Inject(
            inject_EEPROM_disconnect=True,
            sim_EEPROM_data="{'a': 'b'}",
        )
    ):
        print(f"EEPROM={tentacle.read_EEPROM()}")
