"""Models related to inventory management."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Union

from aioeapi import Device, EapiCommandError
from httpx import ConnectError, HTTPError
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, conint, constr, root_validator

from anta.models import AntaTestCommand
from anta.tools.misc import exc_to_str, tb_to_str

logger = logging.getLogger(__name__)

# Default values
DEFAULT_TAG = "all"
DEFAULT_HW_MODEL = "unset"

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
    tags: List[str] = [DEFAULT_TAG]


class AntaInventoryNetwork(BaseModel):
    """
    Network definition for user's inventory.

    Attributes:
        network (IPvAnyNetwork): Subnet to use for testing.
        tags (List[str]): List of attached tags read from inventory file.
    """

    network: IPvAnyNetwork
    tags: List[str] = [DEFAULT_TAG]


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
    tags: List[str] = [DEFAULT_TAG]


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


# Pydantic models for inventory output structures


class AntaDevice(BaseModel, ABC):
    """
    Abstract class representing a device in ANTA.
    An implementation of this class needs must override the abstract coroutine collect().

    Attributes:
        name (str): Device name
        username (str): Username to use for connection.
        password (password): Password to use for connection.
        enable_password (Optional[str]): enable_password to use on the device, required for some tests
        session (Any): JSONRPC session.
        established (bool): Flag to mark if connection is established (True) or not (False). Default: False.
        is_online (bool): Flag to mark if host is alive (True) or not (False). Default: False.
        hw_model (str): HW name gathered during device discovery.
        url (str): eAPI URL to use to build session.
        tags (List[str]): List of attached tags read from inventory file.
    """

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic model configuration"""

        arbitrary_types_allowed = True

    name: str
    host: Optional[Union[constr(regex=RFC_1123_REGEX), IPvAnyAddress]]  # type: ignore[valid-type]
    username: Optional[str]
    password: Optional[str]
    session: Any
    established: bool = False
    is_online: bool = False
    hw_model: str = DEFAULT_HW_MODEL
    tags: List[str] = [DEFAULT_TAG]
    timeout: float = 10.0

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

    @abstractmethod
    async def refresh(self) -> None:
        """
        Update attributes of an AntaDevice instance.

        This coroutine must update the following attributes of AntaDevice:
        - is_online: When a device IP is reachable and a port can be open
        - established: When a command execution succeeds
        - hw_model: The hardware model of the device
        """


class AsyncEOSDevice(AntaDevice):
    """
    Implementation of AntaDevice for EOS using aio-eapi.
    """

    host: Union[constr(regex=RFC_1123_REGEX), IPvAnyAddress]  # type: ignore[valid-type]
    port: conint(gt=1, lt=65535)  # type: ignore[valid-type]
    username: str
    password: str
    enable_password: Optional[str]

    session: Device
    # Hardware model definition in show version
    HW_MODEL_KEY: str = "modelName"

    @root_validator(pre=True)
    def build_device(cls: BaseModel, values: Dict[str, Any]) -> Dict[str, Any]:
        """Build the device session object"""
        if not values.get("host"):
            values["host"] = "localhost"
        if not values.get("port"):
            values["port"] = "8080" if values["host"] == "localhost" else "443"
        if values.get("tags") is not None:
            values["tags"].append(DEFAULT_TAG)
        else:
            values["tags"] = [DEFAULT_TAG]
        if values.get("session") is None:
            proto = "http" if values["port"] in ["80", "8080"] else "https"
            values["session"] = Device(
                host=values["host"],
                port=values["port"],
                username=values.get("username"),
                password=values.get("password"),
                proto=proto,
                timeout=values.get("timeout"),
            )
        if values.get("name") is None:
            values["name"] = f"{values['host']}:{values['port']}"
        return values

    def __eq__(self, other: object) -> bool:
        """
        Two AsyncEOSDevice objects are equal if the hostname and the port are the same.
        This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        if not isinstance(other, AsyncEOSDevice):
            return False
        return self.host == other.host and self.port == other.port

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
            if self.enable_password is not None:
                enable_cmd = {
                    "cmd": "enable",
                    "input": str(self.enable_password),
                }
            else:
                enable_cmd = {"cmd": "enable"}
            response = await self.session.cli(
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
        self.is_online = await self.session.check_connection()
        if self.is_online:
            try:
                response = await self.session.cli(command="show version")
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
