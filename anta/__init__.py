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
__copyright__ = "Copyright 2022, Arista EMEA AS"

# Global ANTA debug environment variable. Can be set using the cli 'anta --debug'.
__DEBUG__ = bool(os.environ.get("ANTA_DEBUG", "").lower() == "true")


# Source: https://rich.readthedocs.io/en/stable/appendix/colors.html
# pylint: disable=R0903
class RICH_COLOR_PALETTE:
    """Color code for text rendering."""

    ERROR = "indian_red"
    FAILURE = "bold red"
    SUCCESS = "green4"
    SKIPPED = "bold orange4"
    HEADER = "cyan"


# Dictionary to use in a Rich.Theme: custom_theme = Theme(RICH_COLOR_THEME)
RICH_COLOR_THEME = {
    "success": RICH_COLOR_PALETTE.SUCCESS,
    "skipped": RICH_COLOR_PALETTE.SKIPPED,
    "failure": RICH_COLOR_PALETTE.FAILURE,
    "error": RICH_COLOR_PALETTE.ERROR,
}
