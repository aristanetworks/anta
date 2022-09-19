#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Models related to inventory management."""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Iterator, Type
from pydantic.networks import Parts
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, AnyHttpUrl, conint, root_validator
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

class eAPIUrl(AnyHttpUrl):
    """
    eAPI URL field type
    The build method has been overriden to provide default value of a eAPI endpoint when using it.

    Examples:
    In : eAPIUrl.build()
    Out: 'http://localhost:8080/command-api'

    In : eAPIUrl.build(host='1.1.1.1')
    Out: 'https://1.1.1.1:443/command-api'

    In : eAPIUrl.build(host='1.1.1.1', port='80')
    Out: 'http://1.1.1.1:80/command-api'
    """
    allowed_schemes = {'http', 'https'}
    host_required = True

    @staticmethod
    def get_default_parts(parts: Parts) -> Parts:
        return {
            'scheme': 'http' if ((parts.get('port') in ['80', '8080']) or parts.get('host') is None) else 'https',
            'domain': 'localhost' if (parts.get('port') == '8080') else '',
            'port': '8080' if (parts.get('host') is None) else '443',
            'path': '/command-api',
        }

    @classmethod
    def build(cls: Type[eAPIUrl], **kwargs: Any) -> eAPIUrl:
        """
        Include default path and port when building an eAPI URL
        """
        parts = Parts(**kwargs)
        default = cls.get_default_parts(parts)
        for field in default:
            if field not in kwargs:
                kwargs.update({field: default.get(field)})
        return super().build(**kwargs)


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
    class Config:
        arbitrary_types_allowed = True

    name: str
    user: str  # TODO: duplicate with url.user
    password: str  # TODO: duplicate with url.password
    enable_password: Optional[str]
    session: Optional[Device]
    established = False
    is_online = False
    hw_model: str = DEFAULT_HW_MODEL
    url: eAPIUrl
    tags: List[str] = [DEFAULT_TAG]

    @root_validator(pre=True)
    def build_name(cls: Type[InventoryDevice], values: Dict[str, Any]) -> Dict[str, Any]:
        """ Build name attribute """
        if values.get('name') is None:
            assert 'host' in values, 'host required if name is not provided'
            values['name'] = f"{values.get('host')}:{values['url'].get('port')}"
        return values

    @root_validator(pre=True)
    def build_eapi_url(cls: Type[InventoryDevice], values: Dict[str, Any]) -> Dict[str, Any]:
        """ Build url attribute """
        if values.get('url') is None:
            if values.get('host') is not None:
                # Ensure the host field is a string
                values.update(host=str(values['host']))
            if values.get('port') is not None:
                # Ensure the port field is a string
                values.update(port=str(values['port']))
            values['url'] = eAPIUrl.build(**values)
        return values

    def __eq__(self, other: BaseModel) -> bool:
        """
            Two InventoryDevice objects are equal if the hostname and the port are the same.
            This covers the use case of port forwarding when the host is localhost and the devices have different ports.
        """
        return self.url.host == other.url.host and self.url.port == other.url.port

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
