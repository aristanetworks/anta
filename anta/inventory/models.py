"""Models related to inventory management."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union

import asyncssh
from aioeapi import Device, EapiCommandError
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, HTTPError
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, conint, constr
from rich.pretty import pretty_repr

from anta.models import AntaTestCommand
from anta.tools.misc import exc_to_str, tb_to_str

logger = logging.getLogger(__name__)

# Default values
DEFAULT_TAG = "all"

# Pydantic models for input validation

RFC_1123_REGEX = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"


# For Python < 3.10, it is not possible to install a version of aio-eapi newer than 0.3.0
# which sadly hardcodes version to 1 in its call to eAPI
# This little piece of nasty hack patches the aio-eapi function to support using a different
# version of the eAPI.
# Hic Sunt Draconis.
# Are we proud of this? No.
# Waiting for: https://github.com/jeremyschulman/aio-eapi/issues/9
def patched_jsoncrpc_command(self: Device, commands: List[str], ofmt: str, **kwargs: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Used to create the JSON-RPC command dictionary object
    """
    version = kwargs.get("version", "latest")

    cmd = {
        "jsonrpc": "2.0",
        "method": "runCmds",
        "params": {
            "version": version,
            "cmds": commands,
            "format": ofmt or self.EAPI_DEFAULT_OFMT,
        },
        "id": str(kwargs.get("req_id") or id(self)),
    }
    if "autoComplete" in kwargs:
        cmd["params"]["autoComplete"] = kwargs["autoComplete"]  # type: ignore

    if "expandAliases" in kwargs:
        cmd["params"]["expandAliases"] = kwargs["expandAliases"]  # type: ignore

    return cmd


Device.jsoncrpc_command = patched_jsoncrpc_command


class AntaInventoryHost(BaseModel):
    """
    Host definition for user's inventory.

    Attributes:
        host (IPvAnyAddress): IPv4 or IPv6 address of the device
        port (int): (Optional) eAPI port to use Default is 443.
        name (str): (Optional) Name to display during tests report. Default is hostname:port
        tags (List[str]): List of attached tags read from inventory file.
    """

    name: Optional[str]
    host: Union[constr(regex=RFC_1123_REGEX), IPvAnyAddress]  # type: ignore
    port: Optional[conint(gt=1, lt=65535)]  # type: ignore
    tags: Optional[List[str]]


class AntaInventoryNetwork(BaseModel):
    """
    Network definition for user's inventory.

    Attributes:
        network (IPvAnyNetwork): Subnet to use for testing.
        tags (List[str]): List of attached tags read from inventory file.
    """

    network: IPvAnyNetwork
    tags: Optional[List[str]]


class AntaInventoryRange(BaseModel):
    """
    IP Range definition for user's inventory.

    Attributes:
        start (IPvAnyAddress): IPv4 or IPv6 address for the begining of the range.
        stop (IPvAnyAddress): IPv4 or IPv6 address for the end of the range.
        tags (List[str]): List of attached tags read from inventory file.
    """

    start: IPvAnyAddress
    end: IPvAnyAddress
    tags: Optional[List[str]]


class AntaInventoryInput(BaseModel):
    """
    User's inventory model.

    Attributes:
        networks (List[AntaInventoryNetwork],Optional): List of AntaInventoryNetwork objects for networks.
        hosts (List[AntaInventoryHost],Optional): List of AntaInventoryHost objects for hosts.
        range (List[AntaInventoryRange],Optional): List of AntaInventoryRange objects for ranges.
    """

    networks: Optional[List[AntaInventoryNetwork]]
    hosts: Optional[List[AntaInventoryHost]]
    ranges: Optional[List[AntaInventoryRange]]


