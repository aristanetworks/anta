# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Patch for aioeapi waiting for https://github.com/jeremyschulman/aio-eapi/pull/13."""
from __future__ import annotations

from typing import Any, AnyStr

import aioeapi

Device = aioeapi.Device


class EapiCommandError(RuntimeError):
    """Exception class for EAPI command errors.

    Attributes
    ----------
    failed: str - the failed command
    errmsg: str - a description of the failure reason
    errors: list[str] - the command failure details
    passed: list[dict] - a list of command results of the commands that passed
    not_exec: list[str] - a list of commands that were not executed
    """

    # pylint: disable=too-many-arguments
    def __init__(self, failed: str, errors: list[str], errmsg: str, passed: list[str | dict[str, Any]], not_exec: list[dict[str, Any]]) -> None:
        """Initializer for the EapiCommandError exception."""
        self.failed = failed
        self.errmsg = errmsg
        self.errors = errors
        self.passed = passed
        self.not_exec = not_exec
        super().__init__()

    def __str__(self) -> str:
        """Returns the error message associated with the exception."""
        return self.errmsg


aioeapi.EapiCommandError = EapiCommandError


async def jsonrpc_exec(self, jsonrpc: dict) -> list[dict | AnyStr]:  # type: ignore
    """Execute the JSON-RPC dictionary object.

    Parameters
    ----------
    jsonrpc: dict
        The JSON-RPC as created by the `meth`:jsonrpc_command().

    Raises
    ------
    EapiCommandError
        In the event that a command resulted in an error response.

    Returns
    -------
    The list of command results; either dict or text depending on the
    JSON-RPC format pameter.
    """
    res = await self.post("/command-api", json=jsonrpc)
    res.raise_for_status()
    body = res.json()

    commands = jsonrpc["params"]["cmds"]
    ofmt = jsonrpc["params"]["format"]

    get_output = (lambda _r: _r["output"]) if ofmt == "text" else (lambda _r: _r)

    # if there are no errors then return the list of command results.
    if (err_data := body.get("error")) is None:
        return [get_output(cmd_res) for cmd_res in body["result"]]

    # ---------------------------------------------------------------------
    # if we are here, then there were some command errors.  Raise a
    # EapiCommandError exception with args (commands that failed, passed,
    # not-executed).
    # ---------------------------------------------------------------------

    # -------------------------- eAPI specification ----------------------
    # On an error, no result object is present, only an error object, which
    # is guaranteed to have the following attributes: code, messages, and
    # data. Similar to the result object in the successful response, the
    # data object is a list of objects corresponding to the results of all
    # commands up to, and including, the failed command. If there was a an
    # error before any commands were executed (e.g. bad credentials), data
    # will be empty. The last object in the data array will always
    # correspond to the failed command. The command failure details are
    # always stored in the errors array.

    cmd_data = err_data["data"]
    len_data = len(cmd_data)
    err_at = len_data - 1
    err_msg = err_data["message"]

    raise EapiCommandError(
        passed=[get_output(cmd_data[cmd_i]) for cmd_i, cmd in enumerate(commands[:err_at])],
        failed=commands[err_at]["cmd"],
        errors=cmd_data[err_at]["errors"],
        errmsg=err_msg,
        not_exec=commands[err_at + 1 :],
    )


aioeapi.Device.jsonrpc_exec = jsonrpc_exec
