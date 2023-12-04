# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Toolkit for ANTA.
"""
from __future__ import annotations

import logging
import traceback

logger = logging.getLogger(__name__)


def exc_to_str(exception: BaseException) -> str:
    """
    Helper function that returns a human readable string from an BaseException object
    """
    return f"{type(exception).__name__}{f' ({exception})' if str(exception) else ''}"


def tb_to_str(exception: BaseException) -> str:
    """
    Helper function that returns a traceback string from an BaseException object
    """
    return "Traceback (most recent call last):\n" + "".join(traceback.format_tb(exception.__traceback__))
