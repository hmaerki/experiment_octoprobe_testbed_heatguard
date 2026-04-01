# Chat Log 2026-04-01a — Heatguard Zephyr Port

## Request 1: Add a Claude specification/hints file

Created `/CLAUDE.md` at the project root with hints covering:
- Project purpose (Octoprobe HIL test environment for heatguard)
- Python ≥ 3.12, `.venv/`, `uv pip install`
- Lint/type-check/test commands (ruff, mypy strict, pylint, pytest)
- Code style (ruff target py312, E501 disabled, mypy strict, PEP 561)
- Project layout (`src/`, `tests/`, `docs/`, `commissioning/`, `kicad/`, `heatguard_zephyr/`)
- Key conventions (PDM backend, octoprobe dependency, test markers)

## Request 2: Follow the instructions in `heatguard_zephyr/CLAUDE.md`

The file `heatguard_zephyr/CLAUDE.md` instructed:

> This folder contains a zephyr application which runs on a Raspberry Pi Pico.
> The program is already implemented in micropython, see `./main.py`.
> This program should now be rewritten in C/C++ to run on zephyr.
>
> Required Results:
> - Directory structure as used for a common zephyr application.
> - Script which compiles the sources into the firmware using `ghcr.io/zephyrproject-rtos/zephyr-build:main`.

### Files created

```
heatguard_zephyr/
  west.yml                     # West manifest (zephyr + hal_rpi_pico + picolibc)
  CMakeLists.txt               # Zephyr CMake build file
  prj.conf                     # Kconfig: GPIO, I2C, UART, WDT, float printf
  build.sh                     # Docker build script (zephyr-build:main)
  boards/
    rpi_pico.overlay           # DT overlay: I2C1 GPIO6/7, UART0 9600 baud
  src/
    main.c                     # Full C port of main.py
```

### Port details

- **State machine** — `INIT → OK → FAILURE / GUARD` with same thresholds:
  - 80 °C guard trigger
  - 3 °C diff failure trigger
  - 60 s guard recovery timeout
- **Diagnostic UART** — parses the same commands:
  - `stimulus heatguard.update_temperatures(temperature_Tguard_C=…, diff_C=…)`
  - `stimulus heatguard.sensor_failed("…")`
  - `inject timeover`
  - `inject endless_loop`
  - `ping` → `pong 'response to ping'`
- **I2C** — raw register reads for LM75B (11-bit temperature) and AT24C02 EEPROM
- **Boot cause** — Zephyr `hwinfo` API → `PWRON_RESET` / `WDT_RESET`
- **LEDs** — GPIO26-29 status LEDs, GPIO16/17/25 XIAO onboard (active-low)
- **Watchdog** — 3 s hardware WDT via Zephyr WDT API
- **Build** — `./build.sh` runs Docker, outputs `zephyr.uf2` + `zephyr.elf`

### Bug note

The Python `sensor_failed()` had `self.state == (self.STATE_INIT, self.STATE_GUARD)` which always evaluates `False` (comparing a string to a tuple). The C port uses the likely intended `state == STATE_INIT || state == STATE_GUARD`.
