# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Device Abstraction Module."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from time import monotonic
from typing import TYPE_CHECKING, Any, Literal

import asyncssh
import httpcore
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, HTTPError, TimeoutException

import asynceapi
from anta import __DEBUG__
from anta.logger import anta_log_exception, exc_to_str
from anta.models import AntaCommand
from asynceapi._types import EapiComplexCommand

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from asynceapi._types import EapiSimpleCommand

logger = logging.getLogger(__name__)

# Do not load the default keypairs multiple times due to a performance issue introduced in cryptography 37.0
# https://github.com/pyca/cryptography/issues/7236#issuecomment-1131908472
CLIENT_KEYS = asyncssh.public_key.load_default_keypairs()

# Limit concurrency to 100 requests (HTTPX default) to avoid high-concurrency performance issues
# See: https://github.com/encode/httpx/issues/3215
MAX_CONCURRENT_REQUESTS = 100


class AntaCache:
    """Class to be used as cache.

    Example
    -------

    ```python
    # Create cache
    cache = AntaCache("device1")
    with cache.locks[key]:
        command_output = cache.get(key)
    ```
    """

    def __init__(self, device: str, max_size: int = 128, ttl: int = 60) -> None:
        """Initialize the cache."""
        self.device = device
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.max_size = max_size
        self.ttl = ttl

        # Stats
        self.stats: dict[str, int] = {}
        self._init_stats()

    def _init_stats(self) -> None:
        """Initialize the stats."""
        self.stats["hits"] = 0
        self.stats["total"] = 0

    async def get(self, key: str) -> Any:  # noqa: ANN401
        """Return the cached entry for key."""
        self.stats["total"] += 1
        if key in self.cache:
            timestamp, value = self.cache[key]
            if monotonic() - timestamp < self.ttl:
                # checking the value is still valid
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                return value
            # Time expired
            del self.cache[key]
            del self.locks[key]
        return None

    async def set(self, key: str, value: Any) -> bool:  # noqa: ANN401
        """Set the cached entry for key to value."""
        timestamp = monotonic()
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
        self.cache[key] = timestamp, value
        return True

    def clear(self) -> None:
        """Empty the cache."""
        logger.debug("Clearing cache for device %s", self.device)
        self.cache = OrderedDict()
        self._init_stats()


