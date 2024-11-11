# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Type definitions used for the asynceapi package."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

EapiJsonOutput = dict[str, Any]
"""Type definition of an eAPI JSON output response."""
EapiTextOutput = str
"""Type definition of an eAPI text output response."""
EapiSimpleCommand = str
"""Type definition of an eAPI simple command."""


class EapiComplexCommand(TypedDict):
    """Type definition of an eAPI complex command."""

    cmd: str
    input: NotRequired[str]
    revision: NotRequired[int]


class JsonRpc(TypedDict):
    """Type definition of a JSON-RPC payload."""

    jsonrpc: Literal["2.0"]
    method: Literal["runCmds"]
    params: JsonRpcParams
    id: NotRequired[int | str]


class JsonRpcParams(TypedDict):
    """Type definition of JSON-RPC parameters."""

    version: NotRequired[int | Literal["latest"]]
    cmds: list[EapiSimpleCommand | EapiComplexCommand]
    format: NotRequired[Literal["json", "text"]]
    autoComplete: NotRequired[bool]
    expandAliases: NotRequired[bool]
    stopOnError: NotRequired[bool]
