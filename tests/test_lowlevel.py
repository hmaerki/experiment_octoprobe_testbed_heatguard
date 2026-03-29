from testbed_heatguard import util_ctx
from testbed_heatguard.tentacle_spec import Inject

# pylint: disable=W0613:unused-argument


# @pytest.mark.required_futs(EnumFut.FUT_I2C)
def test_uart_test(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True)

    tentacle.diag_infra_waitfor("probe state OK True 'Initial state after power up'")
    tentacle.diag_infra_write("ping")
    tentacle.diag_infra_waitfor("pong 'response to ping'")

    # mcu.dut.inspection_exit()


def test_read_Tguard(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True, start_dut_main=False)

    i2c_addresses = tentacle.scan_i2c()
    i2c_addresses_text = [f"0x{addr:02X}" for addr in i2c_addresses]
    print(f"{i2c_addresses_text=}")

    Tguard_C = tentacle.read_Tguard_C()
    print(f"{Tguard_C=}")

    # mcu.dut.inspection_exit()


def test_read_Tguard_sim(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True, start_dut_main=False)

    tentacle.diag_dut_writeline("Hello from DUT")

    with tentacle.inject(Inject(inject_Tref_disconnect=True, sim_temperature_C=82.25)):
        print(f"Tguard_C={tentacle.read_Tguard_C():0.6f}")
        print(f"Tref_C={tentacle.read_Tref_C():0.6f}")

        tentacle.set_sim_temperature_C(43.0)
        print(f"Tguard_C={tentacle.read_Tguard_C():0.6f}")
        print(f"Tref_C={tentacle.read_Tref_C():0.6f}")

    print(f"Tguard_C={tentacle.read_Tguard_C():0.6f}")
    print(f"Tref_C={tentacle.read_Tref_C():0.6f}")


def test_read_EEPROM(ctx: util_ctx.CtxTestrunHeatguard) -> None:
    tentacle = ctx.tentacle

    ctx.set_power_dut(on=True, start_dut_main=False)

    with tentacle.inject(
        Inject(
            inject_EEPROM_disconnect=True,
            sim_EEPROM_data="{'a': 'b'}",
        )
    ):
        print(f"EEPROM={tentacle.read_EEPROM()}")
