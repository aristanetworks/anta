# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.aql — AQL interpreter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from anta.bugdb.aql import aql_compile, aql_evaluate, aql_tokenize


class TestAqlTokenizer:
    """Tests for the AQL tokenizer."""

    def test_empty(self) -> None:
        """Test tokenizing empty string."""
        tokens = aql_tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type.name == "EOF"

    def test_number(self) -> None:
        """Test tokenizing numbers."""
        tokens = aql_tokenize("42 3.14")
        assert tokens[0].value == 42
        assert tokens[1].value == 3.14

    def test_string(self) -> None:
        """Test tokenizing strings."""
        tokens = aql_tokenize('"hello"')
        assert tokens[0].value == "hello"

    def test_single_quote_string(self) -> None:
        """Test AQL rev 5 single-quote strings."""
        tokens = aql_tokenize("'json:{\"key\": 1}'")
        assert tokens[0].value == 'json:{"key": 1}'

    def test_path_query(self) -> None:
        """Test tokenizing path queries."""
        tokens = aql_tokenize("`{_d}:/Sysdb/routing/bgp/config`")
        assert tokens[0].type.name == "PATH_QUERY"
        path, field_filter = tokens[0].value
        assert path == "{_d}:/Sysdb/routing/bgp/config"
        assert field_filter is None

    def test_path_query_with_field_filter(self) -> None:
        """Test path queries with field selection."""
        tokens = aql_tokenize('`<d>:/Sysdb/path`{"field1", "field2"}')
        path, field_filter = tokens[0].value
        assert path == "<d>:/Sysdb/path"
        assert field_filter == ["field1", "field2"]

    def test_comments(self) -> None:
        """Test that comments are skipped."""
        tokens = aql_tokenize("42 # this is a comment\n43")
        assert tokens[0].value == 42
        assert tokens[1].value == 43

    def test_keywords(self) -> None:
        """Test keyword recognition."""
        tokens = aql_tokenize("let if for in true false")
        names = [t.type.name for t in tokens[:-1]]
        assert names == ["LET", "IF", "FOR", "IN", "BOOL_TRUE", "BOOL_FALSE"]

    def test_operators(self) -> None:
        """Test operator tokenization."""
        tokens = aql_tokenize("== != >= <= && || > < + - * / % ^")
        names = [t.type.name for t in tokens[:-1]]
        assert names == ["EQ", "NEQ", "GTE", "LTE", "AND", "OR", "GT", "LT", "PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "CARET"]


class TestAqlParser:
    """Tests for the AQL parser."""

    def test_literal(self) -> None:
        """Test parsing a literal."""
        ast = aql_compile("42")
        assert ast.__class__.__name__ == "AqlLiteral"

    def test_binary_op(self) -> None:
        """Test parsing binary operations."""
        ast = aql_compile("1 + 2")
        assert ast.__class__.__name__ == "AqlBinaryOp"

    def test_let_statement(self) -> None:
        """Test parsing let statements."""
        ast = aql_compile("let x = 42")
        assert ast.__class__.__name__ == "AqlLetStmt"

    def test_subscript(self) -> None:
        """Test parsing subscript access."""
        ast = aql_compile('x["key"]')
        assert ast.__class__.__name__ == "AqlSubscript"

    def test_pipe_filter(self) -> None:
        """Test parsing pipe filters."""
        ast = aql_compile("x | map(_value)")
        assert ast.__class__.__name__ == "AqlPipeFilter"

    def test_function_call(self) -> None:
        """Test parsing function calls."""
        ast = aql_compile("length(x)")
        assert ast.__class__.__name__ == "AqlFunctionCall"

    def test_if_statement(self) -> None:
        """Test parsing if statements."""
        ast = aql_compile("if x > 0 { let y = 1 }")
        assert ast.__class__.__name__ == "AqlIfStmt"

    def test_for_statement(self) -> None:
        """Test parsing for loops."""
        ast = aql_compile("for key, value in x { let y = 1 }")
        assert ast.__class__.__name__ == "AqlForStmt"


class TestAqlEvaluator:
    """Tests for AQL evaluation against SysDB data."""

    def test_bgp_enabled(self) -> None:
        """Test bgpEnabled rule: asNumber != 0 && !shutdown."""
        query = 'let data = merge(`{_d}:/Sysdb/routing/bgp/config`)\ndata["asNumber"]["value"] != 0 && !data["shutdown"]'
        ast = aql_compile(query)

        sysdb_enabled: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": {"value": 65001}, "shutdown": False}}
        assert aql_evaluate(ast, sysdb_enabled)

        sysdb_disabled: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": {"value": 0}, "shutdown": False}}
        assert not aql_evaluate(ast, sysdb_disabled)

        sysdb_shutdown: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": {"value": 65001}, "shutdown": True}}
        assert not aql_evaluate(ast, sysdb_shutdown)

    def test_arbgp_multi_agent(self) -> None:
        """Test ArBgp rule: protocolAgentModel == multi-agent."""
        query = 'merge(`{_d}:/Sysdb/l3/status/protocolAgentModelStatus`)["protocolAgentModel"]["value"] == "multi-agent"'
        ast = aql_compile(query)

        sysdb_yes: dict[str, Any] = {"/Sysdb/l3/status/protocolAgentModelStatus": {"protocolAgentModel": {"value": "multi-agent"}}}
        assert aql_evaluate(ast, sysdb_yes)

        sysdb_no: dict[str, Any] = {"/Sysdb/l3/status/protocolAgentModelStatus": {"protocolAgentModel": {"value": "legacy"}}}
        assert not aql_evaluate(ast, sysdb_no)

    def test_length_check(self) -> None:
        """Test length() function for non-empty collections."""
        query = "let config = merge(`{_d}:/Sysdb/routing/bgp/config/aggregateList`)\nlength(config) > 0"
        ast = aql_compile(query)

        sysdb_has: dict[str, Any] = {"/Sysdb/routing/bgp/config/aggregateList": {"agg1": {}}}
        assert aql_evaluate(ast, sysdb_has)

        sysdb_empty: dict[str, Any] = {"/Sysdb/routing/bgp/config/aggregateList": {}}
        assert not aql_evaluate(ast, sysdb_empty)

    def test_map_where(self) -> None:
        """Test map and where filter operations."""
        query = (
            "let q = `{_d}:/Sysdb/bridging/input/config/cli/switchIntfConfig/*`\n"
            'let accessPort = q | map(merge(_value)["switchportMode"]) | where(_value["Value"] == 0)\n'
            "length(accessPort) > 0"
        )
        ast = aql_compile(query)

        sysdb_match: dict[str, Any] = {
            "/Sysdb/bridging/input/config/cli/switchIntfConfig": {"Ethernet1": {"switchportMode": {"Value": 0}}, "Ethernet2": {"switchportMode": {"Value": 1}}}
        }
        assert aql_evaluate(ast, sysdb_match)

        sysdb_no_match: dict[str, Any] = {"/Sysdb/bridging/input/config/cli/switchIntfConfig": {"Ethernet1": {"switchportMode": {"Value": 1}}}}
        assert not aql_evaluate(ast, sysdb_no_match)

    def test_boolean_field(self) -> None:
        """Test simple boolean field check."""
        query = 'merge(`{_d}:/Sysdb/dot1x/config`)["dot1xEnabled"]'
        ast = aql_compile(query)

        sysdb_yes: dict[str, Any] = {"/Sysdb/dot1x/config": {"dot1xEnabled": True}}
        assert aql_evaluate(ast, sysdb_yes)

        sysdb_no: dict[str, Any] = {"/Sysdb/dot1x/config": {"dot1xEnabled": False}}
        assert not aql_evaluate(ast, sysdb_no)

    def test_for_loop(self) -> None:
        """Test for loop evaluation."""
        query = (
            "let method = merge(`{_d}:/Sysdb/security/aaa/config/defaultLoginMethodList/method`)\n"
            "let found = false\n"
            "for key, value in method {\n"
            '    if value["value"] == "local" {\n'
            "        let found = true\n"
            "    }\n"
            "}\n"
            "found"
        )
        ast = aql_compile(query)

        sysdb_yes: dict[str, Any] = {"/Sysdb/security/aaa/config/defaultLoginMethodList/method": {"0": {"value": "local"}, "1": {"value": "group radius"}}}
        assert aql_evaluate(ast, sysdb_yes)

        sysdb_no: dict[str, Any] = {"/Sysdb/security/aaa/config/defaultLoginMethodList/method": {"0": {"value": "group radius"}}}
        assert not aql_evaluate(ast, sysdb_no)

    def test_errvl_fallback(self) -> None:
        """Test errvl error handling function."""
        query = 'errvl(merge(`{_d}:/Sysdb/nonexistent`)["missing"]["key"], 0)'
        ast = aql_compile(query)
        assert aql_evaluate(ast, {}) is False

    def test_power_operator(self) -> None:
        """Test the power operator used for signed int conversion."""
        query = "2 ^ 31 - 1"
        ast = aql_compile(query)
        from anta.bugdb.aql import AqlEvaluator

        evaluator = AqlEvaluator({})
        result = evaluator.evaluate(ast)
        assert result == 2**31 - 1

    def test_new_style_path(self) -> None:
        """Test <d>: path prefix (AQL rev 2+)."""
        query = 'merge(`<d>:/Sysdb/routing/bgp/config`)["asNumber"]["value"] != 0'
        ast = aql_compile(query)
        sysdb: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": {"value": 65001}}}
        assert aql_evaluate(ast, sysdb)

    def test_empty_path_returns_empty_dict(self) -> None:
        """Test that querying a non-existent path returns empty dict (falsy)."""
        query = "length(merge(`{_d}:/Sysdb/nonexistent/path`)) > 0"
        ast = aql_compile(query)
        assert not aql_evaluate(ast, {})

    @pytest.mark.parametrize("filename", ["AlertBase-CVP.json"])
    def test_parse_all_query_rules(self, filename: str) -> None:
        """Test that all queryRules from the real database can be parsed."""
        path = Path(filename)
        if not path.exists():
            pytest.skip(f"{filename} not found")
        with path.open() as f:
            data = json.load(f)
        all_rules = data.get("queryRules", []) + data.get("queryRulesRev", [])
        failures = []
        for rule in all_rules:
            try:
                aql_compile(rule["query"])
            except SyntaxError as e:  # noqa: PERF203
                failures.append((rule["tag"], str(e)))
        assert not failures, f"Failed to parse {len(failures)} rules: {failures[:5]}"
