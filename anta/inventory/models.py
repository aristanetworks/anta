"""Models related to inventory management."""

from __future__ import annotations

import json
import logging
import sys
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Union

# from ansible_collections.arista.eos.plugins.httpapi.eos import HttpApi
from aioeapi import Device, EapiCommandError
from httpx import ConnectError, HTTPError
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, conint, constr, root_validator

from anta.models import AntaTestCommand
from anta.tools.misc import exc_to_str

# Default values
logger = logging.getLogger(__name__)

DEFAULT_TAG = "all"
DEFAULT_HW_MODEL = "unset"
DEFAULT_NAME = ""

# Pydantic models for input validation

RFC_1123_REGEX = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"

if sys.version_info < (3, 10):
    # @gmuloc - TODO - drop this when anta drops 3.8/3.9 support
    # For Python < 3.10, it is not possible to install a version of aio-eapi newer than 0.3.0
    # which sadly hardcodes version to 1 in its call to eAPI
    # This little piece of nasty hack patches the aio-eapi function to support using a different
    # version of the eAPI.
    # Hic Sunt Draconis.
    # Are we proud of this? No.
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

    python_version = ".".join(map(str, sys.version_info[:3]))
    logger.warning(f"Using Python {python_version} < 3.10 - patching aioeapi.Device.jsoncrpc_command to support 'latest' version")
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


class InventoryDevice(ABC, BaseModel):
    """
    Abstract class for InventoryDevice.

    Attributes:
        name (str): Device name gathered during device initialization.
        session (Any): JSONRPC session. Can support synchronous or asynchronous session object.
        hw_model (str): HW name gathered during device initialization.
    """

    name: str = DEFAULT_NAME
    session: Any
    hw_model: str = DEFAULT_HW_MODEL

    @abstractmethod
    def sync_collect(self, command: AntaTestCommand) -> Any:
        """
        Prepares and sends request(s) to device synchronously.

        Args:
            command (AntaTestCommand): Command to execute on the device.

        Returns:
            Any: The command that was executed, including its output data.
        """

    @abstractmethod
    async def async_collect(self, command: AntaTestCommand) -> Any:
        """
        Prepares and sends request(s) to device asynchronously.

        Args:
            command (AntaTestCommand): Command to execute on the device.

        Returns:
            Any: The command that was executed, including its output data.
        """


class InventoryDeviceHttpApi(InventoryDevice):
    """
    Implementation of InventoryDevice with Ansible HttpApi connection session object.
    """

    @root_validator(pre=True)
    def set_attributes(cls: BaseModel, values: Dict[str, Any]) -> Dict[str, Any]:
        """Set the class attributes"""
        try:
            # Get the device info
            device_info = values["session"].get_device_info()
            values["hw_model"] = device_info.get("network_os_model")
            values["name"] = device_info.get("network_os_hostname")

        except ConnectionError as e:
            # Handle connection errors
            logger.error(f"Connection error raised while collecting device info of {values['name']}) - {exc_to_str(e)}")
            logger.debug(traceback.format_exc())

        return values

    def sync_collect(self, command: AntaTestCommand) -> AntaTestCommand:
        """
        Collect device command result using HttpApi session.

        Args:
            command (AntaTestCommand): Command to execute on the device.

        Returns:
            AntaTestCommand: The command that was executed, including its output data.
        """

        logger.debug(f"run collect from device {self.name} for {command}")

        try:
            # Execute the command and process the response
            response = self.session.send_request(command.command, version=command.version, output=command.ofmt)
            data = json.loads(response) if command.ofmt == "json" else response
            command.output = data

        except ConnectionError as e:
            # Handle connection errors
            logger.error(f"Connection error raised while collecting data for test {self.name} (on device {self.name}) - {exc_to_str(e)}")
            logger.debug(traceback.format_exc())

        return command

    async def async_collect(self, command: AntaTestCommand) -> NotImplementedError:
        """
        Asynchronous collector is not implemented for the HttpApi connector.
        """
        raise NotImplementedError(f"Asynchronous collector is not implemented for {self.__class__.__name__}.")


