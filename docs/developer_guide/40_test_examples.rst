Test Examples
==============================

.. code-block:: python

    @pytest.fixture
    def dut_power_up(tentacle: TentacleHeatguard) -> Iterator[TentacleHeatguard]:
        """
        Powers the dut.
        Waits till the dut is ready, eg 'state OK'.
        """
        assert TESTBED is not None

        tentacle.set_power_dut(on=True, udev=TESTBED.udev)

        tentacle.diag.waitfor("probe state OK True 'Initial state after power up'")

        yield tentacle

    def test_Tguard_i2c_error(dut_power_up: TentacleHeatguard) -> None:
        """
        Rationale: Behaviour when a temperature sensor fails
        Simulation: i2c-error Tguard
        Expected transitons: INIT -> OK -> FAILURE -> OK
        """
        # disconnect Tguard
        with dut_power_up.inject(Inject(inject_Tguard_disconnect=True)):
            dut_power_up.diag.waitfor(
                "probe state FAILURE False 'I2C failed for sensor Tguard!"
            )

        dut_power_up.diag.waitfor("probe state OK True")

    def test_Tguard_high(dut_power_up: TentacleHeatguard) -> None:
        """
        Rationale: Behaviour when the guard sensor measures a high temperature
        Simulation: i2c Tguard 85C
        Expected transitons: INIT -> OK -> GUARD -> OK
        """
        # disconnect Tguard and simulate 85C
        with dut_power_up.inject(
            Inject(inject_Tguard_disconnect=True, sim_temperature_C=85.0)
        ):
            dut_power_up.diag.waitfor(
                "probe state GUARD False 'Too hot! Activate guard: temperature_Tguard_C=85.000C'"
            )

        # The guard condition has gone, bug the guard state must remain
        with pytest.raises(TimeoutError):
            dut_power_up.diag.waitfor("probe state OK", timeout_s=2.0)

        dut_power_up.diag.write("inject timeover")

        dut_power_up.diag.waitfor("probe state OK", timeout_s=70.0)
