
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
