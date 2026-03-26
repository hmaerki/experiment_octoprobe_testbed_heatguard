Test Examples
==============================

.. code-block:: python

    @pytest.fixture
    def dut_power_up(ctx: CtxTestrunHeatguard) -> Iterator[CtxTestrunHeatguard]:
        """
        Powers the dut.
        Waits till the dut is ready, eg 'state OK'.
        """
        ctx.set_power_dut(on=True)

        tty = ctx.tentacle.dut.get_tty()
        logger.info(f"DUT may be connected: mpremote connect {tty}")

        ctx.tentacle.diag_infra_waitfor(
            "probe state OK True 'Initial state after power up'"
        )

        yield ctx

    def test_Tguard_i2c_error(dut_power_up: CtxTestrunHeatguard):
        """
        Rationale: Behaviour when a temperature sensor fails
        Simulation: i2c-error Tguard
        Expected transitons: INIT -> OK -> FAILURE -> OK
        """
        tentacle = dut_power_up.tentacle

        # disconnect Tguard
        with tentacle.inject(Inject(inject_Tguard_disconnect=True)):
            tentacle.diag_infra_waitfor(
                "probe state FAILURE False 'I2C failed for sensor Tguard!"
            )

        tentacle.diag_infra_waitfor("probe state OK True")

    def test_Tguard_high(dut_power_up: CtxTestrunHeatguard):
        """
        Rationale: Behaviour when the guard sensor measures a high temperature
        Simulation: i2c Tguard 85C
        Expected transitons: INIT -> OK -> GUARD -> OK
        """
        tentacle = dut_power_up.tentacle

        # disconnect Tguard and simulate 85C
        with tentacle.inject(Inject(inject_Tguard_disconnect=True, sim_temperature_C=85.0)):
            tentacle.diag_infra_waitfor(
                "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'"
            )

        # The guard condition has gone, bug the guard state must remain
        with pytest.raises(TimeoutError):
            tentacle.diag_infra_waitfor("probe state OK", timeout_s=2.0)

        tentacle.diag_infra_write("inject timeover")

        tentacle.diag_infra_waitfor("probe state OK", timeout_s=70.0)
