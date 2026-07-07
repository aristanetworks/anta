# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.aql — AQL interpreter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from anta.bugdb.aql import AqlEvaluator, aql_compile, aql_evaluate, aql_tokenize


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

    def test_string_with_escape(self) -> None:
        """Test double-quoted string with backslash escape."""
        tokens = aql_tokenize(r'"hello\"world"')
        assert tokens[0].type.name == "STRING"
        assert tokens[0].value == 'hello"world'

    def test_string_with_escaped_backslash(self) -> None:
        """Test double-quoted string with escaped backslash."""
        tokens = aql_tokenize(r'"path\\to"')
        assert tokens[0].type.name == "STRING"
        assert tokens[0].value == "path\\to"

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

    def test_line_continuation(self) -> None:
        """Test backslash-newline line continuation."""
        tokens = aql_tokenize("42 \\\n43")
        assert tokens[0].value == 42
        assert tokens[1].value == 43

    def test_unknown_character(self) -> None:
        """Test that unknown characters are skipped."""
        tokens = aql_tokenize("42 @ 43")
        assert len(tokens) == 3  # 42, 43, EOF

    def test_assign_operator(self) -> None:
        """Test single = is tokenized as ASSIGN."""
        tokens = aql_tokenize("x = 1")
        assert tokens[1].type.name == "ASSIGN"

    def test_not_operator(self) -> None:
        """Test ! is tokenized as NOT."""
        tokens = aql_tokenize("!x")
        assert tokens[0].type.name == "NOT"

    def test_punctuation(self) -> None:
        """Test punctuation tokens."""
        tokens = aql_tokenize("()[]{},.")
        names = [t.type.name for t in tokens[:-1]]
        assert names == ["LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "LBRACE", "RBRACE", "COMMA", "DOT"]


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

        sysdb_enabled: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": 65001, "shutdown": False}}
        assert aql_evaluate(ast, sysdb_enabled)

        sysdb_disabled: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": 0, "shutdown": False}}
        assert not aql_evaluate(ast, sysdb_disabled)

        sysdb_shutdown: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": 65001, "shutdown": True}}
        assert not aql_evaluate(ast, sysdb_shutdown)

    def test_routing_enabled(self) -> None:
        """Test routingEnabled rule: direct == true comparison without ["value"] access."""
        query = 'merge(`{_d}:/Sysdb/routing/config`)["routing"] == true'
        ast = aql_compile(query)

        assert aql_evaluate(ast, {"/Sysdb/routing/config": {"routing": True}})
        assert not aql_evaluate(ast, {"/Sysdb/routing/config": {"routing": False}})

    def test_snmp_enabled(self) -> None:
        """Test SNMPenabled rule: direct == true comparison."""
        query = 'merge(`{_d}:/Sysdb/snmp/config`)["serviceEnabled"] == true'
        ast = aql_compile(query)

        assert aql_evaluate(ast, {"/Sysdb/snmp/config": {"serviceEnabled": True}})
        assert not aql_evaluate(ast, {"/Sysdb/snmp/config": {"serviceEnabled": False}})

    def test_multicast_enabled(self) -> None:
        """Test multicastEnabled rule: truthiness check on two paths."""
        query = 'merge(`{_d}:/Sysdb/routing/hardware/status`)["multicastRoutingSupported"] && merge(`{_d}:/Sysdb/routing/multicast/vrf/config`)["routing"]'
        ast = aql_compile(query)

        sysdb_yes: dict[str, Any] = {
            "/Sysdb/routing/hardware/status": {"multicastRoutingSupported": True},
            "/Sysdb/routing/multicast/vrf/config": {"routing": True},
        }
        assert aql_evaluate(ast, sysdb_yes)

        sysdb_no: dict[str, Any] = {
            "/Sysdb/routing/hardware/status": {"multicastRoutingSupported": True},
            "/Sysdb/routing/multicast/vrf/config": {"routing": False},
        }
        assert not aql_evaluate(ast, sysdb_no)

    def test_subscript_value_identity(self) -> None:
        """Test that ["value"] on a non-dict returns the value itself."""
        query = 'merge(`{_d}:/Sysdb/test`)["attr"]["value"]'
        ast = aql_compile(query)

        evaluator = AqlEvaluator({"/Sysdb/test": {"attr": 42}})
        assert evaluator.evaluate(ast) == 42

        evaluator2 = AqlEvaluator({"/Sysdb/test": {"attr": "hello"}})
        assert evaluator2.evaluate(ast) == "hello"

    def test_arbgp_multi_agent(self) -> None:
        """Test ArBgp rule: protocolAgentModel == multi-agent."""
        query = 'merge(`{_d}:/Sysdb/l3/status/protocolAgentModelStatus`)["protocolAgentModel"]["value"] == "multi-agent"'
        ast = aql_compile(query)

        sysdb_yes: dict[str, Any] = {"/Sysdb/l3/status/protocolAgentModelStatus": {"protocolAgentModel": "multi-agent"}}
        assert aql_evaluate(ast, sysdb_yes)

        sysdb_no: dict[str, Any] = {"/Sysdb/l3/status/protocolAgentModelStatus": {"protocolAgentModel": "legacy"}}
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

        sysdb_yes: dict[str, Any] = {"/Sysdb/security/aaa/config/defaultLoginMethodList/method": {"0": "local", "1": "group radius"}}
        assert aql_evaluate(ast, sysdb_yes)

        sysdb_no: dict[str, Any] = {"/Sysdb/security/aaa/config/defaultLoginMethodList/method": {"0": "group radius"}}
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
        evaluator = AqlEvaluator({})
        result = evaluator.evaluate(ast)
        assert result == 2**31 - 1

    def test_new_style_path(self) -> None:
        """Test <d>: path prefix (AQL rev 2+)."""
        query = 'merge(`<d>:/Sysdb/routing/bgp/config`)["asNumber"]["value"] != 0'
        ast = aql_compile(query)
        sysdb: dict[str, Any] = {"/Sysdb/routing/bgp/config": {"asNumber": 65001}}
        assert aql_evaluate(ast, sysdb)

    def test_empty_path_returns_empty_dict(self) -> None:
        """Test that querying a non-existent path returns empty dict (falsy)."""
        query = "length(merge(`{_d}:/Sysdb/nonexistent/path`)) > 0"
        ast = aql_compile(query)
        assert not aql_evaluate(ast, {})


class TestAqlFunctions:
    """Tests for AQL standard library functions."""

    def test_dict_has_key(self) -> None:
        """Test dictHasKey function."""
        query = 'dictHasKey(merge(`{_d}:/Sysdb/path`), "mykey")'
        ast = aql_compile(query)
        assert aql_evaluate(ast, {"/Sysdb/path": {"mykey": 1}})
        assert not aql_evaluate(ast, {"/Sysdb/path": {"other": 1}})

    def test_dict_value(self) -> None:
        """Test dictValue function with default."""
        query = 'dictValue(merge(`{_d}:/Sysdb/path`), "missing", 42)'
        evaluator = AqlEvaluator({"/Sysdb/path": {}})
        assert evaluator.evaluate(aql_compile(query)) == 42

    def test_str_contains(self) -> None:
        """Test strContains function."""
        query = 'strContains("hello world", "world")'
        assert aql_evaluate(aql_compile(query), {})

    def test_str_has_prefix(self) -> None:
        """Test strHasPrefix function."""
        query = 'strHasPrefix("hello world", "hello")'
        assert aql_evaluate(aql_compile(query), {})
        query_no = 'strHasPrefix("hello world", "world")'
        assert not aql_evaluate(aql_compile(query_no), {})

    def test_sum_function(self) -> None:
        """Test sum function on dict."""
        query = "sum(merge(`{_d}:/Sysdb/path`))"
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": {"a": 1, "b": 2, "c": 3}})
        assert evaluator.evaluate(ast) == 6

    def test_new_dict_and_assignment(self) -> None:
        """Test newDict and subscript assignment."""
        query = 'let d = newDict()\nd["key"] = 42\nd["key"]'
        ast = aql_compile(query)
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 42

    def test_dict_keys(self) -> None:
        """Test dictKeys function."""
        query = "length(dictKeys(merge(`{_d}:/Sysdb/path`))) > 0"
        ast = aql_compile(query)
        assert aql_evaluate(ast, {"/Sysdb/path": {"a": 1, "b": 2}})
        assert not aql_evaluate(ast, {"/Sysdb/path": {}})

    def test_merge_dicts(self) -> None:
        """Test mergeDicts function."""
        query = "length(mergeDicts(merge(`{_d}:/Sysdb/path`)))"
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": {"sub1": {"a": 1}, "sub2": {"b": 2}}})
        assert evaluator.evaluate(ast) == 2

    def test_modulo_operator(self) -> None:
        """Test modulo operator."""
        query = "10 % 3"
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile(query)) == 1

    def test_division_operator(self) -> None:
        """Test division operator."""
        query = "10 / 4"
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile(query)) == 2.5

    def test_unary_minus(self) -> None:
        """Test unary minus operator."""
        query = "-42"
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile(query)) == -42

    def test_recmap_filter(self) -> None:
        """Test recmap pipe filter."""
        query = '`{_d}:/Sysdb/path` | recmap(1, _value["x"])'
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": {"a": {"x": 10}, "b": {"x": 20}}})
        result = evaluator.evaluate(ast)
        assert result == {"a": 10, "b": 20}

    def test_dict_remove(self) -> None:
        """Test dictRemove function."""
        query = 'let d = merge(`{_d}:/Sysdb/path`)\ndictRemove(d, "remove_me")\nlength(d)'
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": {"keep": 1, "remove_me": 2}})
        assert evaluator.evaluate(ast) == 1

    def test_str_cast(self) -> None:
        """Test str() typecast."""
        query = "str(42)"
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile(query)) == "42"

    def test_num_cast(self) -> None:
        """Test num() typecast."""
        query = 'num("42")'
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile(query)) == 42

    def test_string_concatenation(self) -> None:
        """Test string + string concatenation."""
        query = '"hello" + " " + "world"'
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile(query)) == "hello world"

    def test_wildcard_path_query(self) -> None:
        """Test wildcard path query expansion."""
        query = 'length(`{_d}:/Sysdb/routing/bgp/config/neighborConfig/*` | where(_value["enabled"]))'
        ast = aql_compile(query)
        sysdb: dict[str, Any] = {
            "/Sysdb/routing/bgp/config/neighborConfig/10.0.0.1": {"enabled": True},
            "/Sysdb/routing/bgp/config/neighborConfig/10.0.0.2": {"enabled": False},
        }
        evaluator = AqlEvaluator(sysdb)
        assert evaluator.evaluate(ast) == 1

    @pytest.mark.parametrize("filename", ["AlertBase-CVP.json"])
    def test_parse_all_query_rules(self, filename: str) -> None:
        """Test that all queryRules from the real database can be parsed."""
        path = Path(filename)
        if not path.exists():
            pytest.skip(f"{filename} not found")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        all_rules = data.get("queryRules", []) + data.get("queryRulesRev", [])
        failures = []
        for rule in all_rules:
            try:
                aql_compile(rule["query"])
            except SyntaxError as e:  # noqa: PERF203
                failures.append((rule["tag"], str(e)))
        assert not failures, f"Failed to parse {len(failures)} rules: {failures[:5]}"


