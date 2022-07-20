#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: skip-file

"""Models related to inventory management."""

from typing import List, Optional, Any
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork


# Pydantic models for input validation

class AntaInventoryHost(BaseModel):
    """
    Host definition for user's inventory.

    Attributes:
        host(IPvAnyAddress): IPv4 or IPv6 address of the device
    """
    host: IPvAnyAddress

class AntaInventoryNetwork(BaseModel):
    """
    Network definition for user's inventory.

    Attributes:
        network(IPvAnyNetwork): Subnet to use for testing.
    """
    network: IPvAnyNetwork

class AntaInventoryRange(BaseModel):
    """
    IP Range definition for user's inventory.

    Attributes:
        start(IPvAnyAddress): IPv4 or IPv6 address for the begining of the range.
        stop(IPvAnyAddress): IPv4 or IPv6 address for the end of the range.
    """
    start: IPvAnyAddress
    end: IPvAnyAddress

class AntaInventoryInput(BaseModel):
    """
    User's inventory model.

    Attributes:
        netwrks(List[AntaInventoryNetwork],Optional): List of AntaInventoryNetwork objects for networks.
        hosts(List[AntaInventoryHost],Optional): List of AntaInventoryHost objects for hosts.
        range(List[AntaInventoryRange],Optional): List of AntaInventoryRange objects for ranges.
    """
    networks: Optional[List[AntaInventoryNetwork]]
    hosts: Optional[List[AntaInventoryHost]]
    ranges: Optional[List[AntaInventoryRange]]

# Pydantic models for inventory output structures

class InventoryDevice(BaseModel):
    """
    Inventory model exposed by Inventory class.

    Attributes:
        host(IPvAnyAddress): IPv4 or IPv6 address of the device.
        username(str): Username to use for connection.
        password(password): Password to use for connection.
        session(Any): JSONRPC session.
        established(bool): Flag to mark if connection is established (True) or not (False). Default: False.
        is_online(bool): Flag to mark if host is alive (True) or not (False). Default: False.
        hw_model(str): HW name gathered during device discovery.
        url(str): eAPI URL to use to build session.
    """
    host: IPvAnyAddress
    username: str
    password: str
    session: Any
    established = False
    is_online = False
    hw_model: str = 'unset'
    url: str

class InventoryDevices(BaseModel):
    """
    Inventory model to list all InventoryDevice entries.

    Attributes:
        __root__(List[InventoryDevice]): A list of InventoryDevice objects.
    """
    __root__ = []

    def append(self, value) -> None:
        """Add support for append method."""
        self.__root__.append(value)
        super().__init__(__root__=self.__root__)

    def __iter__(self):
        """Use custom iter method."""
        return iter(self.__root__)

    def __getitem__(self, item):
        """Use custom getitem method."""
        return self.__root__[item]

    def __len__(self):
        """Support for length of __root__"""
        return len(self.__root__)
