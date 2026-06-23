# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.sysdb — Acons output parsing."""

from __future__ import annotations

from anta.bugdb.sysdb import _coerce_value, _extract_ls_sections, _parse_ls_output


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
        """Test parsing attribute lines."""
        section = "  asNumber                : 65001\n  shutdown                : False\n  enabled                 : True"
        result = _parse_ls_output(section)
        assert result is not None
        assert result.get("asNumber") == 65001
        assert result.get("shutdown") is False
        assert result.get("enabled") is True

    def test_parse_string_value(self) -> None:
        """Test parsing string attribute values."""
        section = "  protocolAgentModel      : multi-agent"
        result = _parse_ls_output(section)
        assert result is not None
        assert result.get("protocolAgentModel") == "multi-agent"

    def test_empty_section(self) -> None:
        """Test parsing empty section."""
        assert _parse_ls_output("") is None
        assert _parse_ls_output("   ") is None
