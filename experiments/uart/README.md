# UART

These examples demonstrates how the PICO_INFRA uart reader survives a repl.

PICO_INFRA is a uart reader

DUT is a uart writer

## Test

Run a test so that PICO_INFRA and DUT have the micropython code loaded

DUT

```
mpremote a1 exec 'import rp2; rp2.SKIP_MAIN = True; import main; main.uart.ping_forever()'
```


PICO_INFRA

```
mpremote a1 exec 'uart.get_lines()'
```
