# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Download or load the AlertBase bug database."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Final

import httpx

if TYPE_CHECKING:
    from pathlib import Path

from anta.bugdb.models import AlertBaseDatabase

logger = logging.getLogger(__name__)

ALERTBASE_DEFAULT_URL: Final[str] = "https://www.arista.com/custom_data/bug-alert/alertBaseAll-CVP.json"
DOWNLOAD_TIMEOUT: Final[float] = 120.0


async def download_bug_database(token: str, url: str = ALERTBASE_DEFAULT_URL) -> AlertBaseDatabase:
    """Download and parse the AlertBase database from arista.com.

    Parameters
    ----------
    token
        Bearer API token for arista.com authentication.
    url
        URL to download from. Defaults to the Arista bug alert endpoint.

    Returns
    -------
    AlertBaseDatabase
        Parsed bug database.

    Raises
    ------
    httpx.HTTPStatusError
        If the download fails.
    """
    logger.info("Downloading bug database from %s", url)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
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
