#!/bin/bash
# Rebuild the heatguard Zephyr firmware without re-initialising the
# west workspace.  Run ./build_and_init.sh first to create the workspace.
set -e
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/build_and_init.sh" support/build.sh