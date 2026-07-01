# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.sysdb — on-device Acons JSON parsing."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from anta.bugdb.sysdb import _build_acons_commands, fetch_sysdb_paths


class TestBuildAconsCommands:
    """Tests for _build_acons_commands."""

    def test_single_path(self) -> None:
        """Test building commands for a single path."""
        result = _build_acons_commands(["/Sysdb/routing/bgp/config"])
        assert result == "ls -l /ar/Sysdb/routing/bgp/config\nexit\n"

    def test_multiple_paths(self) -> None:
        """Test building commands for multiple paths."""
        result = _build_acons_commands(["/Sysdb/routing/bgp/config", "/Sysdb/snmp/config"])
        lines = result.strip().split("\n")
        assert lines[0] == "ls -l /ar/Sysdb/routing/bgp/config"
        assert lines[1] == "ls -l /ar/Sysdb/snmp/config"
        assert lines[2] == "exit"

    def test_wildcard_path(self) -> None:
        """Test that /* suffix is stripped from paths."""
        result = _build_acons_commands(["/Sysdb/routing/bgp/config/neighborConfig/*"])
        assert "ls -l /ar/Sysdb/routing/bgp/config/neighborConfig\n" in result

    def test_eos_path(self) -> None:
        """Test Eos paths get /ar prefix."""
        result = _build_acons_commands(["/Eos/image"])
        assert "ls -l /ar/Eos/image\n" in result


class TestFetchSysdbPaths:
    """Tests for fetch_sysdb_paths."""

    @pytest.mark.asyncio
    async def test_empty_paths(self) -> None:
        """Test with empty path set returns empty dict."""
        device = MagicMock()
        result = await fetch_sysdb_paths(device, set())
        assert not result

    @pytest.mark.asyncio
    async def test_command_failure(self) -> None:
        """Test when Acons command fails (output stays None)."""
        device = MagicMock()
        device.name = "test-device"

        async def mock_collect(cmds: list) -> None:
            pass  # Don't set output → collected stays False

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/test/path"})
        assert not result

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Test successful SysDB data fetch with JSON output."""
        device = MagicMock()
        device.name = "test-device"
        json_output = json.dumps(
            {
                "/Sysdb/routing/bgp/config": {
                    "asNumber": 65001,
                    "shutdown": False,
                }
            }
        )

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = json_output

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/routing/bgp/config"})
        assert "/Sysdb/routing/bgp/config" in result
        assert result["/Sysdb/routing/bgp/config"]["asNumber"] == 65001
        assert result["/Sysdb/routing/bgp/config"]["shutdown"] is False

    @pytest.mark.asyncio
    async def test_multiple_paths_fetch(self) -> None:
        """Test fetching multiple paths."""
        device = MagicMock()
        device.name = "test-device"
        json_output = json.dumps(
            {
                "/Sysdb/routing/bgp/config": {"asNumber": 65001},
                "/Sysdb/snmp/config": {"enabled": True},
            }
        )

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = json_output

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/routing/bgp/config", "/Sysdb/snmp/config"})
        assert len(result) == 2
        assert result["/Sysdb/routing/bgp/config"]["asNumber"] == 65001
        assert result["/Sysdb/snmp/config"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_empty_output(self) -> None:
        """Test empty command output returns empty dict."""
        device = MagicMock()
        device.name = "test-device"

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = ""

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/test/path"})
        assert not result

    @pytest.mark.asyncio
    async def test_invalid_json_output(self) -> None:
        """Test invalid JSON output returns empty dict."""
        device = MagicMock()
        device.name = "test-device"

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = "not valid json"

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/test/path"})
        assert not result

    @pytest.mark.asyncio
    async def test_value_types_preserved(self) -> None:
        """Test that JSON value types are preserved through the pipeline."""
        device = MagicMock()
        device.name = "test-device"
        json_output = json.dumps(
            {
                "/Sysdb/test": {
                    "boolTrue": True,
                    "boolFalse": False,
                    "integer": 42,
                    "floatVal": 3.14,
                    "string": "multi-agent",
                    "nullVal": None,
                }
            }
        )

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = json_output

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/test"})
        data = result["/Sysdb/test"]
        assert data["boolTrue"] is True
        assert data["boolFalse"] is False
        assert data["integer"] == 42
        assert data["floatVal"] == 3.14
        assert data["string"] == "multi-agent"
        assert data["nullVal"] is None

    @pytest.mark.asyncio
    async def test_not_found_paths_omitted(self) -> None:
        """Test that paths not found on device are omitted from results."""
        device = MagicMock()
        device.name = "test-device"
        json_output = json.dumps(
            {
                "/Sysdb/routing/bgp/config": {"asNumber": 65001},
            }
        )

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = json_output

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/routing/bgp/config", "/Sysdb/missing/path"})
        assert "/Sysdb/routing/bgp/config" in result
        assert "/Sysdb/missing/path" not in result
