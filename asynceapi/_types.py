# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Type definitions used for the asynceapi package."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ._constants import EapiCommandFormat

if sys.version_info >= (3, 11):
    from typing import NotRequired, TypedDict
else:
    from typing_extensions import NotRequired, TypedDict

EapiJsonOutput = dict[str, Any]
"""Type definition of an eAPI JSON output response."""
EapiTextOutput = str
"""Type definition of an eAPI text output response."""
EapiSimpleCommand = str
"""Type definition of an eAPI simple command. A simple command is the CLI command to run as a string."""


class EapiComplexCommand(TypedDict):
    """Type definition of an eAPI complex command. A complex command is a dictionary with the CLI command to run with additional parameters."""

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
    format: NotRequired[EapiCommandFormat]
    autoComplete: NotRequired[bool]
    expandAliases: NotRequired[bool]
    timestamps: NotRequired[bool]
    stopOnError: NotRequired[bool]
