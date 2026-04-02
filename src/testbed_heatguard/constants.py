"""
Constants required by this testbed.
"""

from __future__ import annotations

import enum
import pathlib

from octoprobe.util_baseclasses import TENTACLE_TYPE_MCU
from octoprobe.util_constants import DIRECTORY_OCTOPROBE_GIT_CACHE

TAG_BUILD_VARIANTS = "build_variants"
TAG_BOARD = "board"

TESTBED_NAME = "testbed_heatguard"

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_REPO = DIRECTORY_OF_THIS_FILE.parent.parent
print(DIRECTORY_REPO / "pyproject.toml")
assert (DIRECTORY_REPO / "pyproject.toml").is_file()
DIRECTORY_DOWNLOADS = DIRECTORY_REPO / "downloads"
DIRECTORY_TESTRESULTS_DEFAULT = DIRECTORY_REPO / "testresults"
DIRECTORY_GIT_CACHE = DIRECTORY_OCTOPROBE_GIT_CACHE
FILENAME_TESTBED_LOCK = DIRECTORY_REPO / "testbed.lock"
FILENAME_DUT_MAIN = DIRECTORY_REPO / "heatguard_micropython" / "main.py"


class EnumTentacleType(enum.StrEnum):
    """
    Heatguard uses only one type of tentacles.
    """

    TENTACLE_MCU = TENTACLE_TYPE_MCU


class EnumFut(enum.StrEnum):
    FUT_MCU_ONLY = enum.auto()
