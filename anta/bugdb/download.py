# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Download or load the AlertBase bug database.

The AlertBase database is downloaded from ``www.arista.com`` via an authenticated
HTTP POST to the ``alertBaseDownloadApi.php`` endpoint. The token is a 32-character
alphanumeric string configured in the user's arista.com account.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import TYPE_CHECKING, Final

import httpx

if TYPE_CHECKING:
    from pathlib import Path

from anta.bugdb.models import AlertBaseDatabase

logger = logging.getLogger(__name__)

ALERTBASE_DEFAULT_HOST: Final[str] = "https://www.arista.com"
ALERTBASE_DOWNLOAD_URI: Final[str] = "/custom_data/bug-alert/alertBaseDownloadApi.php"
ALERTBASE_DEFAULT_URL: Final[str] = ALERTBASE_DEFAULT_HOST + ALERTBASE_DOWNLOAD_URI
DOWNLOAD_TIMEOUT: Final[float] = 120.0


async def download_bug_database(token: str, url: str = ALERTBASE_DEFAULT_URL) -> AlertBaseDatabase:
    """Download and parse the AlertBase database from arista.com.

    Uses an HTTP POST with the token in the JSON body, matching the CloudVision
    download mechanism (``aeris/bugalerts``).

    Parameters
    ----------
    token
        arista.com API token (32-character alphanumeric string).
    url
        URL to download from. Defaults to the Arista alertBaseDownloadApi endpoint.

    Returns
    -------
    AlertBaseDatabase
        Parsed bug database.

    Raises
    ------
    httpx.HTTPStatusError
        If the download fails.
    RuntimeError
        If the token validation fails or the response is not valid JSON.
    """
    encoded_token = base64.b64encode(token.encode()).decode()

    logger.info("Downloading bug database from arista.com")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={
                "token_auth": encoded_token,
                "file_version": "2",
            },
            timeout=DOWNLOAD_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

    logger.info("Downloaded bug database (%d bugs)", len(data.get("bugs", [])))
    return AlertBaseDatabase.model_validate(data)


def load_bug_database(path: Path) -> AlertBaseDatabase:
    """Load the AlertBase database from a local JSON file.

    Parameters
    ----------
    path
        Path to the AlertBase-CVP.json file.

    Returns
    -------
    AlertBaseDatabase
        Parsed bug database.
    """
    logger.info("Loading bug database from %s", path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded bug database (%d bugs)", len(data.get("bugs", [])))
    return AlertBaseDatabase.model_validate(data)
