# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""AQL (Arista Query Language) interpreter for queryRules evaluation.

Implements a subset of AQL sufficient to evaluate the ``queryRules`` and ``queryRulesRev``
entries from AlertBase-CVP.json against SysDB data fetched from EOS devices.

Reference: https://aql.arista.com/index.html
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Union

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Tokens
# ──────────────────────────────────────────────────────────────────────


class AqlTokenType(Enum):
    """Token types for the AQL lexer."""

    # Literals
    NUMBER = auto()
    STRING = auto()
    PATH_QUERY = auto()
    BOOL_TRUE = auto()
    BOOL_FALSE = auto()

    # Identifiers and keywords
    IDENT = auto()
    LET = auto()
    IF = auto()
    FOR = auto()
    IN = auto()

    # Operators
    EQ = auto()
    NEQ = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PIPE = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()
    ASSIGN = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    DOT = auto()

    # Special
    EOF = auto()


@dataclass(frozen=True)
class AqlToken:
    """A single token produced by the AQL lexer."""

    type: AqlTokenType
    value: Any
    pos: int = 0


# ──────────────────────────────────────────────────────────────────────
# Lexer
# ──────────────────────────────────────────────────────────────────────

_AQL_KEYWORDS: dict[str, AqlTokenType] = {
    "let": AqlTokenType.LET,
    "if": AqlTokenType.IF,
    "for": AqlTokenType.FOR,
    "in": AqlTokenType.IN,
    "true": AqlTokenType.BOOL_TRUE,
    "false": AqlTokenType.BOOL_FALSE,
}


def _parse_field_filter(source: str, pos: int) -> tuple[list[str], int]:
    """Parse a field filter ``{"f1", "f2"}`` after a path query backtick."""
    n = len(source)
    pos += 1  # skip opening {
    fields: list[str] = []
    while pos < n and source[pos] != "}":
        if source[pos] in ('"', "'"):
            quote = source[pos]
            pos += 1
            start = pos
            while pos < n and source[pos] != quote:
                pos += 1
            fields.append(source[start:pos])
            pos += 1
        else:
            pos += 1
    pos += 1  # skip closing }
    return fields, pos


