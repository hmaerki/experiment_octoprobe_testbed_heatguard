#!/bin/bash
# Build the heatguard Zephyr firmware inside the official Zephyr Docker image.
#
# Usage:  ./build.sh
#
# Output: zephyr.uf2 and zephyr.elf in this directory.
# Flash:  hold BOOTSEL, plug USB, copy zephyr.uf2 to the RPI-RP2 drive.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker run --rm \
    -v "${SCRIPT_DIR}:/workspace/app" \
    -w /workspace \
    ghcr.io/zephyrproject-rtos/zephyr-build:main \
    bash -c '
        set -e

        echo "--- Initialising west workspace ---"
        west init -l app
        west update --narrow --fetch-opt=--depth=1

        echo "--- Building for rpi_pico ---"
        west build -b rpi_pico app

        echo "--- Copying artefacts ---"
        cp build/zephyr/zephyr.uf2 app/
        cp build/zephyr/zephyr.elf app/
    '

echo ""
echo "Build complete!"
echo "  UF2 firmware: ${SCRIPT_DIR}/zephyr.uf2"
echo "  ELF firmware: ${SCRIPT_DIR}/zephyr.elf"
echo ""
echo "To flash: hold BOOTSEL, plug USB, copy zephyr.uf2 to the RPI-RP2 drive."
