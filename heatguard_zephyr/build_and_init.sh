#!/bin/bash
# Build the heatguard Zephyr firmware inside the official Zephyr Docker image.
#
# Usage:  ./build_and_init.sh                        # full init + build
#         ./build_and_init.sh support/build.sh       # rebuild only
#
# Output: zephyr.uf2 and zephyr.elf in this directory.
# Flash:  hold BOOTSEL, plug USB, copy zephyr.uf2 to the RPI-RP2 drive.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/.build_workspace"
DOCKER_SCRIPT="${1:-support/build_and_init.sh}"

echo "--- Preparing workspace in ${BUILD_DIR} ---"
mkdir -p "${BUILD_DIR}/app"
cp "${SCRIPT_DIR}/west.yml"       "${BUILD_DIR}/app/"
cp "${SCRIPT_DIR}/CMakeLists.txt" "${BUILD_DIR}/app/"
cp "${SCRIPT_DIR}/prj.conf"       "${BUILD_DIR}/app/"
cp -a "${SCRIPT_DIR}/src"         "${BUILD_DIR}/app/"
cp -a "${SCRIPT_DIR}/boards"      "${BUILD_DIR}/app/"
cp -a "${SCRIPT_DIR}/support"     "${BUILD_DIR}/"

docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "${BUILD_DIR}:/workspace" \
    -w /workspace \
    ghcr.io/zephyrproject-rtos/zephyr-build:main \
    bash "${DOCKER_SCRIPT}"

cp "${BUILD_DIR}/build/zephyr/zephyr.uf2" "${SCRIPT_DIR}/"
cp "${BUILD_DIR}/build/zephyr/zephyr.elf" "${SCRIPT_DIR}/"

echo ""
echo "Build complete!"
echo "  UF2 firmware: ${SCRIPT_DIR}/zephyr.uf2"
echo "  ELF firmware: ${SCRIPT_DIR}/zephyr.elf"
echo ""
echo "To flash: hold BOOTSEL, plug USB, copy zephyr.uf2 to the RPI-RP2 drive."
