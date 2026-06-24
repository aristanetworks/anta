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
from typing import Any, ClassVar, Union

logger = logging.getLogger(__name__)


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


# Lexer


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


_TWO_CHAR_OPS: dict[str, AqlTokenType] = {
    "==": AqlTokenType.EQ,
    "!=": AqlTokenType.NEQ,
    ">=": AqlTokenType.GTE,
    "<=": AqlTokenType.LTE,
    "&&": AqlTokenType.AND,
    "||": AqlTokenType.OR,
}

_SINGLE_CHAR_OPS: dict[str, AqlTokenType] = {
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


def _read_quoted_string(source: str, i: int, quote: str) -> tuple[str, int]:
    """Read a quoted string (single or double), handling backslash escapes."""
    n = len(source)
    i += 1  # skip opening quote
    start = i
    while i < n and source[i] != quote:
        if source[i] == "\\" and i + 1 < n:
            i += 2
        else:
            i += 1
    value = source[start:i]
    i += 1  # skip closing quote
    return value, i


def _read_path_query(source: str, i: int) -> tuple[AqlToken, int]:
    """Read a backtick path query with optional field filter."""
    n = len(source)
    i += 1  # skip opening backtick
    start = i
    while i < n and source[i] != "`":
        i += 1
    path = source[start:i]
    i += 1  # closing backtick
    field_filter: list[str] | None = None
    if i < n and source[i] == "{":
        field_filter, i = _parse_field_filter(source, i)
    return AqlToken(AqlTokenType.PATH_QUERY, (path, field_filter), start - 1), i


def _read_number(source: str, i: int) -> tuple[AqlToken, int]:
    """Read a numeric literal."""
    n = len(source)
    start = i
    while i < n and (source[i].isdigit() or source[i] == "."):
        i += 1
    val = source[start:i]
    return AqlToken(AqlTokenType.NUMBER, float(val) if "." in val else int(val), start), i


def _read_identifier(source: str, i: int) -> tuple[AqlToken, int]:
    """Read an identifier or keyword."""
    n = len(source)
    start = i
    while i < n and (source[i].isalnum() or source[i] == "_"):
        i += 1
    word = source[start:i]
    tt = _AQL_KEYWORDS.get(word, AqlTokenType.IDENT)
    return AqlToken(tt, word, start), i


def aql_tokenize(source: str) -> list[AqlToken]:  # noqa: C901
    """Tokenize an AQL query string."""
    tokens: list[AqlToken] = []
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]

        if ch in " \t\r\n":
            i += 1
        elif ch == "\\" and i + 1 < n and source[i + 1] == "\n":
            i += 2
        elif ch == "#":
            while i < n and source[i] != "\n":
                i += 1
        elif ch == "`":
            tok, i = _read_path_query(source, i)
            tokens.append(tok)
        elif ch in ('"', "'"):
            val, i = _read_quoted_string(source, i, ch)
            tokens.append(AqlToken(AqlTokenType.STRING, val, i - len(val) - 2))
        elif ch.isdigit():
            tok, i = _read_number(source, i)
            tokens.append(tok)
        elif i + 1 < n and source[i : i + 2] in _TWO_CHAR_OPS:
            two = source[i : i + 2]
            tokens.append(AqlToken(_TWO_CHAR_OPS[two], two, i))
            i += 2
        elif ch in _SINGLE_CHAR_OPS:
            tokens.append(AqlToken(_SINGLE_CHAR_OPS[ch], ch, i))
            i += 1
        elif ch.isalpha() or ch == "_":
            tok, i = _read_identifier(source, i)
            tokens.append(tok)
        else:
            logger.debug("Unexpected character in AQL at pos %d: %r", i, ch)
            i += 1

    tokens.append(AqlToken(AqlTokenType.EOF, None, i))
    return tokens


# AST Nodes


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


# Parser


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

    def _parse_primary(self) -> AqlNode:
        tok = self._peek()

        handler = self._PRIMARY_HANDLERS.get(tok.type)
        if handler is not None:
            return handler(self, tok)

        msg = f"Unexpected token: {tok.type} ({tok.value!r}) at pos {tok.pos}"
        raise SyntaxError(msg)

    def _parse_literal(self, tok: AqlToken) -> AqlNode:
        self._advance()
        return AqlLiteral(tok.value)

    def _parse_bool_true(self, _tok: AqlToken) -> AqlNode:
        self._advance()
        return AqlLiteral(value=True)

    def _parse_bool_false(self, _tok: AqlToken) -> AqlNode:
        self._advance()
        return AqlLiteral(value=False)

    def _parse_path_query(self, tok: AqlToken) -> AqlNode:
        self._advance()
        path, field_filter = tok.value
        return AqlPathQuery(path, field_filter)

    def _parse_paren(self, _tok: AqlToken) -> AqlNode:
        self._advance()
        expr = self._parse_expression()
        self._expect(AqlTokenType.RPAREN)
        return expr

    def _parse_ident_or_call(self, tok: AqlToken) -> AqlNode:
        self._advance()
        if self._peek().type == AqlTokenType.LPAREN:
            return self._parse_function_call_args(tok.value)
        return AqlVariable(tok.value)

    def _parse_function_call_args(self, name: str) -> AqlFunctionCall:
        self._advance()  # consume LPAREN
        args: list[AqlNode] = []
        if self._peek().type != AqlTokenType.RPAREN:
            args.append(self._parse_expression())
            while self._match(AqlTokenType.COMMA):
                args.append(self._parse_expression())
        self._expect(AqlTokenType.RPAREN)
        return AqlFunctionCall(name, args)

    _PRIMARY_HANDLERS: ClassVar[dict[AqlTokenType, Any]] = {
        AqlTokenType.NUMBER: _parse_literal,
        AqlTokenType.STRING: _parse_literal,
        AqlTokenType.BOOL_TRUE: _parse_bool_true,
        AqlTokenType.BOOL_FALSE: _parse_bool_false,
        AqlTokenType.PATH_QUERY: _parse_path_query,
        AqlTokenType.LPAREN: _parse_paren,
        AqlTokenType.IDENT: _parse_ident_or_call,
    }


