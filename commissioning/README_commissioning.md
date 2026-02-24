## Pin assignements

| PICO_INFRA | DUT | Signal |
| - | - | - |
| 10 | - | inject_Tref_disconnect |
| 11 | - | inject_EEPROM_disconnect |
| 12 | 6 | SDA |
| 13 | 7 | SCL |
| 14 | - | inject_Tguard_disconnect |
| 15 | 2 | inject_T_limit (overwrite Tguard over temperature output) |
| 16 (tx) | 1 | RX |
| 17 (rx) | 0 | TX |

## ERRORS

PICO_INFRA 16/17: Correct voltage when disconnected from mezzanine
PICO_INFRAS 12/13: Always 1 V when disconnected from mezzanine

## Test XIAO

```bash
op power --on dut
```

```bash
op power --off dut; op power --on relay1; sleep 1;op power --on dut; sleep 1; op power --off relay1

wget https://micropython.org/resources/firmware/RPI_PICO-20251209-v1.27.0.uf2
```


* LED

```bash
mpremote a1 run test_leds.py
```

* UART DUT->PICO_INFRA

```bash
mpremote a0 run uart_PICO_INFRA.py
mpremote a1 run uart_dut.py
```

* I2C

```bash
mpremote a0 run lm75b_target.py 
mpremote a1 run lm75b_controller.py 
```
