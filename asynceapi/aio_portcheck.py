# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# Initially written by Jeremy Schulman at https://github.com/jeremyschulman/aio-eapi
"""Utility function to check if a port is open."""
# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import asyncio
import socket
from typing import TYPE_CHECKING

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

if TYPE_CHECKING:
    from httpx import URL

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["port_check_url"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


async def port_check_url(url: URL, timeout: int = 5) -> bool:
    """
    Open the port designated by the URL given the timeout in seconds.

    Parameters
    ----------
    url
        The URL that provides the target system.
    timeout
        Time to await for the port to open in seconds.

    Returns
    -------
    bool
        If the port is available then return True; False otherwise.
    """
    port = url.port or socket.getservbyname(url.scheme)

    try:
        wr: asyncio.StreamWriter
        _, wr = await asyncio.wait_for(asyncio.open_connection(host=url.host, port=port), timeout=timeout)

        # MUST close if opened!
        wr.close()

    except TimeoutError:
        return False
    return True