# Evaluator


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
        handler = self._EVAL_DISPATCH.get(type(node))
        if handler is None:
            msg = f"No evaluator for AQL node: {type(node).__name__}"
            raise TypeError(msg)
        return handler(self, node)

    def _eval_literal(self, node: AqlLiteral) -> Any:  # noqa: ANN401
        return node.value

    def _eval_variable(self, node: AqlVariable) -> Any:  # noqa: ANN401
        if node.name in self.variables:
            return self.variables[node.name]
        msg = f"Undefined variable: {node.name}"
        raise NameError(msg)

    def _eval_path_query(self, node: AqlPathQuery) -> Any:  # noqa: ANN401
        path = re.sub(r"^\{_d\}:|^<d>:", "", node.path)
        if path.endswith("/*"):
            return self._resolve_wildcard_path(path[:-2])
        return self.sysdb_data.get(path, {})

    def _resolve_wildcard_path(self, base: str) -> dict[str, Any]:
        """Resolve a wildcard path ``base/*`` against sysdb_data."""
        prefix = base + "/"
        result = {key[len(prefix) :]: value for key, value in self.sysdb_data.items() if key.startswith(prefix) and "/" not in key[len(prefix) :]}
        if not result and base in self.sysdb_data:
            data = self.sysdb_data[base]
            if isinstance(data, dict):
                return data
        return result

    def _eval_binary_op(self, node: AqlBinaryOp) -> Any:  # noqa: ANN401
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

    def _eval_unary_op(self, node: AqlUnaryOp) -> Any:  # noqa: ANN401
        val = self.evaluate(node.operand)
        if node.op == "!":
            return not _aql_truthy(val)
        if node.op == "-":
            return -_aql_numeric(val)
        msg = f"Unknown AQL unary operator: {node.op}"
        raise ValueError(msg)

    def _eval_subscript(self, node: AqlSubscript) -> Any:  # noqa: ANN401
        obj = self.evaluate(node.obj)
        key = self.evaluate(node.key)
        if isinstance(obj, dict):
            return obj.get(key)
        if isinstance(obj, (list, tuple)) and isinstance(key, (int, float)):
            idx = int(key)
            return obj[idx] if 0 <= idx < len(obj) else None
        return None

    def _eval_function_call(self, node: AqlFunctionCall) -> Any:  # noqa: ANN401
        return self._call_function(node.name, node.args)

    def _call_function(self, name: str, arg_nodes: list[AqlNode]) -> Any:  # noqa: ANN401
        """Dispatch AQL function calls."""
        handler = self._FUNCTION_HANDLERS.get(name)
        if handler is None:
            # Handle aliases
            if name in ("str", "string"):
                handler = self._FUNCTION_HANDLERS["str"]
            elif name in ("num", "number"):
                handler = self._FUNCTION_HANDLERS["num"]
            else:
                logger.debug("Unknown AQL function: %s", name)
                return None
        return handler(self, arg_nodes)

    def _fn_merge(self, args: list[AqlNode]) -> Any:  # noqa: ANN401
        """Evaluate merge() — identity for pre-fetched SysDB data."""
        return self.evaluate(args[0]) if args else {}

    def _fn_length(self, args: list[AqlNode]) -> int:
        """Evaluate length()."""
        val = self.evaluate(args[0]) if args else []
        return len(val) if isinstance(val, (dict, list, str, tuple)) else 0

    def _fn_new_dict(self, _args: list[AqlNode]) -> dict[str, Any]:
        """Evaluate newDict()."""
        return {}

    def _fn_dict_keys(self, args: list[AqlNode]) -> list[Any]:
        """Evaluate dictKeys()."""
        val = self.evaluate(args[0]) if args else {}
        return list(val.keys()) if isinstance(val, dict) else []

    def _fn_dict_has_key(self, args: list[AqlNode]) -> bool:
        """Evaluate dictHasKey()."""
        d = self.evaluate(args[0])
        k = self.evaluate(args[1])
        return isinstance(d, dict) and k in d

    def _fn_str(self, args: list[AqlNode]) -> str:
        """Evaluate str()."""
        return str(self.evaluate(args[0])) if args else ""

    def _fn_num(self, args: list[AqlNode]) -> int | float:
        """Evaluate num()."""
        return _aql_numeric(self.evaluate(args[0])) if args else 0

    def _fn_str_contains(self, args: list[AqlNode]) -> bool:
        """Evaluate strContains()."""
        return str(self.evaluate(args[1])) in str(self.evaluate(args[0]))

    def _fn_str_has_prefix(self, args: list[AqlNode]) -> bool:
        """Evaluate strHasPrefix()."""
        return str(self.evaluate(args[0])).startswith(str(self.evaluate(args[1])))

    def _fn_sum(self, args: list[AqlNode]) -> int | float:
        """Evaluate sum()."""
        val = self.evaluate(args[0]) if args else []
        if isinstance(val, dict):
            return sum(_aql_numeric(v) for v in val.values())
        if isinstance(val, list):
            return sum(_aql_numeric(v) for v in val)
        return _aql_numeric(val)

    def _fn_errvl(self, args: list[AqlNode]) -> Any:  # noqa: ANN401
        """Evaluate errvl() — error-value fallback."""
        try:
            return self.evaluate(args[0])
        except Exception:  # noqa: BLE001
            return self.evaluate(args[1]) if len(args) > 1 else None

    def _fn_dict_remove(self, args: list[AqlNode]) -> None:
        """Evaluate dictRemove()."""
        d = self.evaluate(args[0])
        if isinstance(d, dict):
            d.pop(self.evaluate(args[1]), None)

    def _fn_dict_value(self, args: list[AqlNode]) -> Any:  # noqa: ANN401
        """Evaluate dictValue()."""
        d = self.evaluate(args[0])
        k = self.evaluate(args[1])
        default = self.evaluate(args[2]) if len(args) > 2 else None  # noqa: PLR2004
        return d.get(k, default) if isinstance(d, dict) else default

    def _fn_merge_dicts(self, args: list[AqlNode]) -> dict[str, Any]:
        """Evaluate mergeDicts()."""
        d = self.evaluate(args[0])
        if not isinstance(d, dict):
            return {}
        result: dict[str, Any] = {}
        for v in d.values():
            if isinstance(v, dict):
                result.update(v)
        return result

    _FUNCTION_HANDLERS: ClassVar[dict[str, Any]] = {
        "merge": _fn_merge,
        "length": _fn_length,
        "newDict": _fn_new_dict,
        "dictKeys": _fn_dict_keys,
        "dictHasKey": _fn_dict_has_key,
        "str": _fn_str,
        "num": _fn_num,
        "strContains": _fn_str_contains,
        "strHasPrefix": _fn_str_has_prefix,
        "sum": _fn_sum,
        "errvl": _fn_errvl,
        "dictRemove": _fn_dict_remove,
        "dictValue": _fn_dict_value,
        "mergeDicts": _fn_merge_dicts,
    }

    def _eval_pipe_filter(self, node: AqlPipeFilter) -> Any:  # noqa: ANN401
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

    def _eval_let_stmt(self, node: AqlLetStmt) -> Any:  # noqa: ANN401
        val = self.evaluate(node.value)
        self.variables[node.name] = val
        return val

    def _eval_assignment(self, node: AqlAssignment) -> Any:  # noqa: ANN401
        val = self.evaluate(node.value)
        if isinstance(node.target, AqlSubscript):
            obj = self.evaluate(node.target.obj)
            key = self.evaluate(node.target.key)
            if isinstance(obj, dict):
                obj[key] = val
        return val

    def _eval_if_stmt(self, node: AqlIfStmt) -> Any:  # noqa: ANN401
        if _aql_truthy(self.evaluate(node.condition)):
            result = None
            for stmt in node.body:
                result = self.evaluate(stmt)
            return result
        return None

    def _eval_for_stmt(self, node: AqlForStmt) -> Any:  # noqa: ANN401
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

    def _eval_block(self, node: AqlBlock) -> Any:  # noqa: ANN401
        result = None
        for stmt in node.statements:
            result = self.evaluate(stmt)
        return result

    _EVAL_DISPATCH: ClassVar[dict[type, Any]] = {
        AqlLiteral: _eval_literal,
        AqlVariable: _eval_variable,
        AqlPathQuery: _eval_path_query,
        AqlBinaryOp: _eval_binary_op,
        AqlUnaryOp: _eval_unary_op,
        AqlSubscript: _eval_subscript,
        AqlFunctionCall: _eval_function_call,
        AqlPipeFilter: _eval_pipe_filter,
        AqlLetStmt: _eval_let_stmt,
        AqlAssignment: _eval_assignment,
        AqlIfStmt: _eval_if_stmt,
        AqlForStmt: _eval_for_stmt,
        AqlBlock: _eval_block,
    }

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


# Helpers


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


# Public API


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