class InventoryDeviceAioeapi(InventoryDevice):
    """
    Implementation of InventoryDevice with asynchronous connection session object.

    Attributes:
        host (str | IPvAnyAddress): IP address to use for connection.
        username (str): Username to use for connection.
        password (str): Password to use for connection.
        port (int): Port to use for connection.
        enable_password (Optional[str]): enable_password to use on the device, required for some tests
        established (bool): Flag to mark if connection is established (True) or not (False). Default: False.
        is_online (bool): Flag to mark if host is alive (True) or not (False). Default: False.
        tags (List[str]): List of attached tags read from inventory file.
        timeout (float): Timeout in seconds for the connection. Default: 10.0.
    """

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic model configuration"""

        arbitrary_types_allowed = True

    # Setup class attributes with default values
    host: Union[constr(regex=RFC_1123_REGEX), IPvAnyAddress]  # type: ignore[valid-type]
    username: str
    password: str
    port: conint(gt=1, lt=65535)  # type: ignore[valid-type]
    enable_password: Optional[str]
    established: bool = False
    is_online: bool = False
    tags: List[str] = [DEFAULT_TAG]
    timeout: float = 10.0

    @root_validator(pre=True)
    def set_attributes(cls: BaseModel, values: Dict[str, Any]) -> Dict[str, Any]:
        """Build the class attributes"""
        # Setup default values if not provided
        if not values.get("host"):
            values["host"] = "localhost"
        if not values.get("port"):
            values["port"] = "8080" if values["host"] == "localhost" else "443"
        if values.get("tags") is not None:
            values["tags"].append(DEFAULT_TAG)
        else:
            values["tags"] = [DEFAULT_TAG]
        if values.get("session") is None:
            # Initialize session object
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
        Two InventoryDeviceAioeapi objects are equal if the hostname and the port are the same.
        This covers the use case of port forwarding when the host is localhost and the devices have different ports.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, InventoryDeviceAioeapi):
            return False
        return self.session.host == other.session.host and self.session.port == other.session.port

    def assert_enable_password_is_not_none(self, test_name: Optional[str] = None) -> None:
        """
        Raise ValueError if enable_password is None

        Args:
            test_name (Optional[str]): Name of the test if available.

        Raises:
            ValueError: If enable_password is None.
        """
        if not self.enable_password:
            if test_name:
                message = f"{test_name} requires `enable_password` to be set"
            else:
                message = "`enable_password` is not set"
            raise ValueError(message)

    def sync_collect(self, command: AntaTestCommand) -> NotImplementedError:
        """
        Synchronous collector is not implemented for the Aioepi connector.
        """
        raise NotImplementedError(f"Asynchronous collector is not implemented for {self.__class__.__name__}.")

    async def async_collect(self, command: AntaTestCommand) -> AntaTestCommand:
        """
        Collect device command result asynchronously.
        FIXME: Under development / testing
        TODO: Build documentation
        Args:
            command (AntaTestCommand): Command to execute on the device.

        Returns:
            AntaTestCommand: The command that was executed, including its output data.
        """
        logger.debug(f"run collect from device {self.name} for {command}")

        try:
            if self.enable_password is not None:
                enable_cmd = {
                    "cmd": "enable",
                    "input": str(self.enable_password),
                }
            else:
                enable_cmd = {"cmd": "enable"}
            # FIXME: RuntimeError: Event loop is closed
            # When sending commands over 2 asyncio.run, the first call
            # of the second run fails
            # Workaround in cli.debug.run_template
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

        except EapiCommandError as e:
            # Handle command error
            logger.error(f"Command failed on {self.name}: {e.errmsg}")
        except (HTTPError, ConnectError) as e:
            # Handle HTTP and connection errors
            logger.error(f"Cannot connect to device {self.name}: {type(e).__name__}{exc_to_str(e)}")
            logger.debug(traceback.format_exc())
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Handle any other errors
            logger.error(f"Exception raised while collecting data for test {self.name} (on device {self.name}) - {exc_to_str(e)}")
            logger.debug(traceback.format_exc())

        return command


class InventoryDevices(BaseModel):
    """
    Inventory model to list all InventoryDeviceAioeapi entries.

    Attributes:
        __root__(List[InventoryDeviceAioeapi]): A list of InventoryDeviceAioeapi objects.
    """

    # pylint: disable=R0801

    __root__: List[InventoryDeviceAioeapi] = []

    def append(self, value: InventoryDeviceAioeapi) -> None:
        """Add support for append method."""
        self.__root__.append(value)

    def __iter__(self) -> Iterator[InventoryDeviceAioeapi]:
        """Use custom iter method."""
        # TODO - mypy is not happy because we overwrite BaseModel.__iter__
        # return type and are breaking Liskov Substitution Principle.
        return iter(self.__root__)

    def __getitem__(self, item: int) -> InventoryDeviceAioeapi:
        """Use custom getitem method."""
        return self.__root__[item]

    def __len__(self) -> int:
        """Support for length of __root__"""
        return len(self.__root__)

    def json(self, **kwargs: Any) -> str:
        """Returns a JSON representation of the devices"""
        return super().json(exclude={"__root__": {"__all__": {"session"}}}, **kwargs)