class TestAqlEvaluatorEdgeCases:
    """Edge case tests for AQL evaluator: subscripts, operators, filters, errors."""

    def test_wildcard_fallback_to_base_dict(self) -> None:
        """Test wildcard path falls back to base dict when no children match."""
        query = "`{_d}:/Sysdb/test/*`"
        ast = aql_compile(query)
        sysdb: dict[str, Any] = {"/Sysdb/test": {"a": 1, "b": 2}}
        evaluator = AqlEvaluator(sysdb)
        result = evaluator.evaluate(ast)
        assert result == {"a": 1, "b": 2}

    def test_subscript_on_list(self) -> None:
        """Test subscript access on a list."""
        query = "let x = merge(`{_d}:/Sysdb/path`)\nx[0]"
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": [10, 20, 30]})
        assert evaluator.evaluate(ast) == 10

    def test_subscript_on_list_out_of_bounds(self) -> None:
        """Test subscript access on a list with out-of-bounds index."""
        query = "let x = merge(`{_d}:/Sysdb/path`)\nx[99]"
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": [10]})
        assert evaluator.evaluate(ast) is None

    def test_subscript_on_non_collection(self) -> None:
        """Test subscript access on a non-dict/list returns None."""
        query = 'let x = 42\nx["key"]'
        ast = aql_compile(query)
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) is None

    def test_division_by_zero(self) -> None:
        """Test division by zero returns 0."""
        ast = aql_compile("10 / 0")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 0

    def test_modulo_by_zero(self) -> None:
        """Test modulo by zero returns 0."""
        ast = aql_compile("10 % 0")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 0

    def test_unknown_function(self) -> None:
        """Test that unknown functions return None."""
        ast = aql_compile("unknownFunc(42)")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) is None

    def test_string_alias(self) -> None:
        """Test string() as alias for str()."""
        ast = aql_compile("string(42)")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == "42"

    def test_number_alias(self) -> None:
        """Test number() as alias for num()."""
        ast = aql_compile('number("42")')
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 42

    def test_unknown_filter(self) -> None:
        """Test that unknown pipe filters pass through."""
        ast = aql_compile('merge(`{_d}:/Sysdb/path`) | unknownFilter("x")')
        evaluator = AqlEvaluator({"/Sysdb/path": {"a": 1}})
        assert evaluator.evaluate(ast) == {"a": 1}

    def test_map_on_non_dict(self) -> None:
        """Test that map on non-dict returns empty dict."""
        ast = aql_compile("let x = 42\nx | map(_value)")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == {}

    def test_where_on_non_dict(self) -> None:
        """Test that where on non-dict returns empty dict."""
        ast = aql_compile("let x = 42\nx | where(_value)")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == {}

    def test_recmap_on_non_dict(self) -> None:
        """Test recmap on non-dict returns source."""
        ast = aql_compile("let x = 42\nx | recmap(1, _value)")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 42

    def test_recmap_deep(self) -> None:
        """Test recmap with depth > 1."""
        ast = aql_compile('`{_d}:/Sysdb/path` | recmap(2, _value["x"])')
        evaluator = AqlEvaluator({"/Sysdb/path": {"a": {"sub1": {"x": 10}}, "b": {"sub2": {"x": 20}}}})
        result = evaluator.evaluate(ast)
        assert result["a"] == {"sub1": 10}

    def test_for_loop_over_list(self) -> None:
        """Test for loop over a list."""
        query = "let total = 0\nfor idx, val in merge(`{_d}:/Sysdb/path`) {\n    let total = total + val\n}\ntotal"
        ast = aql_compile(query)
        evaluator = AqlEvaluator({"/Sysdb/path": [1, 2, 3]})
        assert evaluator.evaluate(ast) == 6

    def test_if_false_returns_none(self) -> None:
        """Test if with false condition returns None."""
        ast = aql_compile("if false { 42 }")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) is None

    def test_assignment_to_non_subscript(self) -> None:
        """Test assignment where target is a subscript on a dict."""
        ast = aql_compile('let d = newDict()\nd["a"] = 1\nd["b"] = 2\nd["a"] + d["b"]')
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 3


