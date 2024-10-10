# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Device Abstraction Module."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Literal

import asyncssh
import httpcore
from aiocache import Cache
from aiocache.plugins import HitMissRatioPlugin
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, HTTPError, TimeoutException

import asynceapi
from anta import __DEBUG__
from anta.logger import anta_log_exception, exc_to_str
from anta.models import AntaCommand

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

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
    cache : Cache | None
        In-memory cache from aiocache library for this device (None if cache is disabled).
    cache_locks : dict
        Dictionary mapping keys to asyncio locks to guarantee exclusive access to the cache if not disabled.

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
        self.cache: Cache | None = None
        self.cache_locks: defaultdict[str, asyncio.Lock] | None = None

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
        self.cache_locks = defaultdict(asyncio.Lock)

    @property
    def cache_statistics(self) -> dict[str, Any] | None:
        """Return the device cache statistics for logging purposes."""
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
        # Need to ignore pylint no-member as Cache is a proxy class and pylint is not smart enough
        # https://github.com/pylint-dev/pylint/issues/7258
        if self.cache is not None and self.cache_locks is not None and command.use_cache:
            async with self.cache_locks[command.uid]:
                cached_output = await self.cache.get(command.uid)  # pylint: disable=no-member

                if cached_output is not None:
                    logger.debug("Cache hit for %s on %s", command.command, self.name)
                    command.output = cached_output
                else:
                    await self._collect(command=command, collection_id=collection_id)
                    await self.cache.set(command.uid, command.output)  # pylint: disable=no-member
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
    """Implementation of AntaDevice for EOS using aio-eapi.

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
        enable
            Collect commands using privileged mode.
        enable_password
            Password used to gain privileged access on EOS.
        port
            eAPI port. Defaults to 80 is proto is 'http' or 443 if proto is 'https'.
        ssh_port
            SSH port.
        tags
            Tags for this device.
        timeout
            Timeout value in seconds for outgoing API calls.
        insecure
            Disable SSH Host Key validation.
        proto
            eAPI protocol. Value can be 'http' or 'https'.
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

    async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:  # noqa: C901  function is too complex - because of many required except blocks
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
        commands: list[dict[str, str | int]] = []
        if self.enable and self._enable_password is not None:
            commands.append(
                {
                    "cmd": "enable",
                    "input": str(self._enable_password),
                },
            )
        elif self.enable:
            # No password
            commands.append({"cmd": "enable"})
        commands += [{"cmd": command.command, "revision": command.revision}] if command.revision else [{"cmd": command.command}]
        try:
            response: list[dict[str, Any] | str] = await self._session.cli(
                commands=commands,
                ofmt=command.ofmt,
                version=command.version,
                req_id=f"ANTA-{collection_id}-{id(command)}" if collection_id else f"ANTA-{id(command)}",
            )  # type: ignore[assignment] # multiple commands returns a list
            # Do not keep response of 'enable' command
            command.output = response[-1]
        except asynceapi.EapiCommandError as e:
            # This block catches exceptions related to EOS issuing an error.
            command.errors = e.errors
            if command.requires_privileges:
                logger.error(
                    "Command '%s' requires privileged mode on %s. Verify user permissions and if the `enable` option is required.", command.command, self.name
                )
            if command.supported:
                logger.error("Command '%s' failed on %s: %s", command.command, self.name, e.errors[0] if len(e.errors) == 1 else e.errors)
            else:
                logger.debug("Command '%s' is not supported on '%s' (%s)", command.command, self.name, self.hw_model)
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
            if (isinstance(exc := e.__cause__, httpcore.ConnectError) and isinstance(os_error := exc.__context__, OSError)) or isinstance(os_error := e, OSError):  # pylint: disable=no-member
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
            show_version = AntaCommand(command="show version")
            await self._collect(show_version)
            if not show_version.collected:
                logger.warning("Cannot get hardware information from device %s", self.name)
            else:
                self.hw_model = show_version.json_output.get("modelName", None)
                if self.hw_model is None:
                    logger.critical("Cannot parse 'show version' returned by device %s", self.name)
                # in some cases it is possible that 'modelName' comes back empty
                # and it is nice to get a meaninfule error message
                elif self.hw_model == "":
                    logger.critical("Got an empty 'modelName' in the 'show version' returned by device %s", self.name)
        else:
            logger.warning("Could not connect to device %s: cannot open eAPI port", self.name)

        self.established = bool(self.is_online and self.hw_model)

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
