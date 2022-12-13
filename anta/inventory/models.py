#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Models related to inventory management."""

from typing import Dict, List, Optional, Any, Iterator, Type

from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, conint, root_validator
from aioeapi import Device

# Default values

DEFAULT_TAG = 'default'
DEFAULT_HW_MODEL = 'unset'

# Pydantic models for input validation


class AntaInventoryHost(BaseModel):
    """
    Host definition for user's inventory.

    Attributes:
        host (IPvAnyAddress): IPv4 or IPv6 address of the device
        tags (List[str]): List of attached tags read from inventory file.
    """

    name: Optional[str]
    host: str
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
    username: str
    password: str
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
        if values.get('session') is None:
            host = values.get('host')
            if not host:
                host = 'localhost'
            port = values.get('port')
            if not port:
                port = '8080' if host == 'localhost' else '443'
            proto = 'http' if port in ['80', '8080'] else 'https'
            values['session'] = Device(host=host, port=port,
                                       username=values.get('username'), password=values.get('password'),
                                       proto=proto, timeout=values.get('timeout'))
        if values.get('name') is None:
            values['name'] = f"{host}:{port}"
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
