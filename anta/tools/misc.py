"""
Toolkit for ANTA.
"""

from __future__ import annotations

import logging
import traceback

logger = logging.getLogger(__name__)


def exc_to_str(exception: Exception) -> str:
    """
    Helper function that returns a human readable string from an Exception object
    """
    return f"{type(exception).__name__}{f' ({str(exception)})' if str(exception) else ''}"


def tb_to_str(exception: Exception) -> str:
    """
    Helper function that returns a traceback string from an Exception object
    """
    return "Traceback (most recent call last):\n" + "".join(traceback.format_tb(exception.__traceback__))