def aql_tokenize(source: str) -> list[AqlToken]:  # pylint: disable=too-many-branches,too-many-statements  # noqa: C901, PLR0912, PLR0915
    """Tokenize an AQL query string."""
    tokens: list[AqlToken] = []
    i = 0
    n = len(source)

    while i < n:
        # Whitespace and line continuations
        if source[i] in " \t\r\n":
            i += 1
            continue
        if source[i] == "\\" and i + 1 < n and source[i + 1] == "\n":
            i += 2
            continue

        # Comments
        if source[i] == "#":
            while i < n and source[i] != "\n":
                i += 1
            continue

        # Backtick path queries
        if source[i] == "`":
            i += 1
            start = i
            while i < n and source[i] != "`":
                i += 1
            path = source[start:i]
            i += 1  # closing backtick
            # Field filter: `path`{"f1", "f2"} or `path`{"f1", 'json:...'}
            field_filter: list[str] | None = None
            if i < n and source[i] == "{":
                fields, i = _parse_field_filter(source, i)
                field_filter = fields
            tokens.append(AqlToken(AqlTokenType.PATH_QUERY, (path, field_filter), start - 1))
            continue

        # String literals (double-quoted)
        if source[i] == '"':
            i += 1
            start = i
            while i < n and source[i] != '"':
                if source[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            tokens.append(AqlToken(AqlTokenType.STRING, source[start:i], start - 1))
            i += 1
            continue

        # Single-quote strings (AQL rev 5): 'str:text' or 'json:{...}'
        if source[i] == "'":
            i += 1
            start = i
            while i < n and source[i] != "'":
                if source[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            tokens.append(AqlToken(AqlTokenType.STRING, source[start:i], start - 1))
            i += 1
            continue

        # Numbers
        if source[i].isdigit():
            start = i
            while i < n and (source[i].isdigit() or source[i] == "."):
                i += 1
            val = source[start:i]
            tokens.append(AqlToken(AqlTokenType.NUMBER, float(val) if "." in val else int(val), start))
            continue

        # Two-char operators
        if i + 1 < n:
            two = source[i : i + 2]
            two_map: dict[str, AqlTokenType] = {
                "==": AqlTokenType.EQ,
                "!=": AqlTokenType.NEQ,
                ">=": AqlTokenType.GTE,
                "<=": AqlTokenType.LTE,
                "&&": AqlTokenType.AND,
                "||": AqlTokenType.OR,
            }
            if two in two_map:
                tokens.append(AqlToken(two_map[two], two, i))
                i += 2
                continue

        # Single-char operators and punctuation
        ch = source[i]
        single_map: dict[str, AqlTokenType] = {
            ">": AqlTokenType.GT,
            "<": AqlTokenType.LT,
            "!": AqlTokenType.NOT,
            "|": AqlTokenType.PIPE,
            "+": AqlTokenType.PLUS,
            "-": AqlTokenType.MINUS,
            "*": AqlTokenType.STAR,
            "/": AqlTokenType.SLASH,
            "%": AqlTokenType.PERCENT,
            "^": AqlTokenType.CARET,
            "=": AqlTokenType.ASSIGN,
            "(": AqlTokenType.LPAREN,
            ")": AqlTokenType.RPAREN,
            "[": AqlTokenType.LBRACKET,
            "]": AqlTokenType.RBRACKET,
            "{": AqlTokenType.LBRACE,
            "}": AqlTokenType.RBRACE,
            ",": AqlTokenType.COMMA,
            ".": AqlTokenType.DOT,
        }
        if ch in single_map:
            tokens.append(AqlToken(single_map[ch], ch, i))
            i += 1
            continue

        # Identifiers and keywords
        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
            word = source[start:i]
            tt = _AQL_KEYWORDS.get(word, AqlTokenType.IDENT)
            tokens.append(AqlToken(tt, word, start))
            continue

        # Unknown character
        logger.debug("Unexpected character in AQL at pos %d: %r", i, ch)
        i += 1

    tokens.append(AqlToken(AqlTokenType.EOF, None, i))
    return tokens


# ──────────────────────────────────────────────────────────────────────
# AST Nodes
# ──────────────────────────────────────────────────────────────────────

AqlNode = Union[
    "AqlLiteral",
    "AqlVariable",
    "AqlPathQuery",
    "AqlBinaryOp",
    "AqlUnaryOp",
    "AqlSubscript",
    "AqlFunctionCall",
    "AqlPipeFilter",
    "AqlLetStmt",
    "AqlIfStmt",
    "AqlForStmt",
    "AqlAssignment",
    "AqlBlock",
]


@dataclass
class AqlLiteral:
    """A literal value (number, string, bool)."""

    value: Any


@dataclass
class AqlVariable:
    """A variable reference."""

    name: str


@dataclass
class AqlPathQuery:
    r"""An AQL path query ``\`dataset:/path\```."""

    path: str
    field_filter: list[str] | None = None


@dataclass
class AqlBinaryOp:
    """Binary operation."""

    op: str
    left: AqlNode
    right: AqlNode


@dataclass
class AqlUnaryOp:
    """Unary operation."""

    op: str
    operand: AqlNode


@dataclass
class AqlSubscript:
    """Subscript access ``expr[key]``."""

    obj: AqlNode
    key: AqlNode


@dataclass
class AqlFunctionCall:
    """Function call ``func(args...)``."""

    name: str
    args: list[AqlNode]


@dataclass
class AqlPipeFilter:
    """Pipe filter: ``expr | filter(args...)``."""

    source: AqlNode
    filter_name: str
    args: list[AqlNode]


@dataclass
class AqlLetStmt:
    """Let statement: ``let name = expr``."""

    name: str
    value: AqlNode


@dataclass
class AqlAssignment:
    """Assignment to subscript: ``expr[key] = value``."""

    target: AqlNode
    value: AqlNode


@dataclass
class AqlIfStmt:
    """If statement: ``if cond { body }``."""

    condition: AqlNode
    body: list[AqlNode]


@dataclass
class AqlForStmt:
    """For loop: ``for key[, value] in expr { body }``."""

    key_var: str
    value_var: str | None
    iterable: AqlNode
    body: list[AqlNode]


@dataclass
class AqlBlock:  # pylint: disable=too-few-public-methods
    """Sequence of statements; last expression is the result."""

    statements: list[AqlNode] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Parser
# ──────────────────────────────────────────────────────────────────────


class AqlParser:  # pylint: disable=too-few-public-methods
    """Recursive descent parser for AQL."""

    def __init__(self, tokens: list[AqlToken]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> AqlToken:
        return self.tokens[self.pos]

    def _advance(self) -> AqlToken:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, tt: AqlTokenType) -> AqlToken:
        tok = self._advance()
        if tok.type != tt:
            msg = f"Expected {tt}, got {tok.type} ({tok.value!r}) at pos {tok.pos}"
            raise SyntaxError(msg)
        return tok

    def _match(self, tt: AqlTokenType) -> AqlToken | None:
        if self._peek().type == tt:
            return self._advance()
        return None

    def parse(self) -> AqlNode:
        """Parse the token stream into an AST."""
        stmts = self._parse_statements()
        if len(stmts) == 1:
            return stmts[0]
        return AqlBlock(statements=stmts)

    def _parse_statements(self) -> list[AqlNode]:
        stmts: list[AqlNode] = []
        while self._peek().type not in (AqlTokenType.EOF, AqlTokenType.RBRACE):
            stmts.append(self._parse_statement())
        return stmts

    def _parse_statement(self) -> AqlNode:
        tok = self._peek()
        if tok.type == AqlTokenType.LET:
            return self._parse_let()
        if tok.type == AqlTokenType.IF:
            return self._parse_if()
        if tok.type == AqlTokenType.FOR:
            return self._parse_for()
        return self._parse_expression()

    def _parse_let(self) -> AqlLetStmt:
        self._advance()  # consume 'let'
        name_tok = self._expect(AqlTokenType.IDENT)
        self._expect(AqlTokenType.ASSIGN)
        value = self._parse_expression()
        return AqlLetStmt(name=name_tok.value, value=value)

    def _parse_if(self) -> AqlIfStmt:
        self._advance()  # consume 'if'
        cond = self._parse_expression()
        self._expect(AqlTokenType.LBRACE)
        body = self._parse_statements()
        self._expect(AqlTokenType.RBRACE)
        return AqlIfStmt(condition=cond, body=body)

    def _parse_for(self) -> AqlForStmt:
        self._advance()  # consume 'for'
        key_tok = self._expect(AqlTokenType.IDENT)
        value_var = None
        if self._match(AqlTokenType.COMMA):
            val_tok = self._expect(AqlTokenType.IDENT)
            value_var = val_tok.value
        self._expect(AqlTokenType.IN)
        iterable = self._parse_expression()
        self._expect(AqlTokenType.LBRACE)
        body = self._parse_statements()
        self._expect(AqlTokenType.RBRACE)
        return AqlForStmt(key_var=key_tok.value, value_var=value_var, iterable=iterable, body=body)

    # ── Expression parsing with AQL precedence ──

    def _parse_expression(self) -> AqlNode:
        return self._parse_or()

    def _parse_or(self) -> AqlNode:
        left = self._parse_and()
        while self._match(AqlTokenType.OR):
            right = self._parse_and()
            left = AqlBinaryOp("||", left, right)
        return left

    def _parse_and(self) -> AqlNode:
        left = self._parse_equality()
        while self._match(AqlTokenType.AND):
            right = self._parse_equality()
            left = AqlBinaryOp("&&", left, right)
        return left

    def _parse_equality(self) -> AqlNode:
        left = self._parse_comparison()
        while self._peek().type in (AqlTokenType.EQ, AqlTokenType.NEQ):
            op = self._advance()
            right = self._parse_comparison()
            left = AqlBinaryOp(op.value, left, right)
        return left

    def _parse_comparison(self) -> AqlNode:
        left = self._parse_addition()
        while self._peek().type in (AqlTokenType.GT, AqlTokenType.LT, AqlTokenType.GTE, AqlTokenType.LTE):
            op = self._advance()
            right = self._parse_addition()
            left = AqlBinaryOp(op.value, left, right)
        return left

    def _parse_addition(self) -> AqlNode:
        left = self._parse_multiplication()
        while self._peek().type in (AqlTokenType.PLUS, AqlTokenType.MINUS):
            op = self._advance()
            right = self._parse_multiplication()
            left = AqlBinaryOp(op.value, left, right)
        return left

    def _parse_multiplication(self) -> AqlNode:
        left = self._parse_pipe()
        while self._peek().type in (AqlTokenType.STAR, AqlTokenType.SLASH, AqlTokenType.PERCENT):
            op = self._advance()
            right = self._parse_pipe()
            left = AqlBinaryOp(op.value, left, right)
        return left

    def _parse_pipe(self) -> AqlNode:
        left = self._parse_power()
        while self._peek().type == AqlTokenType.PIPE:
            self._advance()
            func_tok = self._expect(AqlTokenType.IDENT)
            self._expect(AqlTokenType.LPAREN)
            args: list[AqlNode] = []
            if self._peek().type != AqlTokenType.RPAREN:
                args.append(self._parse_expression())
                while self._match(AqlTokenType.COMMA):
                    args.append(self._parse_expression())
            self._expect(AqlTokenType.RPAREN)
            left = AqlPipeFilter(left, func_tok.value, args)
        return left

    def _parse_power(self) -> AqlNode:
        left = self._parse_unary()
        if self._peek().type == AqlTokenType.CARET:
            self._advance()
            right = self._parse_unary()
            left = AqlBinaryOp("^", left, right)
        return left

    def _parse_unary(self) -> AqlNode:
        if self._peek().type == AqlTokenType.NOT:
            self._advance()
            operand = self._parse_unary()
            return AqlUnaryOp("!", operand)
        if self._peek().type == AqlTokenType.MINUS:
            self._advance()
            operand = self._parse_unary()
            return AqlUnaryOp("-", operand)
        return self._parse_postfix()

    def _parse_postfix(self) -> AqlNode:
        node = self._parse_primary()
        while True:
            if self._peek().type == AqlTokenType.LBRACKET:
                self._advance()
                key = self._parse_expression()
                self._expect(AqlTokenType.RBRACKET)
                # Check for assignment: expr[key] = value
                if self._peek().type == AqlTokenType.ASSIGN:
                    self._advance()
                    val = self._parse_expression()
                    return AqlAssignment(target=AqlSubscript(node, key), value=val)
                node = AqlSubscript(node, key)
            elif self._peek().type == AqlTokenType.DOT:
                self._advance()
                field_tok = self._expect(AqlTokenType.IDENT)
                node = AqlSubscript(node, AqlLiteral(field_tok.value))
            else:
                break
        return node

    def _parse_primary(self) -> AqlNode:  # noqa: C901, PLR0911
        tok = self._peek()

        if tok.type == AqlTokenType.NUMBER:
            self._advance()
            return AqlLiteral(tok.value)

        if tok.type == AqlTokenType.STRING:
            self._advance()
            return AqlLiteral(tok.value)

        if tok.type == AqlTokenType.BOOL_TRUE:
            self._advance()
            return AqlLiteral(value=True)

        if tok.type == AqlTokenType.BOOL_FALSE:
            self._advance()
            return AqlLiteral(value=False)

        if tok.type == AqlTokenType.PATH_QUERY:
            self._advance()
            path, field_filter = tok.value
            return AqlPathQuery(path, field_filter)

        if tok.type == AqlTokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(AqlTokenType.RPAREN)
            return expr

        if tok.type == AqlTokenType.IDENT:
            self._advance()
            # Function call
            if self._peek().type == AqlTokenType.LPAREN:
                self._advance()
                args: list[AqlNode] = []
                if self._peek().type != AqlTokenType.RPAREN:
                    args.append(self._parse_expression())
                    while self._match(AqlTokenType.COMMA):
                        args.append(self._parse_expression())
                self._expect(AqlTokenType.RPAREN)
                return AqlFunctionCall(tok.value, args)
            return AqlVariable(tok.value)

        msg = f"Unexpected token: {tok.type} ({tok.value!r}) at pos {tok.pos}"
        raise SyntaxError(msg)


# ──────────────────────────────────────────────────────────────────────
# Evaluator
# ──────────────────────────────────────────────────────────────────────


class AqlEvaluator:  # pylint: disable=too-few-public-methods
    """Evaluate a parsed AQL AST against SysDB data.

    In the context of AlertBase queryRules, SysDB data is pre-fetched from
    the device and provided as a dict mapping paths to their values.
    AQL ``merge()`` is treated as identity since Acons returns current state.

    Parameters
    ----------
    sysdb_data
        Dict mapping SysDB paths (e.g. ``/Sysdb/routing/bgp/config``)
        to their data as returned by the device.
    """

    def __init__(self, sysdb_data: dict[str, Any]) -> None:
        self.sysdb_data = sysdb_data
        self.variables: dict[str, Any] = {}

    def evaluate(self, node: AqlNode) -> Any:  # noqa: ANN401
        """Evaluate an AQL AST node and return the result."""
        method = getattr(self, f"_eval_{type(node).__name__}", None)
        if method is None:
            msg = f"No evaluator for AQL node: {type(node).__name__}"
            raise TypeError(msg)
        return method(node)  # pylint: disable=not-callable

    def _eval_AqlLiteral(self, node: AqlLiteral) -> Any:  # noqa: ANN401, N802
        return node.value

    def _eval_AqlVariable(self, node: AqlVariable) -> Any:  # noqa: ANN401, N802
        if node.name in self.variables:
            return self.variables[node.name]
        msg = f"Undefined variable: {node.name}"
        raise NameError(msg)

    def _eval_AqlPathQuery(self, node: AqlPathQuery) -> Any:  # noqa: ANN401, N802
        path = re.sub(r"^\{_d\}:|^<d>:", "", node.path)
        if path.endswith("/*"):
            base = path[:-2]
            result = {}
            for key, value in self.sysdb_data.items():
                if key.startswith(base + "/"):
                    remainder = key[len(base) + 1 :]
                    if "/" not in remainder:
                        result[remainder] = value
            if not result and base in self.sysdb_data:
                data = self.sysdb_data[base]
                if isinstance(data, dict):
                    result = data
            return result
        return self.sysdb_data.get(path, {})

    def _eval_AqlBinaryOp(self, node: AqlBinaryOp) -> Any:  # noqa: ANN401, N802
        # Short-circuit for boolean ops
        if node.op == "&&":
            return _aql_truthy(self.evaluate(node.left)) and _aql_truthy(self.evaluate(node.right))
        if node.op == "||":
            return _aql_truthy(self.evaluate(node.left)) or _aql_truthy(self.evaluate(node.right))

        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        ops: dict[str, Any] = {
            "==": lambda: left == right,
            "!=": lambda: left != right,
            ">": lambda: _aql_numeric(left) > _aql_numeric(right),
            "<": lambda: _aql_numeric(left) < _aql_numeric(right),
            ">=": lambda: _aql_numeric(left) >= _aql_numeric(right),
            "<=": lambda: _aql_numeric(left) <= _aql_numeric(right),
            "+": lambda: (str(left) + str(right)) if isinstance(left, str) or isinstance(right, str) else _aql_numeric(left) + _aql_numeric(right),
            "-": lambda: _aql_numeric(left) - _aql_numeric(right),
            "*": lambda: _aql_numeric(left) * _aql_numeric(right),
            "/": lambda: _aql_numeric(left) / _aql_numeric(right) if _aql_numeric(right) != 0 else 0,
            "%": lambda: _aql_numeric(left) % _aql_numeric(right) if _aql_numeric(right) != 0 else 0,
            "^": lambda: _aql_numeric(left) ** _aql_numeric(right),
        }
        fn = ops.get(node.op)
        if fn is None:
            msg = f"Unknown AQL operator: {node.op}"
            raise ValueError(msg)
        return fn()

    def _eval_AqlUnaryOp(self, node: AqlUnaryOp) -> Any:  # noqa: ANN401, N802
        val = self.evaluate(node.operand)
        if node.op == "!":
            return not _aql_truthy(val)
        if node.op == "-":
            return -_aql_numeric(val)
        msg = f"Unknown AQL unary operator: {node.op}"
        raise ValueError(msg)

    def _eval_AqlSubscript(self, node: AqlSubscript) -> Any:  # noqa: ANN401, N802
        obj = self.evaluate(node.obj)
        key = self.evaluate(node.key)
        if isinstance(obj, dict):
            return obj.get(key)
        if isinstance(obj, (list, tuple)) and isinstance(key, (int, float)):
            idx = int(key)
            return obj[idx] if 0 <= idx < len(obj) else None
        return None

    def _eval_AqlFunctionCall(self, node: AqlFunctionCall) -> Any:  # noqa: ANN401, N802
        return self._call_function(node.name, node.args)

    def _call_function(self, name: str, arg_nodes: list[AqlNode]) -> Any:  # pylint: disable=too-many-return-statements,too-many-branches  # noqa: ANN401, C901, PLR0911, PLR0912
        """Dispatch AQL function calls."""
        # merge(timeseries) -> dict (identity for pre-fetched data)
        if name == "merge":
            return self.evaluate(arg_nodes[0]) if arg_nodes else {}

        if name == "length":
            val = self.evaluate(arg_nodes[0]) if arg_nodes else []
            return len(val) if isinstance(val, (dict, list, str, tuple)) else 0

        if name == "newDict":
            return {}

        if name == "dictKeys":
            val = self.evaluate(arg_nodes[0]) if arg_nodes else {}
            return list(val.keys()) if isinstance(val, dict) else []

        if name == "dictHasKey":
            d = self.evaluate(arg_nodes[0])
            k = self.evaluate(arg_nodes[1])
            return isinstance(d, dict) and k in d

        if name in ("str", "string"):
            val = self.evaluate(arg_nodes[0]) if arg_nodes else ""
            return str(val)

        if name in ("num", "number"):
            val = self.evaluate(arg_nodes[0]) if arg_nodes else 0
            return _aql_numeric(val)

        if name == "strContains":
            s = str(self.evaluate(arg_nodes[0]))
            sub = str(self.evaluate(arg_nodes[1]))
            return sub in s

        if name == "strHasPrefix":
            s = str(self.evaluate(arg_nodes[0]))
            prefix = str(self.evaluate(arg_nodes[1]))
            return s.startswith(prefix)

        if name == "sum":
            val = self.evaluate(arg_nodes[0]) if arg_nodes else []
            if isinstance(val, dict):
                return sum(_aql_numeric(v) for v in val.values())
            if isinstance(val, list):
                return sum(_aql_numeric(v) for v in val)
            return _aql_numeric(val)

        if name == "errvl":
            try:
                return self.evaluate(arg_nodes[0])
            except Exception:  # noqa: BLE001
                return self.evaluate(arg_nodes[1]) if len(arg_nodes) > 1 else None

        if name == "dictRemove":
            d = self.evaluate(arg_nodes[0])
            k = self.evaluate(arg_nodes[1])
            if isinstance(d, dict):
                d.pop(k, None)
            return None

        if name == "dictValue":
            d = self.evaluate(arg_nodes[0])
            k = self.evaluate(arg_nodes[1])
            default = self.evaluate(arg_nodes[2]) if len(arg_nodes) > 2 else None  # noqa: PLR2004
            return d.get(k, default) if isinstance(d, dict) else default

        if name == "mergeDicts":
            d = self.evaluate(arg_nodes[0])
            if isinstance(d, dict):
                result: dict[str, Any] = {}
                for v in d.values():
                    if isinstance(v, dict):
                        result.update(v)
                return result
            return {}

        logger.debug("Unknown AQL function: %s", name)
        return None

    def _eval_AqlPipeFilter(self, node: AqlPipeFilter) -> Any:  # noqa: ANN401, N802
        source = self.evaluate(node.source)
        name = node.filter_name

        if name == "map":
            return self._apply_map(source, node.args[0])
        if name == "where":
            return self._apply_where(source, node.args[0])
        if name == "recmap":
            depth = int(_aql_numeric(self.evaluate(node.args[0])))
            return self._apply_recmap(source, depth, node.args[1])

        logger.debug("Unknown AQL filter: %s", name)
        return source

    def _apply_map(self, source: Any, transform: AqlNode) -> dict[str, Any]:  # noqa: ANN401
        if not isinstance(source, dict):
            return {}
        result: dict[str, Any] = {}
        for key, value in source.items():
            with self._scoped_vars(_key=key, _value=value):
                result[key] = self.evaluate(transform)
        return result

    def _apply_where(self, source: Any, predicate: AqlNode) -> dict[str, Any]:  # noqa: ANN401
        if not isinstance(source, dict):
            return {}
        result: dict[str, Any] = {}
        for key, value in source.items():
            with self._scoped_vars(_key=key, _value=value):
                if _aql_truthy(self.evaluate(predicate)):
                    result[key] = value
        return result

    def _apply_recmap(self, source: Any, depth: int, transform: AqlNode) -> Any:  # noqa: ANN401
        if not isinstance(source, dict):
            return source
        if depth <= 1:
            return self._apply_map(source, transform)
        return {k: self._apply_recmap(v, depth - 1, transform) for k, v in source.items() if isinstance(v, dict)}

    def _eval_AqlLetStmt(self, node: AqlLetStmt) -> Any:  # noqa: ANN401, N802
        val = self.evaluate(node.value)
        self.variables[node.name] = val
        return val

    def _eval_AqlAssignment(self, node: AqlAssignment) -> Any:  # noqa: ANN401, N802
        val = self.evaluate(node.value)
        if isinstance(node.target, AqlSubscript):
            obj = self.evaluate(node.target.obj)
            key = self.evaluate(node.target.key)
            if isinstance(obj, dict):
                obj[key] = val
        return val

    def _eval_AqlIfStmt(self, node: AqlIfStmt) -> Any:  # noqa: ANN401, N802
        if _aql_truthy(self.evaluate(node.condition)):
            result = None
            for stmt in node.body:
                result = self.evaluate(stmt)
            return result
        return None

    def _eval_AqlForStmt(self, node: AqlForStmt) -> Any:  # noqa: ANN401, N802
        iterable = self.evaluate(node.iterable)
        result = None
        items: list[tuple[Any, Any]] = []
        if isinstance(iterable, dict):
            items = list(iterable.items())
        elif isinstance(iterable, list):
            items = list(enumerate(iterable))

        for key, value in items:
            self.variables[node.key_var] = key
            if node.value_var:
                self.variables[node.value_var] = value
            for stmt in node.body:
                result = self.evaluate(stmt)
        return result

    def _eval_AqlBlock(self, node: AqlBlock) -> Any:  # noqa: ANN401, N802
        result = None
        for stmt in node.statements:
            result = self.evaluate(stmt)
        return result

    def _scoped_vars(self, **kwargs: Any) -> _ScopedVars:  # noqa: ANN401
        """Create a context manager for temporarily setting AQL metavariables."""
        return _ScopedVars(self, **kwargs)


class _ScopedVars:  # pylint: disable=too-few-public-methods
    """Context manager for temporarily setting AQL metavariables."""

    def __init__(self, evaluator: AqlEvaluator, **kwargs: Any) -> None:  # noqa: ANN401
        self.evaluator = evaluator
        self.kwargs = kwargs
        self.saved: dict[str, tuple[bool, Any]] = {}

    def __enter__(self) -> None:
        for name, value in self.kwargs.items():
            had = name in self.evaluator.variables
            old = self.evaluator.variables.get(name)
            self.saved[name] = (had, old)
            self.evaluator.variables[name] = value

    def __exit__(self, *args: object) -> None:
        for name, (had, old) in self.saved.items():
            if had:
                self.evaluator.variables[name] = old
            else:
                self.evaluator.variables.pop(name, None)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _aql_truthy(value: Any) -> bool:  # noqa: ANN401
    """AQL truthiness: None, 0, empty string/dict/list are falsy."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, (dict, list)):
        return len(value) > 0
    return bool(value)


def _aql_numeric(value: Any) -> int | float:  # noqa: ANN401
    """Coerce a value to AQL num type (float64)."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return 0
    return 0


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def aql_compile(query_str: str) -> AqlNode:
    """Parse an AQL query string into an AST.

    Parameters
    ----------
    query_str
        Raw AQL query from a queryRule entry.

    Returns
    -------
    AqlNode
        Compiled AST ready for evaluation.
    """
    tokens = aql_tokenize(query_str)
    parser = AqlParser(tokens)
    return parser.parse()


def aql_evaluate(ast: AqlNode, sysdb_data: dict[str, Any]) -> bool:
    """Evaluate a compiled AQL AST against SysDB data.

    Parameters
    ----------
    ast
        Compiled AST from ``aql_compile``.
    sysdb_data
        Dict mapping SysDB paths to their fetched data.

    Returns
    -------
    bool
        True if the query result is truthy (the tag applies to the device).
    """
    evaluator = AqlEvaluator(sysdb_data)
    result = evaluator.evaluate(ast)
    return _aql_truthy(result)
