# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.download."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest
import respx

from anta.bugdb.download import ALERTBASE_DEFAULT_URL, download_bug_database, load_bug_database, load_cached_database, save_database_to_cache
from anta.bugdb.models import AlertBaseDatabase

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
    """Test downloading bug database via HTTP POST."""
    respx.post(ALERTBASE_DEFAULT_URL).mock(return_value=httpx.Response(200, json=MINIMAL_DB))
    db = await download_bug_database("fake-token")
    assert not db.bugs


@respx.mock
async def test_download_bug_database_token_encoding() -> None:
    """Test that the token is base64-encoded in the POST body."""
    route = respx.post(ALERTBASE_DEFAULT_URL).mock(return_value=httpx.Response(200, json=MINIMAL_DB))
    await download_bug_database("my-secret-token")
    assert route.called
    request = route.calls[0].request
    body = json.loads(request.content)
    expected_encoded = base64.b64encode(b"my-secret-token").decode()
    assert body["token_auth"] == expected_encoded
    assert body["file_version"] == "2"


@respx.mock
async def test_download_bug_database_http_error() -> None:
    """Test that HTTP errors are raised."""
    respx.post(ALERTBASE_DEFAULT_URL).mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError):
        await download_bug_database("bad-token")


def test_save_database_to_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test saving a database to the cache directory."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    db = AlertBaseDatabase.model_validate(MINIMAL_DB)
    cache_path = save_database_to_cache(db)
    assert cache_path.exists()
    assert cache_path == tmp_path / "anta" / "AlertBase-CVP.json"
    roundtrip = load_bug_database(cache_path)
    assert len(roundtrip.bugs) == len(db.bugs)


def test_load_cached_database_no_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_cached_database returns None when no cache exists."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert load_cached_database() is None


def test_load_cached_database_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading a valid (non-expired) cached database."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    db = AlertBaseDatabase.model_validate(MINIMAL_DB)
    save_database_to_cache(db)
    result = load_cached_database()
    assert result is not None
    loaded_db, cache_time = result
    assert len(loaded_db.bugs) == 0
    assert cache_time is not None


def test_load_cached_database_expired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an expired cache returns None."""
    import os
    import time

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    db = AlertBaseDatabase.model_validate(MINIMAL_DB)
    cache_path = save_database_to_cache(db)
    # Set mtime to 13 hours ago
    old_time = time.time() - 13 * 3600
    os.utime(cache_path, (old_time, old_time))
    assert load_cached_database() is None


def test_load_cached_database_malformed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a malformed cache file is treated as a cache miss."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_dir = tmp_path / "anta"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "AlertBase-CVP.json"
    cache_file.write_text("not valid json {{{", encoding="utf-8")
    assert load_cached_database() is None


def test_load_cached_database_bad_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a cache file with invalid schema is treated as a cache miss."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_dir = tmp_path / "anta"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "AlertBase-CVP.json"
    cache_file.write_text(json.dumps({"unexpected": "data"}), encoding="utf-8")
    assert load_cached_database() is None


def test_get_cache_dir_xdg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that XDG_CACHE_HOME is respected."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "custom"))
    db = AlertBaseDatabase.model_validate(MINIMAL_DB)
    cache_path = save_database_to_cache(db)
    assert str(tmp_path / "custom" / "anta") in str(cache_path)


def test_get_cache_dir_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the default cache directory when XDG_CACHE_HOME is not set."""
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    from anta.bugdb.download import get_bug_database_cache_path

    cache_path = get_bug_database_cache_path()
    assert str(cache_path).endswith("anta/AlertBase-CVP.json")
    assert ".cache" in str(cache_path)
