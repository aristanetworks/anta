"""Models related to inventory management."""

import logging
from typing import Any, Dict, Iterator, List, Optional, Type, Union

import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException

from aioeapi import Device
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, conint, constr, root_validator

# Default values

DEFAULT_TAG = 'all'
DEFAULT_HW_MODEL = 'unset'

# Pydantic models for input validation

RFC_1123_REGEX = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'


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

class InventoryDevice(BaseModel):
    """
    Inventory model exposed by Inventory class.

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
        """ Pydantic model configuration """
        arbitrary_types_allowed = True

    name: str
    host: Union[constr(regex=RFC_1123_REGEX), IPvAnyAddress]  # type: ignore[valid-type]
    username: str
    password: str
    port: conint(gt=1, lt=65535)  # type: ignore[valid-type]
    enable_password: Optional[str]
    session: Device
    established = False
    is_online = False
    hw_model: str = DEFAULT_HW_MODEL
    tags: List[str] = [DEFAULT_TAG]
    timeout: float = 10.0

    @root_validator(pre=True)
    def build_device(cls: Type[Any], values: Dict[str, Any]) -> Dict[str, Any]:
        """ Build the device session object """
        if not values.get('host'):
            values['host'] = 'localhost'
        if not values.get('port'):
            values['port'] = '8080' if values['host'] == 'localhost' else '443'
        if values.get('tags') is not None:
            values['tags'].append(DEFAULT_TAG)
        else:
            values['tags'] = [DEFAULT_TAG]
        if values.get('session') is None:
            proto = 'http' if values['port'] in ['80', '8080'] else 'https'
            values['session'] = Device(host=values['host'], port=values['port'],
                                       username=values.get('username'), password=values.get('password'),
                                       proto=proto, timeout=values.get('timeout'))
        if values.get('name') is None:
            values['name'] = f"{values['host']}:{values['port']}"
        return values

    def __eq__(self, other: BaseModel) -> bool:
        """
            Two InventoryDevice objects are equal if the hostname and the port are the same.
            This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        return self.session.host == other.session.host and self.session.port == other.session.port

    def assert_enable_password_is_not_none(self, test_name: Optional[str] = None) -> None:
        """
        raise ValueError is enable_password is None
        """
        if not self.enable_password:
            if test_name:
                message = f"{test_name} requires `enable_password` to be set"
            else:
                message = "`enable_password` is not set"
            raise ValueError(message)

    def create_ssh_socket(self, ssh_port: int = 22, banner_timeout: int = 60) -> paramiko.SSHClient:
        """
        Create SSH socket to send commend over SSH

        Returns:
            paramiko.SSHClient: SSH Socket created
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                port=ssh_port,
                username=self.username,
                password=self.password,
                banner_timeout=banner_timeout
            )
        except AuthenticationException as error:
            logging.error(f'Authentication error for device {self.name}')
            logging.error(error)
        except SSHException as error:
            logging.error(f'SSHException for device {self.name}')
            logging.error(error)
        return client


class InventoryDevices(BaseModel):
    """
    Inventory model to list all InventoryDevice entries.

    Attributes:
        __root__(List[InventoryDevice]): A list of InventoryDevice objects.
    """
    # pylint: disable=R0801

    __root__: List[InventoryDevice] = []

    def append(self, value: InventoryDevice) -> None:
        """Add support for append method."""
        self.__root__.append(value)

    def __iter__(self) -> Iterator[InventoryDevice]:
        """Use custom iter method."""
        return iter(self.__root__)

    def __getitem__(self, item: int) -> InventoryDevice:
        """Use custom getitem method."""
        return self.__root__[item]

    def __len__(self) -> int:
        """Support for length of __root__"""
        return len(self.__root__)

    def json(self) -> str:
        """Returns a JSON representation of the devices"""
        return super().json(exclude={'__root__': {'__all__': {'session'}}})
