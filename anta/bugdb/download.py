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
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import httpx

from anta.bugdb.models import AlertBaseDatabase

logger = logging.getLogger(__name__)

ALERTBASE_DEFAULT_HOST: Final[str] = "https://www.arista.com"
ALERTBASE_DOWNLOAD_URI: Final[str] = "/custom_data/bug-alert/alertBaseDownloadApi.php"
ALERTBASE_DEFAULT_URL: Final[str] = ALERTBASE_DEFAULT_HOST + ALERTBASE_DOWNLOAD_URI
DOWNLOAD_TIMEOUT: Final[float] = 120.0
BUGDB_CACHE_FILE: Final[str] = "AlertBase-CVP.json"
BUGDB_CACHE_TTL_HOURS: Final[float] = 12.0


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


def _get_cache_dir() -> Path:
    """Return the ANTA bug database cache directory."""
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg_cache) if xdg_cache else Path.home() / ".cache"
    return base / "anta"


def get_bug_database_cache_path() -> Path:
    """Return the path to the cached AlertBase database file."""
    return _get_cache_dir() / BUGDB_CACHE_FILE


def load_cached_database() -> tuple[AlertBaseDatabase, datetime] | None:
    """Load the AlertBase database from cache if available and not expired."""
    cache_path = get_bug_database_cache_path()
    if not cache_path.exists():
        return None
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)
    age_hours = (datetime.now(tz=timezone.utc) - mtime).total_seconds() / 3600
    if age_hours >= BUGDB_CACHE_TTL_HOURS:
        logger.info("Bug database cache expired (%.1fh old, TTL is %.0fh): %s", age_hours, BUGDB_CACHE_TTL_HOURS, cache_path)
        return None
    logger.info("Loading bug database from cache (%.1fh old): %s", age_hours, cache_path)
    return load_bug_database(cache_path), mtime


def save_database_to_cache(db: AlertBaseDatabase) -> Path:
    """Save the AlertBase database to the cache directory."""
    cache_path = get_bug_database_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(db.model_dump_json(by_alias=True), encoding="utf-8")
    logger.info("Bug database cached at %s", cache_path)
    return cache_path


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