class AntaDevice(ABC):
    """Abstract class representing a device in ANTA.

    An implementation of this class must override the abstract coroutines `_collect()` and
    `refresh()`.

    Attributes
    ----------
    name : str
        Device name.
    is_online : bool
        True if the device IP is reachable and a port can be open.
    established : bool
        True if remote command execution succeeds.
    hw_model : str | None
        Hardware model of the device.
    tags : set[str]
        Tags for this device.
    cache : AntaCache | None
        In-memory cache for this device (None if cache is disabled).
    cache_locks : defaultdict[str, asyncio.Lock] | None
        Dictionary mapping keys to asyncio locks to guarantee exclusive access to the cache if not disabled.
        Deprecated, will be removed in ANTA v2.0.0, use self.cache.locks instead.
    max_connections : int | None
        For informational/logging purposes only. Can be used by the runner to verify that
        the total potential connections of a run do not exceed the system file descriptor limit.
        This does **not** affect the actual device configuration. None if not available.
    """

    def __init__(self, name: str, tags: set[str] | None = None, *, disable_cache: bool = False) -> None:
        """Initialize an AntaDevice.

        Parameters
        ----------
        name
            Device name.
        tags
            Tags for this device.
        disable_cache
            Disable caching for all commands for this device.

        """
        self.name: str = name
        self.hw_model: str | None = None
        self.tags: set[str] = tags if tags is not None else set()
        # A device always has its own name as tag
        self.tags.add(self.name)
        self.is_online: bool = False
        self.established: bool = False
        self.cache: AntaCache | None = None
        # Keeping cache_locks for backward compatibility.
        self.cache_locks: defaultdict[str, asyncio.Lock] | None = None

        # Initialize cache if not disabled
        if not disable_cache:
            self._init_cache()

    @property
    @abstractmethod
    def _keys(self) -> tuple[Any, ...]:
        """Read-only property to implement hashing and equality for AntaDevice classes."""

    @property
    def max_connections(self) -> int | None:
        """Maximum number of concurrent connections allowed by the device. Can be overridden by subclasses, returns None if not available."""
        return None

    def __eq__(self, other: object) -> bool:
        """Implement equality for AntaDevice objects."""
        return self._keys == other._keys if isinstance(other, self.__class__) else False

    def __hash__(self) -> int:
        """Implement hashing for AntaDevice objects."""
        return hash(self._keys)

    def _init_cache(self) -> None:
        """Initialize cache for the device, can be overridden by subclasses to manipulate how it works."""
        self.cache = AntaCache(device=self.name, ttl=60)
        self.cache_locks = self.cache.locks

    @property
    def cache_statistics(self) -> dict[str, Any] | None:
        """Return the device cache statistics for logging purposes."""
        if self.cache is not None:
            stats = self.cache.stats
            ratio = stats["hits"] / stats["total"] if stats["total"] > 0 else 0
            return {"total_commands_sent": stats["total"], "cache_hits": stats["hits"], "cache_hit_ratio": f"{ratio * 100:.2f}%"}
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

    def __repr__(self) -> str:
        """Return a printable representation of an AntaDevice."""
        return (
            f"AntaDevice({self.name!r}, "
            f"tags={self.tags!r}, "
            f"hw_model={self.hw_model!r}, "
            f"is_online={self.is_online!r}, "
            f"established={self.established!r}, "
            f"disable_cache={self.cache is None!r})"
        )

    @abstractmethod
    async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
        """Collect device command output.

        This abstract coroutine can be used to implement any command collection method
        for a device in ANTA.

        The `_collect()` implementation needs to populate the `output` attribute
        of the `AntaCommand` object passed as argument.

        If a failure occurs, the `_collect()` implementation is expected to catch the
        exception and implement proper logging, the `output` attribute of the
        `AntaCommand` object passed as argument would be `None` in this case.

        Parameters
        ----------
        command
            The command to collect.
        collection_id
            An identifier used to build the eAPI request ID.
        """

    async def collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
        """Collect the output for a specified command.

        When caching is activated on both the device and the command,
        this method prioritizes retrieving the output from the cache. In cases where the output isn't cached yet,
        it will be freshly collected and then stored in the cache for future access.
        The method employs asynchronous locks based on the command's UID to guarantee exclusive access to the cache.

        When caching is NOT enabled, either at the device or command level, the method directly collects the output
        via the private `_collect` method without interacting with the cache.

        Parameters
        ----------
        command
            The command to collect.
        collection_id
            An identifier used to build the eAPI request ID.
        """
        if self.cache is not None and command.use_cache:
            async with self.cache.locks[command.uid]:
                cached_output = await self.cache.get(command.uid)

                if cached_output is not None:
                    logger.debug("Cache hit for %s on %s", command.command, self.name)
                    command.output = cached_output
                else:
                    await self._collect(command=command, collection_id=collection_id)
                    await self.cache.set(command.uid, command.output)
        else:
            await self._collect(command=command, collection_id=collection_id)

    async def collect_commands(self, commands: list[AntaCommand], *, collection_id: str | None = None) -> None:
        """Collect multiple commands.

        Parameters
        ----------
        commands
            The commands to collect.
        collection_id
            An identifier used to build the eAPI request ID.
        """
        await asyncio.gather(*(self.collect(command=command, collection_id=collection_id) for command in commands))

    @abstractmethod
    async def refresh(self) -> None:
        """Update attributes of an AntaDevice instance.

        This coroutine must update the following attributes of AntaDevice:

        - `is_online`: When the device IP is reachable and a port can be open.

        - `established`: When a command execution succeeds.

        - `hw_model`: The hardware model of the device.
        """

    async def copy(self, sources: list[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """Copy files to and from the device, usually through SCP.

        It is not mandatory to implement this for a valid AntaDevice subclass.

        Parameters
        ----------
        sources
            List of files to copy to or from the device.
        destination
            Local or remote destination when copying the files. Can be a folder.
        direction
            Defines if this coroutine copies files to or from the device.

        """
        _ = (sources, destination, direction)
        msg = f"copy() method has not been implemented in {self.__class__.__name__} definition"
        raise NotImplementedError(msg)


class AsyncEOSDevice(AntaDevice):
    """Implementation of AntaDevice for EOS using the `asynceapi` library, which is built on HTTPX.

    Attributes
    ----------
    name : str
        Device name.
    is_online : bool
        True if the device IP is reachable and a port can be open.
    established : bool
        True if remote command execution succeeds.
    hw_model : str
        Hardware model of the device.
    tags : set[str]
        Tags for this device.
    """

    def __init__(  # noqa: PLR0913
        self,
        host: str,
        username: str,
        password: str,
        name: str | None = None,
        enable_password: str | None = None,
        port: int | None = None,
        ssh_port: int = 22,
        tags: set[str] | None = None,
        timeout: float | None = None,
        proto: Literal["http", "https"] = "https",
        *,
        enable: bool = False,
        insecure: bool = False,
        disable_cache: bool = False,
    ) -> None:
        """Instantiate an AsyncEOSDevice.

        Parameters
        ----------
        host
            Device FQDN or IP.
        username
            Username to connect to eAPI and SSH.
        password
            Password to connect to eAPI and SSH.
        name
            Device name.
        enable_password
            Password used to gain privileged access on EOS.
        port
            eAPI port. Defaults to 80 is proto is 'http' or 443 if proto is 'https'.
        ssh_port
            SSH port.
        tags
            Tags for this device.
        timeout
            Global timeout value in seconds for outgoing eAPI calls. None means no timeout.
        proto
            eAPI protocol. Value can be 'http' or 'https'.
        enable
            Collect commands using privileged mode.
        insecure
            Disable SSH Host Key validation.
        disable_cache
            Disable caching for all commands for this device.
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
        self._session: asynceapi.Device = asynceapi.Device(host=host, port=port, username=username, password=password, proto=proto, timeout=timeout)
        ssh_params: dict[str, Any] = {}
        if insecure:
            ssh_params["known_hosts"] = None
        self._ssh_opts: SSHClientConnectionOptions = SSHClientConnectionOptions(
            host=host, port=ssh_port, username=username, password=password, client_keys=CLIENT_KEYS, **ssh_params
        )

        self._command_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

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
            yield ("max_connections", self.max_connections) if self.max_connections is not None else ("max_connections", "N/A")

    def __repr__(self) -> str:
        """Return a printable representation of an AsyncEOSDevice."""
        return (
            f"AsyncEOSDevice({self.name!r}, "
            f"tags={self.tags!r}, "
            f"hw_model={self.hw_model!r}, "
            f"is_online={self.is_online!r}, "
            f"established={self.established!r}, "
            f"disable_cache={self.cache is None!r}, "
            f"host={self._session.host!r}, "
            f"eapi_port={self._session.port!r}, "
            f"username={self._ssh_opts.username!r}, "
            f"enable={self.enable!r}, "
            f"insecure={self._ssh_opts.known_hosts is None!r})"
        )

    @property
    def _keys(self) -> tuple[Any, ...]:
        """Two AsyncEOSDevice objects are equal if the hostname and the port are the same.

        This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        return (self._session.host, self._session.port)

    @property
    def max_connections(self) -> int | None:
        """Maximum number of concurrent connections allowed by the device. Returns None if not available."""
        try:
            return self._session._transport._pool._max_connections  # type: ignore[attr-defined]  # noqa: SLF001
        except AttributeError:
            return None

    async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
        """Collect device command output from EOS using aio-eapi.

        Supports outformat `json` and `text` as output structure.
        Gain privileged access using the `enable_password` attribute
        of the `AntaDevice` instance if populated.

        Parameters
        ----------
        command
            The command to collect.
        collection_id
            An identifier used to build the eAPI request ID.
        """
        async with self._command_semaphore:
            commands: list[EapiComplexCommand | EapiSimpleCommand] = []
            if self.enable and self._enable_password is not None:
                commands.append(
                    {
                        "cmd": "enable",
                        "input": str(self._enable_password),
                    },
                )
            elif self.enable:
                # No password
                commands.append(EapiComplexCommand(cmd="enable"))
            commands += [EapiComplexCommand(cmd=command.command, revision=command.revision)] if command.revision else [EapiComplexCommand(cmd=command.command)]
            try:
                response = await self._session.cli(
                    commands=commands,
                    ofmt=command.ofmt,
                    version=command.version,
                    req_id=f"ANTA-{collection_id}-{id(command)}" if collection_id else f"ANTA-{id(command)}",
                )
                # Do not keep response of 'enable' command
                command.output = response[-1]
            except asynceapi.EapiCommandError as e:
                # This block catches exceptions related to EOS issuing an error.
                self._handle_eapi_command_error(command, e)
            except TimeoutException as e:
                # This block catches Timeout exceptions.
                command.errors = [exc_to_str(e)]
                timeouts = self._session.timeout.as_dict()
                logger.error(
                    "%s occurred while sending a command to %s. Consider increasing the timeout.\nCurrent timeouts: Connect: %s | Read: %s | Write: %s | Pool: %s",
                    exc_to_str(e),
                    self.name,
                    timeouts["connect"],
                    timeouts["read"],
                    timeouts["write"],
                    timeouts["pool"],
                )
            except (ConnectError, OSError) as e:
                # This block catches OSError and socket issues related exceptions.
                command.errors = [exc_to_str(e)]
                # pylint: disable=no-member
                if (isinstance(exc := e.__cause__, httpcore.ConnectError) and isinstance(os_error := exc.__context__, OSError)) or isinstance(
                    os_error := e, OSError
                ):
                    if isinstance(os_error.__cause__, OSError):
                        os_error = os_error.__cause__
                    logger.error("A local OS error occurred while connecting to %s: %s.", self.name, os_error)
                else:
                    anta_log_exception(e, f"An error occurred while issuing an eAPI request to {self.name}", logger)
            except HTTPError as e:
                # This block catches most of the httpx Exceptions and logs a general message.
                command.errors = [exc_to_str(e)]
                anta_log_exception(e, f"An error occurred while issuing an eAPI request to {self.name}", logger)
            logger.debug("%s: %s", self.name, command)

    def _handle_eapi_command_error(self, command: AntaCommand, e: asynceapi.EapiCommandError) -> None:
        """Handle and appropriately log an EapiCommandError exception."""
        # Filter out empty strings from the list of errors
        error_details = [err for err in e.errors if err]

        if not error_details:
            # If e.errors is empty or just [""], fall back to e.errmsg
            # Split on the first " failed: " and keep only the reason for the failure
            cleaned_errmsg = e.errmsg.split(" failed: ", 1)[-1]
            command.errors = [cleaned_errmsg]
        else:
            command.errors = error_details

        # Join errors for cleaner logging
        error_message_str = ", ".join(command.errors)

        if command.requires_privileges:
            logger.error(
                "Command '%s' on device %s requires privileged mode. Verify user permissions and if the 'enable' option is required.",
                command.command,
                self.name,
            )
        elif not command.supported:
            logger.warning("Command '%s' on device %s is not supported on this platform (%s)", command.command, self.name, self.hw_model)
        elif command.returned_known_eos_error:
            logger.debug("Command '%s' on device %s returned a known EOS error: %s", command.command, self.name, error_message_str)
        else:
            logger.error("Command '%s' on device %s failed: %s", command.command, self.name, error_message_str)

    async def refresh(self) -> None:
        """Update attributes of an AsyncEOSDevice instance.

        This coroutine must update the following attributes of AsyncEOSDevice:
        - is_online: When a device eAPI HTTP endpoint is accessible
        - established: When a command execution succeeds
        - hw_model: The hardware model of the device
        """
        logger.debug("Refreshing device %s", self.name)
        try:
            self.is_online = await self._session.check_api_endpoint()
        except HTTPError as e:
            self.is_online = False
            self.established = False
            logger.warning("An error occurred while attempting to connect to device %s: %s", self.name, exc_to_str(e))
            return

        show_version = AntaCommand(command="show version")
        await self._collect(show_version)
        if not show_version.collected:
            self.established = False
            logger.warning("Cannot get hardware information from device %s", self.name)
            return

        self.hw_model = show_version.json_output.get("modelName", None)
        if self.hw_model is None:
            self.established = False
            logger.critical("Cannot parse 'show version' returned by device %s", self.name)
        # in some cases it is possible that 'modelName' comes back empty
        elif self.hw_model == "":
            self.established = False
            logger.critical("Got an empty 'modelName' in the 'show version' returned by device %s", self.name)
        else:
            self.established = True

    async def copy(self, sources: list[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """Copy files to and from the device using asyncssh.scp().

        Parameters
        ----------
        sources
            List of files to copy to or from the device.
        destination
            Local or remote destination when copying the files. Can be a folder.
        direction
            Defines if this coroutine copies files to or from the device.

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
