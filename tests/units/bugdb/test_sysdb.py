# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.sysdb — Acons output parsing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from anta.bugdb.sysdb import _classify_acons_line, _coerce_value, _extract_ls_sections, _parse_ls_output, fetch_sysdb_paths


class TestCoerceValue:
    """Tests for _coerce_value."""

    def test_bool_true(self) -> None:
        """Test boolean True coercion."""
        assert _coerce_value("True") is True
        assert _coerce_value("true") is True

    def test_bool_false(self) -> None:
        """Test boolean False coercion."""
        assert _coerce_value("False") is False
        assert _coerce_value("false") is False

    def test_none_values(self) -> None:
        """Test None coercion."""
        assert _coerce_value("None") is None
        assert _coerce_value("[]") is None
        assert _coerce_value("") is None

    def test_integer(self) -> None:
        """Test integer coercion."""
        assert _coerce_value("42") == 42
        assert _coerce_value("0") == 0
        assert _coerce_value("65001") == 65001

    def test_float(self) -> None:
        """Test float coercion."""
        assert _coerce_value("3.14") == 3.14

    def test_string(self) -> None:
        """Test string passthrough."""
        assert _coerce_value("multi-agent") == "multi-agent"
        assert _coerce_value("hello world") == "hello world"


class TestExtractLsSections:
    """Tests for _extract_ls_sections."""

    def test_single_entity(self) -> None:
        """Test extracting a single entity's attributes."""
        output = (
            "Connecting to agent Sysdb on port 0, socket @00001\n"
            "Connected to process 3872\n"
            "$ /ar/Sysdb/routing/bgp/config is <entity(...)>\n"
            "  asNumber                : 65001\n"
            "  shutdown                : False\n"
            "$ Connection closed by server\n"
        )
        sections = _extract_ls_sections(output)
        assert len(sections) == 1
        assert "asNumber" in sections[0]

    def test_multiple_entities(self) -> None:
        """Test extracting multiple entities."""
        output = (
            "Connecting to agent Sysdb on port 0, socket @00001\n"
            "Connected to process 3872\n"
            "$ /ar/Sysdb/routing/bgp/config is <entity(...)>\n"
            "  asNumber                : 65001\n"
            "$ /ar/Sysdb/l3/status/protocolAgentModelStatus is <entity(...)>\n"
            "  protocolAgentModel      : multi-agent\n"
            "$ Connection closed by server\n"
        )
        sections = _extract_ls_sections(output)
        assert len(sections) == 2

    def test_not_found(self) -> None:
        """Test handling of 'not found' paths."""
        output = "Connecting to agent Sysdb on port 0, socket @00001\nConnected to process 3872\n$ Directory enabled not found\n$ Connection closed by server\n"
        sections = _extract_ls_sections(output)
        assert len(sections) == 1
        assert sections[0] == ""


class TestParseLsOutput:
    """Tests for _parse_ls_output."""

    def test_parse_attributes(self) -> None:
        """Test parsing attribute lines — values are wrapped in {"value": v}."""
        section = "  asNumber                : 65001\n  shutdown                : False\n  enabled                 : True"
        result = _parse_ls_output(section)
        assert result is not None
        assert result["asNumber"] == {"value": 65001}  # pylint: disable=unsubscriptable-object
        assert result["shutdown"] == {"value": False}  # pylint: disable=unsubscriptable-object
        assert result["enabled"] == {"value": True}  # pylint: disable=unsubscriptable-object

    def test_parse_string_value(self) -> None:
        """Test parsing string attribute values — wrapped in {"value": v}."""
        section = "  protocolAgentModel      : multi-agent"
        result = _parse_ls_output(section)
        assert result is not None
        assert result["protocolAgentModel"] == {"value": "multi-agent"}  # pylint: disable=unsubscriptable-object

    def test_empty_section(self) -> None:
        """Test parsing empty section."""
        assert _parse_ls_output("") is None
        assert _parse_ls_output("   ") is None

    def test_no_matching_lines(self) -> None:
        """Test parsing section with no attribute : value lines."""
        assert _parse_ls_output("no colons here\njust text") is None


class TestClassifyAconsLine:
    """Tests for _classify_acons_line."""

    def test_skip_banner(self) -> None:
        """Test banner lines are classified as skip."""
        assert _classify_acons_line("Connecting to agent Sysdb") == "skip"
        assert _classify_acons_line("Connected to process 1234") == "skip"
        assert _classify_acons_line("Connection closed") == "skip"

    def test_skip_empty(self) -> None:
        """Test empty and prompt-only lines are skip."""
        assert _classify_acons_line("") == "skip"
        assert _classify_acons_line("$") == "skip"

    def test_header(self) -> None:
        """Test entity header lines."""
        assert _classify_acons_line("/ar/Sysdb/routing/bgp/config is <entity>") == "header"
        assert _classify_acons_line("/Sysdb/routing/bgp/config is <entity>") == "header"

    def test_not_found(self) -> None:
        """Test 'not found' detection."""
        assert _classify_acons_line("Directory enabled not found") == "not_found"

    def test_data(self) -> None:
        """Test regular data lines."""
        assert _classify_acons_line("asNumber : 65001") == "data"


class TestFetchSysdbPaths:
    """Tests for fetch_sysdb_paths."""

    @pytest.mark.asyncio
    async def test_empty_paths(self) -> None:
        """Test with empty path set returns empty dict."""
        device = MagicMock()
        result = await fetch_sysdb_paths(device, set())
        assert result == {}

    @pytest.mark.asyncio
    async def test_command_failure(self) -> None:
        """Test when Acons command fails (output stays None)."""
        device = MagicMock()
        device.name = "test-device"

        async def mock_collect(cmds: list) -> None:
            pass  # Don't set output → collected stays False

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/test/path"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Test successful SysDB data fetch."""
        device = MagicMock()
        device.name = "test-device"
        acons_output = (
            "Connecting to agent Sysdb on port 0\n"
            "Connected to process 1234\n"
            "$ /ar/Sysdb/routing/bgp/config is <entity>\n"
            "  asNumber                : 65001\n"
            "  shutdown                : False\n"
            "$ Connection closed\n"
        )

        async def mock_collect(cmds: list) -> None:
            cmds[0].output = acons_output

        device.collect_commands = AsyncMock(side_effect=mock_collect)
        result = await fetch_sysdb_paths(device, {"/Sysdb/routing/bgp/config"})
        assert "/Sysdb/routing/bgp/config" in result
        assert result["/Sysdb/routing/bgp/config"]["asNumber"] == {"value": 65001}


class TestExtractLsSectionsExtended:
    """Extended tests for _extract_ls_sections."""

    def test_sections_more_than_paths(self) -> None:
        """Test when more sections than expected paths."""
        output = (
            "Connecting to agent Sysdb\n"
            "Connected to process 1234\n"
            "$ /ar/Sysdb/path1 is <entity>\n"
            "  attr1 : val1\n"
            "$ /ar/Sysdb/path2 is <entity>\n"
            "  attr2 : val2\n"
            "$ /ar/Sysdb/path3 is <entity>\n"
            "  attr3 : val3\n"
        )
        sections = _extract_ls_sections(output)
        assert len(sections) == 3

    def test_data_outside_section(self) -> None:
        """Test that data lines outside a section are ignored."""
        output = "Connecting to agent Sysdb\nConnected to process 1234\n  attr1 : value1\n$ Connection closed\n"
        sections = _extract_ls_sections(output)
        assert len(sections) == 0
