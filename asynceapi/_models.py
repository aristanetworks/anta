# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models for the asynceapi package."""

from __future__ import annotations

from dataclasses import dataclass, field
from json import JSONDecodeError, loads
from logging import getLogger
from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

from ._constants import EapiCommandFormat
from ._errors import EapiReponseError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ._types import EapiComplexCommand, EapiJsonOutput, EapiSimpleCommand, EapiTextOutput, JsonRpc

LOGGER = getLogger(__name__)


@dataclass(frozen=True)
class EapiRequest:
    """Model for an eAPI request.

    Attributes
    ----------
    commands : list[EapiSimpleCommand | EapiComplexCommand]
        A list of commands to execute.
    version : int | Literal["latest"]
        The eAPI version to use. Defaults to "latest".
    format : EapiCommandFormat
        The command output format. Defaults "json".
    timestamps : bool
        Include timestamps in the command output. Defaults to False.
    auto_complete : bool
        Enable command auto-completion. Defaults to False.
    expand_aliases : bool
        Expand command aliases. Defaults to False.
    stop_on_error : bool
        Stop command execution on first error. Defaults to True.
    id : int | str
        The request ID. Defaults to a random hex string.
    """

    commands: list[EapiSimpleCommand | EapiComplexCommand]
    version: int | Literal["latest"] = "latest"
    format: EapiCommandFormat = EapiCommandFormat.JSON
    timestamps: bool = False
    auto_complete: bool = False
    expand_aliases: bool = False
    stop_on_error: bool = True
    id: int | str = field(default_factory=lambda: uuid4().hex)

    def to_jsonrpc(self) -> JsonRpc:
        """Return the JSON-RPC dictionary payload for the request."""
        return {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": {
                "version": self.version,
                "cmds": self.commands,
                "format": self.format,
                "timestamps": self.timestamps,
                "autoComplete": self.auto_complete,
                "expandAliases": self.expand_aliases,
                "stopOnError": self.stop_on_error,
            },
            "id": self.id,
        }


@dataclass(frozen=True)
class EapiResponse:
    """Model for an eAPI response.

    Construct an EapiResponse from a JSON-RPC response dictionary using the `from_jsonrpc` class method.

    Can be iterated over to access command results in order of execution.

    Attributes
    ----------
    request_id : str
        The ID of the original request this response corresponds to.
    _results : dict[int, EapiCommandResult]
        Dictionary mapping request command indices to their respective results.
    error_code : int | None
        The JSON-RPC error code, if any.
    error_message : str | None
        The JSON-RPC error message, if any.
    """

    request_id: str
    _results: dict[int, EapiCommandResult] = field(default_factory=dict)
    error_code: int | None = None
    error_message: str | None = None

    @property
    def success(self) -> bool:
        """Return True if the response has no errors."""
        return self.error_code is None

    @property
    def results(self) -> list[EapiCommandResult]:
        """Get all results as a list. Results are ordered by the command indices in the request."""
        return list(self._results.values())

    def __len__(self) -> int:
        """Return the number of results."""
        return len(self._results)

    def __iter__(self) -> Iterator[EapiCommandResult]:
        """Enable iteration over the results. Results are yielded in the same order as provided in the request."""
        yield from self._results.values()

    @classmethod
    def from_jsonrpc(cls, response: dict[str, Any], request: EapiRequest, *, raise_on_error: bool = False) -> EapiResponse:
        """Build an EapiResponse from a JSON-RPC eAPI response.

        Parameters
        ----------
        response
            The JSON-RPC eAPI response dictionary.
        request
            The corresponding EapiRequest.
        raise_on_error
            Raise an EapiReponseError if the response contains errors, by default False.

        Returns
        -------
        EapiResponse
            The EapiResponse object.
        """
        has_error = "error" in response
        response_data = response["error"]["data"] if has_error else response["result"]

        # Handle case where we have fewer results than commands (stop_on_error=True)
        executed_count = min(len(response_data), len(request.commands))

        # Process the results we have
        results = {}
        for i in range(executed_count):
            cmd = request.commands[i]
            cmd_str = cmd["cmd"] if isinstance(cmd, dict) else cmd
            data = response_data[i]

            output = None
            errors = []
            success = True
            start_time = None
            duration = None

            # Parse the output based on the data type, no output when errors are present
            if isinstance(data, dict):
                if "errors" in data:
                    errors = data["errors"]
                    success = False
                else:
                    output = data["output"] if request.format == EapiCommandFormat.TEXT and "output" in data else data

                # Add timestamps if available
                if request.timestamps and "_meta" in data:
                    meta = data.pop("_meta")
                    start_time = meta.get("execStartTime")
                    duration = meta.get("execDuration")

            elif isinstance(data, str):
                # Handle case where eAPI returns a JSON string response (serialized JSON) for certain commands
                try:
                    output = loads(data)
                except (JSONDecodeError, TypeError):
                    # If it's not valid JSON, store as is
                    LOGGER.warning("Invalid JSON response for command: %s. Storing as text: %s", cmd_str, data)
                    output = data

            results[i] = EapiCommandResult(
                command=cmd_str,
                output=output,
                errors=errors,
                success=success,
                start_time=start_time,
                duration=duration,
            )

        # If stop_on_error is True and we have an error, indicate commands not executed
        if has_error and request.stop_on_error and executed_count < len(request.commands):
            for i in range(executed_count, len(request.commands)):
                cmd = request.commands[i]
                cmd_str = cmd["cmd"] if isinstance(cmd, dict) else cmd
                results[i] = EapiCommandResult(command=cmd_str, output=None, errors=["Command not executed due to previous error"], success=False, executed=False)

        response_obj = cls(
            request_id=response["id"],
            _results=results,
            error_code=response["error"]["code"] if has_error else None,
            error_message=response["error"]["message"] if has_error else None,
        )

        if raise_on_error and has_error:
            raise EapiReponseError(response_obj)

        return response_obj


@dataclass(frozen=True)
class EapiCommandResult:
    """Model for an eAPI command result.

    Attributes
    ----------
    command : str
        The command that was executed.
    output : EapiJsonOutput | EapiTextOutput | None
        The command result output. None if the command returned errors.
    errors : list[str]
        A list of error messages, if any.
    success : bool
        True if the command was successful.
    executed : bool
        True if the command was executed. When `stop_on_error` is True in the request, some commands may not be executed.
    start_time : float | None
        Command execution start time in seconds. Uses Unix epoch format. `timestamps` must be True in the request.
    duration : float | None
        Command execution duration in seconds. `timestamps` must be True in the request.
    """

    command: str
    output: EapiJsonOutput | EapiTextOutput | None
    errors: list[str] = field(default_factory=list)
    success: bool = True
    executed: bool = True
    start_time: float | None = None
    duration: float | None = None
