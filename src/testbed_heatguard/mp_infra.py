import machine  # type: ignore # pylint: disable=import-error

I2C_ADDRESS_Tguard = 0x48
I2C_ADDRESS_Tref = 0x49
I2C_ADDRESS_EEPROM = 0x50
I2C_ADDRESS_OFFSET_DISCONNECT = 4


class Diag:
    def __init__(self) -> None:
        self._uart = machine.UART(
            0,
            baudrate=9600,
            tx=machine.Pin("GPIO16"),
            rx=machine.Pin("GPIO17"),
            timeout=100,
        )
        self._rx_line: bytes = b""
        self._rx_queue: list[str] = []
        self._uart.irq(handler=self._irq_handler, trigger=machine.UART.IRQ_RXIDLE)

    def _irq_handler(self, uart_obj: machine.UART) -> None:
        data = uart_obj.read()
        if data is None:
            return
        assert isinstance(data, bytes)
        self._rx_line += data
        while b"\n" in self._rx_line:
            line, self._rx_line = self._rx_line.split(b"\n", 1)
            self._rx_queue.append(line.strip().decode("utf-8", "replace"))

    def get_lines(self, drain: bool = False) -> list[str]:
        lines = self._rx_queue
        if drain:
            self._rx_line = b""
            self._rx_queue = []
        return lines

    def drain(self) -> None:
        self.get_lines(drain=True)

    def readline(self) -> str | None:
        while True:
            msg = self._uart.readline()
            if msg is not None:
                assert isinstance(msg, bytes)
                return msg.strip().decode("utf-8", "replace")
            return None

    def writeline(self, line: str) -> None:
        self._uart.write(line + "\n")


class Inject:
    def __init__(self) -> None:
        self.Tref_disconnect = machine.Pin("GPIO10", machine.Pin.OUT)
        self.EEPROM_disconnect = machine.Pin("GPIO11", machine.Pin.OUT)
        self.Tguard_disconnect = machine.Pin("GPIO14", machine.Pin.OUT)
        self.T_limit = machine.Pin("GPIO15", machine.Pin.OPEN_DRAIN)
        self.reset()

    def reset(self) -> None:
        self.Tref_disconnect.value(0)
        self.EEPROM_disconnect.value(0)
        self.Tguard_disconnect.value(0)
        self.T_limit.value(1)


class SimulationI2C:
    EEPROM_START_BYTE = 0x00
    EEPROM_SIZE_BYTE = 0x200
    "2 Kbit = 0x800 bits = 0x200 bytes"

    def __init__(self) -> None:
        self._mem = bytearray(self.EEPROM_SIZE_BYTE)
        self._i2c: machine.I2CTarget | None = None

    def enable(self, addr: int) -> None:
        self.reset()

        self._i2c = machine.I2CTarget(
            0,
            sda=machine.Pin("GPIO12"),
            scl=machine.Pin("GPIO13"),
            mem=self._mem,
            addr=addr,
        )

    def reset(self) -> None:
        if self._i2c is not None:
            self._i2c.deinit()
            self._i2c = None

    def set_temperature_C(self, temperature_C: float) -> None:
        """
        LM75B:
        Convert temperature to LM75B format (11-bit, 0.125°C resolution)
        """
        assert self._i2c is not None

        temperature_raw = int(temperature_C / 0.125)

        if temperature_raw < 0:
            temperature_raw = temperature_raw + 0x800

        # Shift left by 5 bits (11-bit value in upper bits of 16-bit word)
        temperature_raw = temperature_raw << 5

        # Split into two bytes (MSB first)
        msb = (temperature_raw >> 8) & 0xFF
        lsb = temperature_raw & 0xFF

        self._mem[0] = msb
        self._mem[1] = lsb

    def set_EEPROM(self, data: str) -> None:
        data_bytes = data.encode("utf-8", "replace")
        data_bytes = data_bytes[0 : self.EEPROM_SIZE_BYTE]
        self._mem[0 : len(data_bytes)] = data_bytes

    def get_EEPROM(self) -> str:
        data_bytes = bytes(self._mem[0 : self.EEPROM_SIZE_BYTE])
        pos = data_bytes.find(b"\xff")
        if pos >= 0:
            data_bytes = data_bytes[0:pos]
        pos = data_bytes.find(b"\x00")
        if pos >= 0:
            data_bytes = data_bytes[0:pos]
        return data_bytes.decode("utf-8", "replace")


# diag = Diag()
inject = Inject()
simulation_i2c = SimulationI2C()


def set_inject(dict_inject: dict[str, bool | float | None]) -> None:
    """
    Example dict_inject:
        {
            "inject_Tguard_disconnect": False,
            "inject_Tref_disconnect": True,
            "inject_EEPROM_disconnect": False,
            "inject_T_limit": False,
            "sim_temperature_C": 82.25,
            "sim_EEPROM_data": None,
        }

    There are many invalid combinations of 'dict_inject'.
    For example {'inject_Tref_disconnect': True, 'sim_temperature_C': 82,5} is valid.
    For example {'inject_Tref_disconnect': True, 'sim_EEPROM_data': 'data'} is conflicting.
    It is assumed, that we have been passed meaningful values.
    """
    inject.Tguard_disconnect.value(dict_inject["inject_Tguard_disconnect"])
    inject.Tref_disconnect.value(dict_inject["inject_Tref_disconnect"])
    inject.EEPROM_disconnect.value(dict_inject["inject_EEPROM_disconnect"])
    inject.T_limit.value(dict_inject["inject_T_limit"])
    sim_temperature_C = dict_inject["sim_temperature_C"]
    sim_EEPROM_data = dict_inject["sim_EEPROM_data"]
    if sim_temperature_C is None:
        simulation_i2c.reset()
    if sim_EEPROM_data is None:
        simulation_i2c.reset()
    if sim_temperature_C is not None:
        addr = (
            I2C_ADDRESS_Tguard if inject.Tguard_disconnect.value() else I2C_ADDRESS_Tref
        )
        simulation_i2c.enable(addr=addr)
        simulation_i2c.set_temperature_C(sim_temperature_C)
        return
    if sim_EEPROM_data is not None:
        assert isinstance(sim_EEPROM_data, str)
        simulation_i2c.enable(addr=I2C_ADDRESS_EEPROM)
        simulation_i2c.set_EEPROM(sim_EEPROM_data)
        return


# Reset
set_inject(
    dict_inject={
        "inject_Tguard_disconnect": False,
        "inject_Tref_disconnect": False,
        "inject_EEPROM_disconnect": False,
        "inject_T_limit": False,
        "sim_temperature_C": None,
        "sim_EEPROM_data": None,
    }
)

print("[RESULT]success")
