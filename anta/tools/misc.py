"""
Toolkit for ANTA.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def exc_to_str(exception: Exception) -> str:
    """
    Helper function to parse Exceptions
    """
    return f"{type(exception).__name__}{f' ({str(exception)})' if str(exception) else ''}"
