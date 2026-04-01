#!/bin/bash
# Runs INSIDE the Docker container: rebuild only (reuses existing west workspace).
set -e

if [ ! -d .west ]; then
    echo "Error: No existing workspace. Run ./build_and_init.sh first." >&2
    exit 1
fi

echo "--- Building for rpi_pico ---"
west build -b rpi_pico app