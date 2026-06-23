# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.download."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from anta.bugdb.download import ALERTBASE_DEFAULT_URL, download_bug_database, load_bug_database

DATA_DIR = Path(__file__).parents[2].resolve() / "data"

MINIMAL_DB = {"bugs": [], "tagImplication": [], "queryRules": [], "queryRulesRev": []}


def test_load_bug_database() -> None:
    """Test loading a bug database from a local file."""
    db = load_bug_database(DATA_DIR / "test_alertbase.json")
    assert len(db.bugs) == 5
    assert db.bugs[0].bug_id == 1001


def test_load_bug_database_invalid(tmp_path: Path) -> None:
    """Test loading an invalid JSON file."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{}", encoding="utf-8")
    with pytest.raises(Exception):  # noqa: B017, PT011
        load_bug_database(bad_file)


def test_load_bug_database_minimal(tmp_path: Path) -> None:
    """Test loading a minimal valid database."""
    minimal = tmp_path / "minimal.json"
    minimal.write_text(json.dumps(MINIMAL_DB), encoding="utf-8")
    db = load_bug_database(minimal)
    assert not db.bugs


@respx.mock
async def test_download_bug_database() -> None:
    """Test downloading bug database via HTTP."""
    respx.get(ALERTBASE_DEFAULT_URL).mock(return_value=httpx.Response(200, json=MINIMAL_DB))
    db = await download_bug_database("fake-token")
    assert not db.bugs


@respx.mock
async def test_download_bug_database_auth_header() -> None:
    """Test that the Bearer token is sent in the Authorization header."""
    route = respx.get(ALERTBASE_DEFAULT_URL).mock(return_value=httpx.Response(200, json=MINIMAL_DB))
    await download_bug_database("my-secret-token")
    assert route.called
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer my-secret-token"


@respx.mock
async def test_download_bug_database_http_error() -> None:
    """Test that HTTP errors are raised."""
    respx.get(ALERTBASE_DEFAULT_URL).mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError):
        await download_bug_database("bad-token")
