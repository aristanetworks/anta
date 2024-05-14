# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Optional
import socket
import asyncio

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------


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


async def port_check_url(url: URL, timeout: Optional[int] = 5) -> bool:
    """
    This function attempts to open the port designated by the URL given the
    timeout in seconds.  If the port is avaialble then return True; False
    otherwise.

    Parameters
    ----------
    url:
        The URL that provides the target system

    timeout: optional, default is 5 seonds
        Time to await for the port to open in seconds
    """
    port = url.port or socket.getservbyname(url.scheme)

    try:
        wr: asyncio.StreamWriter
        _, wr = await asyncio.wait_for(
            asyncio.open_connection(host=url.host, port=port), timeout=timeout
        )

        # MUST close if opened!
        wr.close()
        return True

    except Exception:  # noqa
        return False
