# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Device Abstraction Module."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import Lock
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

import asyncssh
import httpcore
from aiocache import Cache
from aiocache.plugins import HitMissRatioPlugin
from asynceapi import Device, EapiCommandError
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, HTTPError, Limits, TimeoutException
from typing_extensions import Self

from anta import __DEBUG__
from anta.logger import anta_log_exception, exc_to_str
from anta.models import AntaCommand

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path
    from types import TracebackType
    from anta.models import AntaTest

logger = logging.getLogger(__name__)

# Do not load the default keypairs multiple times due to a performance issue introduced in cryptography 37.0
# https://github.com/pyca/cryptography/issues/7236#issuecomment-1131908472
CLIENT_KEYS = asyncssh.public_key.load_default_keypairs()


class AntaDevice(ABC):
    """Abstract class representing a device in ANTA.

    An implementation of this class must override the abstract coroutines `_collect()` and
    `refresh()`.

    Attributes
    ----------
        name: Device name
        is_online: True if the device IP is reachable and a port can be open.
        established: True if remote command execution succeeds.
        hw_model: Hardware model of the device.
        tags: Tags for this device.
        cache: In-memory cache from aiocache library for this device (None if cache is disabled).
        cache_locks: Dictionary mapping keys to asyncio locks to guarantee exclusive access to the cache if not disabled.

    """

    def __init__(self, name: str, tags: set[str] | None = None, *, disable_cache: bool = False) -> None:
        """Initialize an AntaDevice.

        Args:
        ----
            name: Device name.
            tags: Tags for this device.
            disable_cache: Disable caching for all commands for this device.

        """
        self.name: str = name
        self.hw_model: str | None = None
        self.tags: set[str] = tags if tags is not None else set()
        # A device always has its own name as tag
        self.tags.add(self.name)
        self.is_online: bool = False
        self.established: bool = False
        self.cache: Cache | None = None
        self.cache_locks: defaultdict[str, Lock] | None = None

        # Initialize cache if not disabled
        if not disable_cache:
            self._init_cache()

    @property
    @abstractmethod
    def _keys(self) -> tuple[Any, ...]:
        """Read-only property to implement hashing and equality for AntaDevice classes."""

    def __eq__(self, other: object) -> bool:
        """Implement equality for AntaDevice objects."""
        return self._keys == other._keys if isinstance(other, self.__class__) else False

    def __hash__(self) -> int:
        """Implement hashing for AntaDevice objects."""
        return hash(self._keys)

    def _init_cache(self) -> None:
        """Initialize cache for the device, can be overridden by subclasses to manipulate how it works."""
        self.cache = Cache(cache_class=Cache.MEMORY, ttl=60, namespace=self.name, plugins=[HitMissRatioPlugin()])
        self.cache_locks = defaultdict(Lock)

    @property
    def cache_statistics(self) -> dict[str, Any] | None:
        """Returns the device cache statistics for logging purposes."""
        # Need to ignore pylint no-member as Cache is a proxy class and pylint is not smart enough
        # https://github.com/pylint-dev/pylint/issues/7258
        if self.cache is not None:
            stats = getattr(self.cache, "hit_miss_ratio", {"total": 0, "hits": 0, "hit_ratio": 0})
            return {"total_commands_sent": stats["total"], "cache_hits": stats["hits"], "cache_hit_ratio": f"{stats['hit_ratio'] * 100:.2f}%"}
        return None

    def __rich_repr__(self) -> Iterator[tuple[str, Any]]:
        """Implement Rich Repr Protocol.

        https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol.
        """
        yield "name", self.name
        yield "tags", self.tags
        yield "hw_model", self.hw_model
        yield "is_online", self.is_online
        yield "established", self.established
        yield "disable_cache", self.cache is None

    @abstractmethod
    async def _collect(self, anta_commands: list[AntaCommand], *, req_format: Literal["json", "text"] = "json", req_id: str | None = None) -> None:
        """Collect device command output.

        This abstract coroutine can be used to implement any command collection method
        for a device in ANTA.

        The `_collect()` implementation needs to populate the `output` attribute
        of the `AntaCommand` object passed as argument.

        If a failure occurs, the `_collect()` implementation is expected to catch the
        exception and implement proper logging, the `output` attribute of the
        `AntaCommand` object passed as argument would be `None` in this case.

        Args:
        ----
            command: The command to collect.
            collection_id: An identifier used to build the eAPI request ID.
        """

    async def collect_commands(self, anta_commands: list[AntaCommand], *, req_format: Literal["text", "json"] = "json", req_id: str) -> None:
        """Collect multiple commands.

        Args:
        ----
            commands: The commands to collect.
            collection_id: An identifier used to build the eAPI request ID.
        """
        # FIXME: Avoid querying the cache for the initial commands that are not cached.
        commands_to_collect = []

        # FIXME: Don't loop over commands if the cache is disabled
        for command in anta_commands:
            if self.cache is not None and self.cache_locks is not None and command.use_cache:
                async with self.cache_locks[command.uid]:
                    # Need to disable pylint no-member as Cache is a proxy class and pylint is not smart enough
                    # https://github.com/pylint-dev/pylint/issues/7258
                    cached_output = await self.cache.get(command.uid)  # pylint: disable=no-member

                    if cached_output is not None:
                        logger.debug("Cache hit for %s on %s", command.command, self.name)
                        command.output = cached_output
                    else:
                        commands_to_collect.append(command)
            else:
                commands_to_collect.append(command)

        # Collect the batch of commands that are not cached
        if commands_to_collect:
            await self._collect(commands_to_collect, req_format=req_format, req_id=req_id)
            # Cache the outputs of the collected commands
            for command in commands_to_collect:
                if self.cache is not None and self.cache_locks is not None and command.use_cache:
                    async with self.cache_locks[command.uid]:
                        await self.cache.set(command.uid, command.output)  # pylint: disable=no-member

    @abstractmethod
    async def refresh(self) -> None:
        """Update attributes of an AntaDevice instance.

        This coroutine must update the following attributes of AntaDevice:
            - `is_online`: When the device IP is reachable and a port can be open
            - `established`: When a command execution succeeds
            - `hw_model`: The hardware model of the device
        """

    async def copy(self, sources: list[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """Copy files to and from the device, usually through SCP.

        It is not mandatory to implement this for a valid AntaDevice subclass.

        Args:
        ----
            sources: List of files to copy to or from the device.
            destination: Local or remote destination when copying the files. Can be a folder.
            direction: Defines if this coroutine copies files to or from the device.

        """
        _ = (sources, destination, direction)
        msg = f"copy() method has not been implemented in {self.__class__.__name__} definition"
        raise NotImplementedError(msg)


class AsyncEOSDevice(AntaDevice):
    """Implementation of AntaDevice for EOS using aio-eapi.

    Attributes
    ----------
        name: Device name
        is_online: True if the device IP is reachable and a port can be open
        established: True if remote command execution succeeds
        hw_model: Hardware model of the device
        tags: Tags for this device

    """

    # pylint: disable=R0913
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        name: str | None = None,
        enable_password: str | None = None,
        port: int | None = None,
        ssh_port: int | None = 22,
        tags: set[str] | None = None,
        timeout: float | None = None,
        proto: Literal["http", "https"] = "https",
        *,
        enable: bool = False,
        insecure: bool = False,
        disable_cache: bool = False,
    ) -> None:
        """Instantiate an AsyncEOSDevice.

        Args:
        ----
            host: Device FQDN or IP.
            username: Username to connect to eAPI and SSH.
            password: Password to connect to eAPI and SSH.
            name: Device name.
            enable: Collect commands using privileged mode.
            enable_password: Password used to gain privileged access on EOS.
            port: eAPI port. Defaults to 80 is proto is 'http' or 443 if proto is 'https'.
            ssh_port: SSH port.
            tags: Tags for this device.
            timeout: Timeout value in seconds for outgoing API calls.
            insecure: Disable SSH Host Key validation.
            proto: eAPI protocol. Value can be 'http' or 'https'.
            disable_cache: Disable caching for all commands for this device.

        """
        if host is None:
            message = "'host' is required to create an AsyncEOSDevice"
            logger.error(message)
            raise ValueError(message)
        if name is None:
            name = f"{host}{f':{port}' if port else ''}"
        super().__init__(name, tags, disable_cache=disable_cache)
        if username is None:
            message = f"'username' is required to instantiate device '{self.name}'"
            logger.error(message)
            raise ValueError(message)
        if password is None:
            message = f"'password' is required to instantiate device '{self.name}'"
            logger.error(message)
            raise ValueError(message)
        self.enable = enable
        self._enable_password = enable_password
        self._session: Device = Device(host=host, port=port, username=username, password=password, proto=proto, timeout=timeout, limits=Limits(max_connections=7))
        ssh_params: dict[str, Any] = {}
        if insecure:
            ssh_params["known_hosts"] = None
        self._ssh_opts: SSHClientConnectionOptions = SSHClientConnectionOptions(
            host=host, port=ssh_port, username=username, password=password, client_keys=CLIENT_KEYS, **ssh_params
        )

    def __rich_repr__(self) -> Iterator[tuple[str, Any]]:
        """Implement Rich Repr Protocol.

        https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol.
        """
        yield from super().__rich_repr__()
        yield ("host", self._session.host)
        yield ("eapi_port", self._session.port)
        yield ("username", self._ssh_opts.username)
        yield ("enable", self.enable)
        yield ("insecure", self._ssh_opts.known_hosts is None)
        if __DEBUG__:
            _ssh_opts = vars(self._ssh_opts).copy()
            removed_pw = "<removed>"
            _ssh_opts["password"] = removed_pw
            _ssh_opts["kwargs"]["password"] = removed_pw
            yield ("_session", vars(self._session))
            yield ("_ssh_opts", _ssh_opts)

    @property
    def _keys(self) -> tuple[Any, ...]:
        """Two AsyncEOSDevice objects are equal if the hostname and the port are the same.

        This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        return (self._session.host, self._session.port)

    async def _handle_eapi_command_error(self, exception: EapiCommandError, anta_commands: list[AntaCommand], *, req_format: str, req_id: str) -> None:
        """Handle EapiCommandError exceptions."""
        # Populate the output attribute of the AntaCommand objects with the commands that passed
        passed_outputs = exception.passed[1:] if self.enable else exception.passed
        for anta_command, output in zip(anta_commands, passed_outputs):
            anta_command.output = output

        # Populate the errors attribute of the AntaCommand object of the command that failed
        err_at = exception.err_at - 1 if self.enable else exception.err_at
        anta_command = anta_commands[err_at]
        anta_command.errors = exception.errors
        if anta_command.requires_privileges:
            logger.error(
                "Command '%s' requires privileged mode on %s. Verify user permissions and if the `enable` option is required.",
                anta_command.command,
                self.name,
            )

        if anta_command.supported:
            error_message = exception.errors[0] if len(exception.errors) == 1 else exception.errors
            logger.error(
                "Command '%s' failed on %s: %s",
                anta_command.command,
                self.name,
                error_message,
            )
        else:
            logger.error("Command '%s' is not supported on %s (%s).", anta_command.command, self.name, self.hw_model)

        # Collect the commands that were not executed
        await self._collect(anta_commands=anta_commands[err_at + 1:], req_format=req_format, req_id=req_id)

    def _handle_timeout_exception(self, exception: TimeoutException, anta_commands: list[AntaCommand]) -> None:
        """Handle TimeoutException exceptions."""
        # FIXME: Handle timeouts more gracefully
        for anta_command in anta_commands:
            anta_command.errors = [exc_to_str(exception)]

        timeouts = self._session.timeout.as_dict()
        logger.error(
            "%s occurred while sending commands to %s. Consider increasing the timeout.\nCurrent timeouts: Connect: %s | Read: %s | Write: %s | Pool: %s",
            exc_to_str(exception),
            self.name,
            timeouts["connect"],
            timeouts["read"],
            timeouts["write"],
            timeouts["pool"],
        )

    def _handle_connect_os_error(self, exception: ConnectError | OSError, anta_commands: list[AntaCommand]) -> None:
        """Handle HTTPX ConnectError and OSError exceptions."""
        # FIXME: Handle connection errors more gracefully
        for anta_command in anta_commands:
            anta_command.errors = [exc_to_str(exception)]

        if (isinstance(exc := exception.__cause__, httpcore.ConnectError) and isinstance(os_error := exc.__context__, OSError)) or isinstance(os_error := exception, OSError):
            if isinstance(os_error.__cause__, OSError):
                os_error = os_error.__cause__
            logger.error("A local OS error occurred while connecting to %s: %s.", self.name, os_error)
        else:
            anta_log_exception(exception, f"An error occurred while issuing an eAPI request to {self.name}", logger)

    def _handle_http_error(self, exception: HTTPError, anta_commands: list[AntaCommand]) -> None:
        """Handle HTTPError exceptions."""
        # FIXME: Handle HTTP errors more gracefully
        for anta_command in anta_commands:
            anta_command.errors = [exc_to_str(exception)]

        anta_log_exception(exception, f"An error occurred while issuing an eAPI request to {self.name}", logger)

    async def _collect(self, anta_commands: list[AntaCommand], *, req_format: Literal["json", "text"] = "json", req_id: str) -> None:
        """Collect device command output from EOS using aio-eapi.

        Supports outformat `json` and `text` as output structure.
        Gain privileged access using the `enable_password` attribute
        of the `AntaDevice` instance if populated.

        Args:
        ----
            command: The command to collect.
            collection_id: An identifier used to build the eAPI request ID.
        """
        commands = [
            {"cmd": anta_command.command, "revision": anta_command.revision}
            if anta_command.revision else {"cmd": anta_command.command}
            for anta_command in anta_commands
        ]

        if self.enable and self._enable_password is not None:
            commands.insert(0, {"cmd": "enable", "input": str(self._enable_password)})
        elif self.enable:
            # No password
            commands.insert(0, {"cmd": "enable"})

        try:
            response = await self._session.cli(
                commands=commands,
                ofmt=req_format,
                req_id=f"ANTA-{req_id}",
            )
            # If enable was used, exclude the first element from the response
            if self.enable:
                response = response[1:]

            # Populate the output attribute of the AntaCommand objects
            for anta_command, command_output in zip(anta_commands, response):
                anta_command.output = command_output

        except EapiCommandError as e:
            # This block catches exceptions related to EOS issuing an error.
            await self._handle_eapi_command_error(e, anta_commands, req_format=req_format, req_id=req_id)
        except TimeoutException as e:
            # This block catches exceptions related to the timeout of the request.
            self._handle_timeout_exception(e, anta_commands)
        except ConnectError as e:
            # This block catches exceptions related to the connection to the device.
            self._handle_connect_os_error(e, anta_commands)
        except HTTPError as e:
            # This block catches exceptions related to the HTTP connection.
            self._handle_http_error(e, anta_commands)

    async def refresh(self) -> None:
        """Update attributes of an AsyncEOSDevice instance.

        This coroutine must update the following attributes of AsyncEOSDevice:
        - is_online: When a device IP is reachable and a port can be open
        - established: When a command execution succeeds
        - hw_model: The hardware model of the device
        """
        logger.debug("Refreshing device %s", self.name)
        self.is_online = await self._session.check_connection()
        if self.is_online:
            show_version = AntaCommand(command="show version", revision=1)
            await self._collect([show_version], req_format="json", req_id="Refresh")
            if not show_version.collected:
                logger.warning("Cannot get hardware information from device %s", self.name)
            else:
                self.hw_model = show_version.json_output.get("modelName", None)
                if self.hw_model is None:
                    logger.critical("Cannot parse 'show version' returned by device %s", self.name)
        else:
            logger.warning("Could not connect to device %s: cannot open eAPI port", self.name)

        self.established = bool(self.is_online and self.hw_model)

    async def copy(self, sources: list[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """Copy files to and from the device using asyncssh.scp().

        Args:
        ----
            sources: List of files to copy to or from the device.
            destination: Local or remote destination when copying the files. Can be a folder.
            direction: Defines if this coroutine copies files to or from the device.

        """
        async with asyncssh.connect(
            host=self._ssh_opts.host,
            port=self._ssh_opts.port,
            tunnel=self._ssh_opts.tunnel,
            family=self._ssh_opts.family,
            local_addr=self._ssh_opts.local_addr,
            options=self._ssh_opts,
        ) as conn:
            src: list[tuple[SSHClientConnection, Path]] | list[Path]
            dst: tuple[SSHClientConnection, Path] | Path
            if direction == "from":
                src = [(conn, file) for file in sources]
                dst = destination
                for file in sources:
                    message = f"Copying '{file}' from device {self.name} to '{destination}' locally"
                    logger.info(message)

            elif direction == "to":
                src = sources
                dst = conn, destination
                for file in src:
                    message = f"Copying '{file}' to device {self.name} to '{destination}' remotely"
                    logger.info(message)

            else:
                logger.critical("'direction' argument to copy() function is invalid: %s", direction)

                return
            await asyncssh.scp(src, dst)

class RequestManager:
    """Request Manager class to handle sending requests to a device.

    # FIXME: Handle text output format
    # FIXME: Handle the case where the last batch is less than the batch size
    # FIXME: Handle different batch sizes for different tests
    # TODO: Investigate if we should transform this class into an async context manager
    # TODO: Investigate if asyncio.Condition is a better choice than asyncio.Event to signal request completion
    """

    def __init__(self, device: AntaDevice, batch_size: int) -> None:
        """
        Initialize the RequestManager object.

        Arguments:
        ----------
            device: The device object to send the requests to.
            batch_size: The maximum number of commands to send in a single request.
        """
        self.device = device
        self.batch_size = batch_size
        self.current_batch_commands = []
        self.current_batch_request_ids = set()
        self.current_batch_size = 0
        self.lock = asyncio.Lock()
        self.pending_requests: dict[str, asyncio.Event] = {}
        self.test_instances = set()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        """Exit the async context and send any remaining commands."""
        async with self.lock:
            if self.current_batch_commands:
                logger.warning("Exiting RequestManager context with pending commands")
                await self.send_eapi_request()
            else:
                logger.warning("Exiting RequestManager context with no pending commands")


    async def add_commands(self, commands: list[AntaCommand], test_instance: AntaTest) -> None:
        """Add the commands to the current batch."""
        async with self.lock:
            # Remove the test instance from the tracking set since its commands are being processed
            if test_instance in self.test_instances:
                self.test_instances.remove(test_instance)

            self.current_batch_commands.extend(commands)
            self.current_batch_size += len(commands)

            request_id = self.generate_request_id()
            self.pending_requests[request_id] = asyncio.Event()
            self.current_batch_request_ids.add(request_id)

            # Send the request if the batch size is exceeded or there are no more test instances to process
            if self.current_batch_size >= self.batch_size or not self.test_instances:
                await self.send_eapi_request()

            return request_id

    async def send_eapi_request(self) -> None:
        """Send the current batch as a request."""
        eapi_request_id = self.generate_request_id()
        logger.debug("Sending eAPI request ID: %s", eapi_request_id)

        current_batch_commands = self.current_batch_commands.copy()
        current_batch_request_ids = self.current_batch_request_ids.copy()

        task = asyncio.create_task(
            self.device.collect_commands(current_batch_commands, req_format="json", req_id=eapi_request_id),
            name=f"Request ID {eapi_request_id} on {self.device.name}",
        )
        task.add_done_callback(lambda t: self.on_request_complete(t, current_batch_request_ids))

        # Reset the current batch and its attributes
        self.current_batch_commands.clear()
        self.current_batch_request_ids.clear()
        self.current_batch_size = 0

    def on_request_complete(self, task: asyncio.Task, request_ids: set[str]) -> None:
        """Set the event when the request is complete."""
        task_name = task.get_name()
        try:
            if task.cancelled():
                logger.warning("%s was cancelled", task_name)
            elif task.exception():
                logger.error("%s failed: %s", task_name, task.exception())
            else:
                logger.debug("%s succeeded", task_name)
        except asyncio.CancelledError:
            logger.warning("%s was cancelled unexpectedly", task_name)

        for request_id in request_ids:
            self.pending_requests[request_id].set()
            del self.pending_requests[request_id]

    def generate_request_id(self) -> str:
        """Generate a unique request ID using a UUID."""
        return str(uuid4())

    async def wait_for_request(self, request_id: str) -> None:
        """Wait for a specific request to complete."""
        await self.pending_requests[request_id].wait()