class AntaDevice(ABC):
    """
    Abstract class representing a device in ANTA.
    An implementation of this class needs must override the abstract coroutines `collect()` and
    `refresh()`.

    Instance attributes:
        name: Device name
        is_online: True if the device IP is reachable and a port can be open
        established: True if remote command execution succeeds
        hw_model: Hardware model of the device
        tags: List of tags for this device
    """

    def __init__(self, name: str, tags: Optional[List[str]] = None) -> None:
        """
        Constructor of AntaDevice

        Args:
            name: Device name
            tags: List of tags for this device
        """
        self.name: str = name
        self.hw_model: Optional[str] = None
        self.tags: List[str] = tags if tags is not None else []
        self.is_online: bool = False
        self.established: bool = False

        # Ensure tag 'all' is always set
        if DEFAULT_TAG not in self.tags:
            self.tags.append(DEFAULT_TAG)

    # https://github.com/python/mypy/issues/6523
    if TYPE_CHECKING:
        __dict__ = {}  # type: Dict[str, Any]
    else:

        @property
        def __dict__(self) -> dict[str, Any]:
            """
            Returns a dictionary that represents the AntaDevice object.
            Can be overriden in subclasses.
            """
            return {
                "name": self.name,
                "type": self.__class__.__name__,
                "hw_model": self.hw_model,
                "tags": self.tags,
                "is_online": self.is_online,
                "established": self.established,
            }

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        AntaDevice equality depends on the class implementation.
        """

    @abstractmethod
    async def collect(self, command: AntaTestCommand) -> None:
        """
        Collect device command output.
        This abstract coroutine can be used to implement any command collection method
        for a device in ANTA.

        The `collect()` implementation needs to populate the `output` attribute
        of the `AntaTestCommand` object passed as argument.

        If a failure occurs, the `collect()` implementation is expected to catch the
        exception and implement proper logging, the `output` attribute of the
        `AntaTestCommand` object passed as argument would be `None` in this case.

        Args:
            command: the command to collect
        """

    async def collect_commands(self, commands: List[AntaTestCommand]) -> None:
        """
        Collect multiple commands.

        Args:
            commands: the commands to collect
        """
        await asyncio.gather(*(self.collect(command=command) for command in commands))

    @abstractmethod
    async def refresh(self) -> None:
        """
        Update attributes of an AntaDevice instance.

        This coroutine must update the following attributes of AntaDevice:
        - is_online: When the device IP is reachable and a port can be open
        - established: When a command execution succeeds
        - hw_model: The hardware model of the device
        """

    async def copy(self, sources: List[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """
        Copy files to and from the device, usually through SCP.
        It is not mandatory to implement this for a valid AntaDevice subclass.

        Args:
            sources: List of files to copy to or from the device.
            destination: Local or remote destination when copying the files. Can be a folder.
            direction: Defines if this coroutine copies files to or from the device.
        """
        raise NotImplementedError(f"copy() method has not been implemented in {self.__class__.__name__} definition")


class AsyncEOSDevice(AntaDevice):
    """
    Implementation of AntaDevice for EOS using aio-eapi.

    Instance attributes:
        name: Device name
        is_online: True if the device IP is reachable and a port can be open
        established: True if remote command execution succeeds
        hw_model: Hardware model of the device
        tags: List of tags for this device
    """

    # Hardware model definition in show version
    HW_MODEL_KEY: str = "modelName"
    # Maximum concurrent SSH connections opened with EOS
    MAX_SSH_CONNECTIONS: int = 10

    def __init__(  # pylint: disable=R0913
        self,
        host: str,
        username: str,
        password: str,
        name: Optional[str] = None,
        enable_password: Optional[str] = None,
        port: Optional[int] = None,
        ssh_port: Optional[int] = 22,
        tags: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        insecure: bool = False,
        proto: Literal["http", "https"] = "https",
    ) -> None:
        """
        Constructor of AsyncEOSDevice

        Args:
            host: Device FQDN or IP
            username: Username to connect to eAPI and SSH
            password: Password to connect to eAPI and SSH
            name: Device name
            enable_password: Password used to gain privileged access on EOS
            proto: eAPI protocol. Value can be 'http' or 'https'
            port: eAPI port. Defaults to 80 is proto is 'http' or 443 if proto is 'https'.
            ssh_port: SSH port
            insecure: Disable SSH Host Key validation
            tags: List of tags for this device
            timeout: Timeout value in seconds for outgoing connections. Default to 10 secs.
        """
        if name is None:
            name = f"{host}:{port}"
        super().__init__(name, tags)
        self._enable_password = enable_password
        self._session: Device = Device(host=host, port=port, username=username, password=password, proto=proto, timeout=timeout)
        ssh_params: Dict[str, Any] = {}
        if insecure:
            ssh_params.update({"known_hosts": None})
        self._ssh_opts: SSHClientConnectionOptions = SSHClientConnectionOptions(host=host, port=ssh_port, username=username, password=password, **ssh_params)
        logger.debug(pretty_repr(vars(self)))

    # https://github.com/python/mypy/issues/6523
    if TYPE_CHECKING:
        __dict__ = {}  # type: Dict[str, Any]
    else:

        @property
        def __dict__(self) -> dict[str, Any]:
            """
            Returns a dictionary that represents the AntaDevice object.
            Can be overriden in subclasses.
            """
            return {
                "name": self.name,
                "type": self.__class__.__name__,
                "hw_model": self.hw_model,
                "tags": self.tags,
                "is_online": self.is_online,
                "established": self.established,
                "session": vars(self._session),
                "ssh_options": vars(self._ssh_opts),
            }

    def __eq__(self, other: object) -> bool:
        """
        Two AsyncEOSDevice objects are equal if the hostname and the port are the same.
        This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        if not isinstance(other, AsyncEOSDevice):
            return False
        return self._session.host == other._session.host and self._session.port == other._session.port

    async def collect(self, command: AntaTestCommand) -> None:
        """
        Collect device command output from EOS using aio-eapi.

        Supports outformat `json` and `text` as output structure.
        Gain privileged access using the `enable_password` attribute
        of the `AntaDevice` instance if populated.

        Args:
            command: the command to collect
        """
        try:
            if self._enable_password is not None:
                enable_cmd = {
                    "cmd": "enable",
                    "input": str(self._enable_password),
                }
            else:
                enable_cmd = {"cmd": "enable"}
            response = await self._session.cli(
                commands=[enable_cmd, command.command],
                ofmt=command.ofmt,
                version=command.version,
            )
            # remove first dict related to enable command
            # only applicable to json output
            if command.ofmt in ["json", "text"]:
                # selecting only our command output
                response = response[1]
            command.output = response
            logger.debug(f"{self.name}: {command}")

        except EapiCommandError as e:
            logger.error(f"Command '{command.command}' failed on {self.name}: {e.errmsg}")
            logger.debug(command)
        except (HTTPError, ConnectError) as e:
            logger.error(f"Cannot connect to device {self.name}: {exc_to_str(e)}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.critical(f"Exception raised while collecting command '{command.command}' on device {self.name} - {exc_to_str(e)}")
            logger.debug(tb_to_str(e))
            logger.debug(command)

    async def refresh(self) -> None:
        """
        Update attributes of an AsyncEOSDevice instance.

        This coroutine must update the following attributes of AsyncEOSDevice:
        - is_online: When a device IP is reachable and a port can be open
        - established: When a command execution succeeds
        - hw_model: The hardware model of the device
        """
        logger.debug(f"Refreshing device {self.name}")
        self.is_online = await self._session.check_connection()
        if self.is_online:
            try:
                response = await self._session.cli(command="show version")
            except EapiCommandError as e:
                logger.warning(f"Cannot get hardware information from device {self.name}: {e.errmsg}")
            except (HTTPError, ConnectError) as e:
                logger.warning(f"Cannot get hardware information from device {self.name}: {type(e).__name__}{'' if not str(e) else f' ({str(e)})'}")
            else:
                if self.HW_MODEL_KEY in response:
                    self.hw_model = response[self.HW_MODEL_KEY]
                else:
                    logger.warning(f"Cannot get hardware information from device {self.name}: cannot parse 'show version'")
        else:
            logger.warning(f"Could not connect to device {self.name}: cannot open eAPI port")
        self.established = bool(self.is_online and self.hw_model)

    async def copy(self, sources: List[Path], destination: Path, direction: Literal["to", "from"] = "from") -> None:
        """
        Copy files to and from the device using asyncssh.scp().

        Args:
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
            src: Union[List[Tuple[SSHClientConnection, Path]], List[Path]]
            dst: Union[Tuple[SSHClientConnection, Path], Path]
            if direction == "from":
                src = [(conn, file) for file in sources]
                dst = destination
                for file in sources:
                    logger.info(f"Copying '{file}' from device {self.name} to '{destination}' locally")
            elif direction == "to":
                src = sources
                dst = (conn, destination)
                for file in sources:
                    logger.info(f"Copying '{file}' to device {self.name} to '{destination}' remotely")
            else:
                logger.critical(f"'direction' argument to copy() fonction is invalid: {direction}")
                return
            await asyncssh.scp(src, dst)
