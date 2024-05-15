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

    If the port is avaialble then return True; False otherwise.

    Parameters
    ----------
        url: The URL that provides the target system
        timeout: Time to await for the port to open in seconds
    """
    port = url.port or socket.getservbyname(url.scheme)

    try:
        wr: asyncio.StreamWriter
        _, wr = await asyncio.wait_for(asyncio.open_connection(host=url.host, port=port), timeout=timeout)

        # MUST close if opened!
        wr.close()

    except TimeoutError:
        return False
    else:
        return True
