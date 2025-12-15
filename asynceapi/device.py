# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# Initially written by Jeremy Schulman at https://github.com/jeremyschulman/aio-eapi
"""asynceapi.Device definition."""
# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from socket import getservbyname
from typing import TYPE_CHECKING, Any, Literal, overload

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------
import httpx
from typing_extensions import deprecated

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------
from ._constants import EapiCommandFormat
from .aio_portcheck import port_check_url
from .config_session import SessionConfig
from .errors import EapiCommandError

if TYPE_CHECKING:
    from ._types import EapiComplexCommand, EapiJsonOutput, EapiSimpleCommand, EapiTextOutput, JsonRpc

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------


__all__ = ["Device"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class Device(httpx.AsyncClient):
    """Represent the async JSON-RPC client that communicates with an Arista EOS device.

    This class inherits directly from the
    httpx.AsyncClient, so any initialization options can be passed directly.
    """

    EAPI_COMMAND_API_URL = "/command-api"
    EAPI_OFMT_OPTIONS = ("json", "text")
    EAPI_DEFAULT_OFMT = "json"

    def __init__(
        self,
        host: str | None = None,
        username: str | None = None,
        password: str | None = None,
        proto: str = "https",
        port: str | int | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize the Device class.

        As a subclass to httpx.AsyncClient, the caller can provide any of those initializers.
        Specific parameters for Device class are all optional and described below.

        Parameters
        ----------
        host
            The EOS target device, either hostname (DNS) or ipaddress.
        username
            The login user-name; requires the password parameter.
        password
            The login password; requires the username parameter.
        proto
            The protocol, http or https, to communicate eAPI with the device.
        port
            If not provided, the proto value is used to look up the associated
                  port (http=80, https=443). If provided, overrides the port used to
                  communite with the device.
        kwargs
            Other named keyword arguments, some of them are being used in the function
            cf Other Parameters section below, others are just passed as is to the httpx.AsyncClient.

        Other Parameters
        ----------------
        base_url : str
            If provided, the complete URL to the device eAPI endpoint.

        auth :
            If provided, used as the httpx authorization initializer value. If
            not provided, then username+password is assumed by the Caller and
            used to create a BasicAuth instance.
        """
        self.port = port or getservbyname(proto)
        self.host = host
        kwargs.setdefault("base_url", httpx.URL(f"{proto}://{self.host}:{self.port}"))
        kwargs.setdefault("verify", False)

        auth_object = httpx.BasicAuth(username, password) if username and password else None
        kwargs.setdefault("auth", auth_object)

        super().__init__(**kwargs)
        self.headers["Content-Type"] = "application/json-rpc"

    @deprecated("This method is deprecated, use `Device.check_api_endpoint` method instead. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    async def check_connection(self) -> bool:
        """Check the target device to ensure that the eAPI port is open and accepting connections.

        It is recommended that a Caller checks the connection before involving cli commands,
        but this step is not required.

        Returns
        -------
        bool
            True when the device eAPI is accessible, False otherwise.
        """
        return await port_check_url(self.base_url)

    async def check_api_endpoint(self) -> bool:
        """Check the target device eAPI HTTP endpoint with a HEAD request.

        It is recommended that a Caller checks the connection before involving cli commands,
        but this step is not required.

        Returns
        -------
        bool
            True when the device eAPI HTTP endpoint is accessible (2xx status code),
            otherwise an HTTPStatusError exception is raised.
        """
        response = await self.head(self.EAPI_COMMAND_API_URL, timeout=5)
        response.raise_for_status()
        return True

    # Single command, JSON output, no suppression
    @overload
    async def cli(
        self,
        *,
        command: EapiSimpleCommand | EapiComplexCommand,
        commands: None = None,
        ofmt: Literal["json"] = "json",
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[False] = False,
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> EapiJsonOutput: ...

    # Multiple commands, JSON output, no suppression
    @overload
    async def cli(
        self,
        *,
        command: None = None,
        commands: list[EapiSimpleCommand | EapiComplexCommand],
        ofmt: Literal["json"] = "json",
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[False] = False,
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> list[EapiJsonOutput]: ...

    # Single command, TEXT output, no suppression
    @overload
    async def cli(
        self,
        *,
        command: EapiSimpleCommand | EapiComplexCommand,
        commands: None = None,
        ofmt: Literal["text"],
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[False] = False,
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> EapiTextOutput: ...

    # Multiple commands, TEXT output, no suppression
    @overload
    async def cli(
        self,
        *,
        command: None = None,
        commands: list[EapiSimpleCommand | EapiComplexCommand],
        ofmt: Literal["text"],
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[False] = False,
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> list[EapiTextOutput]: ...

    # Single command, JSON output, with suppression
    @overload
    async def cli(
        self,
        *,
        command: EapiSimpleCommand | EapiComplexCommand,
        commands: None = None,
        ofmt: Literal["json"] = "json",
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[True],
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> EapiJsonOutput | None: ...

    # Multiple commands, JSON output, with suppression
    @overload
    async def cli(
        self,
        *,
        command: None = None,
        commands: list[EapiSimpleCommand | EapiComplexCommand],
        ofmt: Literal["json"] = "json",
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[True],
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> list[EapiJsonOutput] | None: ...

    # Single command, TEXT output, with suppression
    @overload
    async def cli(
        self,
        *,
        command: EapiSimpleCommand | EapiComplexCommand,
        commands: None = None,
        ofmt: Literal["text"],
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[True],
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> EapiTextOutput | None: ...

    # Multiple commands, TEXT output, with suppression
    @overload
    async def cli(
        self,
        *,
        command: None = None,
        commands: list[EapiSimpleCommand | EapiComplexCommand],
        ofmt: Literal["text"],
        version: int | Literal["latest"] = "latest",
        suppress_error: Literal[True],
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> list[EapiTextOutput] | None: ...

    # Actual implementation
    async def cli(
        self,
        command: EapiSimpleCommand | EapiComplexCommand | None = None,
        commands: list[EapiSimpleCommand | EapiComplexCommand] | None = None,
        ofmt: Literal["json", "text"] = "json",
        version: int | Literal["latest"] = "latest",
        *,
        suppress_error: bool = False,
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> EapiJsonOutput | EapiTextOutput | list[EapiJsonOutput] | list[EapiTextOutput] | None:
        """Execute one or more CLI commands.

        Parameters
        ----------
        command
            A single command to execute; results in a single output response.
        commands
            A list of commands to execute; results in a list of output responses.
        ofmt
            Either 'json' or 'text'; indicates the output format for the CLI commands.
            eAPI defaults to 'json'.
        version
            By default the eAPI will use "version 1" for all API object models.
            This driver will, by default, always set version to "latest" so
            that the behavior matches the CLI of the device.  The caller can
            override the "latest" behavior by explicitly setting the version.
        suppress_error
            When not False, then if the execution of the command would-have
            raised an EapiCommandError, rather than raising this exception this
            routine will return the value None.

            For example, if the following command had raised
            EapiCommandError, now response would be set to None instead.

                response = dev.cli(..., suppress_error=True)
        auto_complete
            Enabled/disables the command auto-compelete feature of the eAPI. Per the
            documentation:
                Allows users to use shorthand commands in eAPI calls. With this
                parameter included a user can send 'sh ver' via eAPI to get the
                output of 'show version'.
        expand_aliases
            Enables/disables the command use of user-defined alias. Per the
            documentation:
                Allowed users to provide the expandAliases parameter to eAPI
                calls. This allows users to use aliased commands via the API.
                For example if an alias is configured as 'sv' for 'show version'
                then an API call with sv and the expandAliases parameter will
                return the output of show version.
        req_id
            A unique identifier that will be echoed back by the switch. May be a string or number.

        Returns
        -------
        dict[str, Any]
            Single command, JSON output, suppress_error=False
        list[dict[str, Any]]
            Multiple commands, JSON output, suppress_error=False
        str
            Single command, TEXT output, suppress_error=False
        list[str]
            Multiple commands, TEXT output, suppress_error=False
        dict[str, Any] | None
            Single command, JSON output, suppress_error=True
        list[dict[str, Any]] | None
            Multiple commands, JSON output, suppress_error=True
        str | None
            Single command, TEXT output, suppress_error=True
        list[str] | None
            Multiple commands, TEXT output, suppress_error=True
        """
        if not any((command, commands)):
            msg = "Required 'command' or 'commands'"
            raise RuntimeError(msg)

        jsonrpc = self._jsonrpc_command(
            commands=[command] if command else commands if commands else [],
            ofmt=ofmt,
            version=version,
            auto_complete=auto_complete,
            expand_aliases=expand_aliases,
            req_id=req_id,
        )

        try:
            res = await self.jsonrpc_exec(jsonrpc)
            return res[0] if command else res
        except EapiCommandError:
            if suppress_error:
                return None
            raise

    def _jsonrpc_command(
        self,
        commands: list[EapiSimpleCommand | EapiComplexCommand],
        ofmt: Literal["json", "text"] = "json",
        version: int | Literal["latest"] = "latest",
        *,
        auto_complete: bool = False,
        expand_aliases: bool = False,
        req_id: int | str | None = None,
    ) -> JsonRpc:
        """Create the JSON-RPC command dictionary object.

        Parameters
        ----------
        commands
            A list of commands to execute; results in a list of output responses.
        ofmt
            Either 'json' or 'text'; indicates the output format for the CLI commands.
            eAPI defaults to 'json'.
        version
            By default the eAPI will use "version 1" for all API object models.
            This driver will, by default, always set version to "latest" so
            that the behavior matches the CLI of the device.  The caller can
            override the "latest" behavior by explicitly setting the version.
        auto_complete
            Enabled/disables the command auto-compelete feature of the EAPI.  Per the
            documentation:
                Allows users to use shorthand commands in eAPI calls. With this
                parameter included a user can send 'sh ver' via eAPI to get the
                output of 'show version'.
        expand_aliases
            Enables/disables the command use of User defined alias.  Per the
            documentation:
                Allowed users to provide the expandAliases parameter to eAPI
                calls. This allows users to use aliased commands via the API.
                For example if an alias is configured as 'sv' for 'show version'
                then an API call with sv and the expandAliases parameter will
                return the output of show version.
        req_id
            A unique identifier that will be echoed back by the switch. May be a string or number.

        Returns
        -------
        dict[str, Any]:
            dict containing the JSON payload to run the command.

        """
        return {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": {
                "version": version,
                "cmds": commands,
                "format": EapiCommandFormat(ofmt),
                "autoComplete": auto_complete,
                "expandAliases": expand_aliases,
            },
            "id": req_id or id(self),
        }

    async def jsonrpc_exec(self, jsonrpc: JsonRpc) -> list[EapiJsonOutput] | list[EapiTextOutput]:
        """Execute the JSON-RPC dictionary object.

        Parameters
        ----------
        jsonrpc
            The JSON-RPC as created by the `meth`:_jsonrpc_command().

        Raises
        ------
        EapiCommandError
            In the event that a command resulted in an error response.

        Returns
        -------
        list[dict[str, Any] | str]
            The list of command results; either dict or text depending on the
            JSON-RPC format parameter.
        """
        res = await self.post(self.EAPI_COMMAND_API_URL, json=jsonrpc)
        res.raise_for_status()
        body = res.json()

        commands = jsonrpc["params"]["cmds"]
        ofmt = jsonrpc["params"].get("format", EapiCommandFormat.JSON)

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
        failed_cmd = commands[err_at]

        raise EapiCommandError(
            passed=[get_output(cmd_data[i]) for i in range(err_at)],
            failed=failed_cmd["cmd"] if isinstance(failed_cmd, dict) else failed_cmd,
            errors=cmd_data[err_at]["errors"],
            errmsg=err_msg,
            not_exec=commands[err_at + 1 :],
        )

    def config_session(self, name: str) -> SessionConfig:
        """Return a SessionConfig instance bound to this device with the given session name.

        Parameters
        ----------
        name
            The config-session name.

        Returns
        -------
        SessionConfig
            SessionConfig instance bound to this device with the given session name.
        """
        return SessionConfig(self, name)
