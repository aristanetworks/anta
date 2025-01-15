# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Arista Network Test Automation (ANTA) Framework."""

import importlib.metadata
import os

__version__ = f"v{importlib.metadata.version('anta')}"
__credits__ = [
    "Angélique Phillipps",
    "Colin MacGiollaEáin",
    "Khelil Sator",
    "Matthieu Tâche",
    "Onur Gashi",
    "Paul Lavelle",
    "Guillaume Mulocher",
    "Thomas Grimonet",
]
__copyright__ = "Copyright 2022-2024, Arista Networks, Inc."

# ANTA Debug Mode environment variable
__DEBUG__ = os.environ.get("ANTA_DEBUG", "").lower() == "true"
if __DEBUG__:
    # enable asyncio DEBUG mode when __DEBUG__ is enabled
    os.environ["PYTHONASYNCIODEBUG"] = "1"


# Source: https://rich.readthedocs.io/en/stable/appendix/colors.html
# pylint: disable=R0903
class RICH_COLOR_PALETTE:
    """Color code for text rendering."""

    ERROR = "indian_red"
    FAILURE = "bold red"
    SUCCESS = "green4"
    SKIPPED = "bold orange4"
    HEADER = "cyan"
    UNSET = "grey74"


# Dictionary to use in a Rich.Theme: custom_theme = Theme(RICH_COLOR_THEME)
RICH_COLOR_THEME = {
    "success": RICH_COLOR_PALETTE.SUCCESS,
    "skipped": RICH_COLOR_PALETTE.SKIPPED,
    "failure": RICH_COLOR_PALETTE.FAILURE,
    "error": RICH_COLOR_PALETTE.ERROR,
    "unset": RICH_COLOR_PALETTE.UNSET,
}

GITHUB_SUGGESTION = "Please reach out to the maintainer team or open an issue on Github: https://github.com/aristanetworks/anta."
