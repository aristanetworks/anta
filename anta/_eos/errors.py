# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Arista EOS command error classification helpers."""

from __future__ import annotations

from anta.constants import UNSUPPORTED_PLATFORM_ERROR_FRAGMENT, UNSUPPORTED_PLATFORM_ERROR_PREFIXES


def is_unsupported_platform_error(error: str) -> bool:
    """Return whether an EOS error indicates an unsupported command."""
    return error.startswith(UNSUPPORTED_PLATFORM_ERROR_PREFIXES) or UNSUPPORTED_PLATFORM_ERROR_FRAGMENT in error