class TestAqlOperatorsAndBuiltins:  # pylint: disable=too-many-public-methods
    """Tests for AQL operators, short-circuit logic, and built-in function edge cases."""

    def test_or_short_circuit(self) -> None:
        """Test || short-circuit: first truthy wins."""
        ast = aql_compile("true || false")
        assert aql_evaluate(ast, {})

    def test_and_short_circuit(self) -> None:
        """Test && short-circuit: first falsy loses."""
        ast = aql_compile("false && true")
        assert not aql_evaluate(ast, {})

    def test_comparison_operators(self) -> None:
        """Test comparison operators."""
        assert aql_evaluate(aql_compile("5 > 3"), {})
        assert aql_evaluate(aql_compile("3 < 5"), {})
        assert aql_evaluate(aql_compile("5 >= 5"), {})
        assert aql_evaluate(aql_compile("5 <= 5"), {})
        assert not aql_evaluate(aql_compile("5 < 3"), {})

    def test_eq_ne(self) -> None:
        """Test equality and inequality."""
        assert aql_evaluate(aql_compile('"a" == "a"'), {})
        assert aql_evaluate(aql_compile('"a" != "b"'), {})

    def test_multiply(self) -> None:
        """Test multiplication."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("3 * 4")) == 12

    def test_subtract(self) -> None:
        """Test subtraction."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("10 - 3")) == 7

    def test_sum_on_list(self) -> None:
        """Test sum() on a list."""
        evaluator = AqlEvaluator({"/Sysdb/path": [1, 2, 3]})
        assert evaluator.evaluate(aql_compile("sum(merge(`{_d}:/Sysdb/path`))")) == 6

    def test_sum_on_scalar(self) -> None:
        """Test sum() on a scalar."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("sum(42)")) == 42

    def test_length_on_string(self) -> None:
        """Test length() on a string."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile('length("hello")')) == 5

    def test_length_on_non_collection(self) -> None:
        """Test length() on a non-collection returns 0."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("length(42)")) == 0

    def test_dict_keys_on_non_dict(self) -> None:
        """Test dictKeys on non-dict returns empty list."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("dictKeys(42)")) == []

    def test_dict_has_key_on_non_dict(self) -> None:
        """Test dictHasKey on non-dict returns False."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile('dictHasKey(42, "key")')) is False

    def test_merge_dicts_on_non_dict(self) -> None:
        """Test mergeDicts on non-dict returns empty dict."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("mergeDicts(42)")) == {}

    def test_dict_remove_on_non_dict(self) -> None:
        """Test dictRemove on non-dict is a no-op."""
        evaluator = AqlEvaluator({})
        evaluator.evaluate(aql_compile('dictRemove(42, "key")'))

    def test_errvl_with_fallback(self) -> None:
        """Test errvl returns fallback value on error."""
        evaluator = AqlEvaluator({})
        result = evaluator.evaluate(aql_compile("errvl(undefinedVar, 99)"))
        assert result == 99

    def test_undefined_variable_raises(self) -> None:
        """Test that accessing undefined variable raises NameError."""
        evaluator = AqlEvaluator({})
        with pytest.raises(NameError, match="Undefined variable"):
            evaluator.evaluate(aql_compile("undefinedVar + 1"))

    def test_unknown_node_type_raises(self) -> None:
        """Test that unknown node types raise TypeError."""
        evaluator = AqlEvaluator({})
        with pytest.raises(TypeError, match="No evaluator"):
            evaluator.evaluate("not_a_node")  # type: ignore[arg-type]

    def test_syntax_error_on_unexpected_token(self) -> None:
        """Test that unexpected tokens raise SyntaxError."""
        with pytest.raises(SyntaxError, match="Unexpected token"):
            aql_compile(")")

    def test_dot_access(self) -> None:
        """Test dot access on object."""
        ast = aql_compile("merge(`{_d}:/Sysdb/path`).myfield")
        evaluator = AqlEvaluator({"/Sysdb/path": {"myfield": 42}})
        assert evaluator.evaluate(ast) == 42

    def test_paren_expression(self) -> None:
        """Test parenthesized expression."""
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(aql_compile("(2 + 3) * 4")) == 20

    def test_block_returns_last(self) -> None:
        """Test block returns last expression."""
        ast = aql_compile("let a = 1\nlet b = 2\na + b")
        evaluator = AqlEvaluator({})
        assert evaluator.evaluate(ast) == 3


