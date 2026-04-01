#!/bin/bash
# Runs INSIDE the Docker container: full west init + update + build.
set -e

rm -rf .west bootloader build dts modules tools zephyr

echo "--- Initialising west workspace ---"
west init -l app
west update --narrow --fetch-opt=--depth=1

echo "--- Building for rpi_pico ---"
west build -b rpi_pico app