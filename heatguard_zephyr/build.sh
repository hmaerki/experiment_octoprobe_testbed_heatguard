#!/bin/bash
# Build the heatguard Zephyr firmware inside the official Zephyr Docker image.
#
# Usage:  ./build.sh
#
# Output: zephyr.uf2 and zephyr.elf in this directory.
# Flash:  hold BOOTSEL, plug USB, copy zephyr.uf2 to the RPI-RP2 drive.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use a host-side temp directory as the full west workspace so the
# container user has write permissions for .west/, build/, etc.
BUILD_DIR=$(mktemp -d)
trap 'rm -rf "${BUILD_DIR}"' EXIT

echo "--- Preparing workspace in ${BUILD_DIR} ---"
mkdir -p "${BUILD_DIR}/app"
cp "${SCRIPT_DIR}/west.yml"       "${BUILD_DIR}/app/"
cp "${SCRIPT_DIR}/CMakeLists.txt" "${BUILD_DIR}/app/"
cp "${SCRIPT_DIR}/prj.conf"       "${BUILD_DIR}/app/"
cp -a "${SCRIPT_DIR}/src"         "${BUILD_DIR}/app/"
cp -a "${SCRIPT_DIR}/boards"      "${BUILD_DIR}/app/"

docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "${BUILD_DIR}:/workspace" \
    -w /workspace \
    ghcr.io/zephyrproject-rtos/zephyr-build:main \
    bash -c '
        set -e

        echo "--- Initialising west workspace ---"
        west init -l app
        west update --narrow --fetch-opt=--depth=1

        echo "--- Building for rpi_pico ---"
        west build -b rpi_pico app
    '

cp "${BUILD_DIR}/build/zephyr/zephyr.uf2" "${SCRIPT_DIR}/"
cp "${BUILD_DIR}/build/zephyr/zephyr.elf" "${SCRIPT_DIR}/"

echo ""
echo "Build complete!"
echo "  UF2 firmware: ${SCRIPT_DIR}/zephyr.uf2"
echo "  ELF firmware: ${SCRIPT_DIR}/zephyr.elf"
echo ""
echo "To flash: hold BOOTSEL, plug USB, copy zephyr.uf2 to the RPI-RP2 drive."