class TestAqlTruthyNumeric:
    """Tests for _aql_truthy and _aql_numeric helpers."""

    def test_truthy_none(self) -> None:
        """Test None is falsy."""
        from anta.bugdb.aql import _aql_truthy

        assert not _aql_truthy(None)

    def test_truthy_bool(self) -> None:
        """Test bool truthiness."""
        from anta.bugdb.aql import _aql_truthy

        val_true: bool = True
        val_false: bool = False
        assert _aql_truthy(val_true)
        assert not _aql_truthy(val_false)

    def test_truthy_number(self) -> None:
        """Test number truthiness."""
        from anta.bugdb.aql import _aql_truthy

        assert _aql_truthy(1)
        assert not _aql_truthy(0)
        assert _aql_truthy(0.1)

    def test_truthy_string(self) -> None:
        """Test string truthiness."""
        from anta.bugdb.aql import _aql_truthy

        assert _aql_truthy("hello")
        assert not _aql_truthy("")

    def test_truthy_collections(self) -> None:
        """Test collection truthiness."""
        from anta.bugdb.aql import _aql_truthy

        assert _aql_truthy({"a": 1})
        assert not _aql_truthy({})
        assert _aql_truthy([1])
        assert not _aql_truthy([])

    def test_truthy_fallback(self) -> None:
        """Test truthiness of arbitrary object."""
        from anta.bugdb.aql import _aql_truthy

        assert _aql_truthy(object())

    def test_numeric_bool(self) -> None:
        """Test bool to numeric conversion."""
        from anta.bugdb.aql import _aql_numeric

        val_true: bool = True
        val_false: bool = False
        assert _aql_numeric(val_true) == 1
        assert _aql_numeric(val_false) == 0

    def test_numeric_string_int(self) -> None:
        """Test string-to-int numeric conversion."""
        from anta.bugdb.aql import _aql_numeric

        assert _aql_numeric("42") == 42

    def test_numeric_string_float(self) -> None:
        """Test string-to-float numeric conversion."""
        from anta.bugdb.aql import _aql_numeric

        assert _aql_numeric("3.14") == 3.14

    def test_numeric_non_numeric_string(self) -> None:
        """Test non-numeric string returns 0."""
        from anta.bugdb.aql import _aql_numeric

        assert _aql_numeric("hello") == 0

    def test_numeric_none(self) -> None:
        """Test None returns 0."""
        from anta.bugdb.aql import _aql_numeric

        assert _aql_numeric(None) == 0
