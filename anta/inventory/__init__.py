"""
Inventory Module for ANTA.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import yaml
from aioeapi.errors import EapiCommandError
from httpx import ConnectError, HTTPError
from netaddr import IPAddress, IPNetwork
from pydantic import ValidationError
from yaml.loader import SafeLoader

from .exceptions import InventoryIncorrectSchema, InventoryRootKeyErrors
from .models import AntaInventoryInput, InventoryDevice, InventoryDevices

logger = logging.getLogger(__name__)


class AntaInventory:
    """
    Inventory Abstraction for ANTA framework.

    Attributes:
        timeout (float): Connection to device timeout.
        INVENTORY_ROOT_KEY (str, Optional): head of the YAML inventory. Default is anta_inventory
        EAPI_SESSION_TPL (str, Optional): Template for eAPI URL builder
        INVENTORY_OUTPUT_FORMAT (List[str],Optional): List of supported output format. Default ['native', 'json']
        HW_MODEL_KEY (str,Optional): Name of the key in Arista eAPI JSON provided by device.

    Examples:

        Inventory file input

            print(inventory.yml)
            anta_inventory:
              hosts:
                - hosts: 1.1.1.1
                - host: 2.2.2.2
                  tags: ['dc1', 'spine', 'pod01']
              networks:
                - network: 10.0.0.0/8
                - network: 192.168.0.0/16
                  tags: ['dc1', 'spine', 'pod01']
              ranges:
                - start: 10.0.0.1
                  end: 10.0.0.11
                  tags: ['dc1', 'spine', 'pod01']

        Inventory result:

            test = AntaInventory(
                ... inventory_file='examples/inventory.yml',
                ... username='ansible',
                ... password='ansible',
                ... auto_connect=True)
            test.get_inventory()
            [
                    "InventoryDevice(host=IPv4Address('192.168.0.17')",
                    "username='ansible'",
                    "password='ansible'",
                    "session=<ServerProxy for ansible:ansible@192.168.0.17/command-api>",
                    "url='https://ansible:ansible@192.168.0.17/command-api'",
                    "established=True",
                    "is_online=True",
                    "hw_model=cEOS-LAB",
                 ...
                    "InventoryDevice(host=IPv4Address('192.168.0.2')",
                    "username='ansible'",
                    "password='ansible'",
                    "session=None",
                    "url='https://ansible:ansible@192.168.0.2/command-api'",
                    "established=False"
                    "is_online=False",
                    "tags": ['dc1', 'spine', 'pod01'],
                    "hw_model=unset",
                ]

    Raises:
        InventoryRootKeyErrors: Root key of inventory is missing.
        InventoryIncorrectSchema: Inventory file is not following AntaInventory Schema.
        InventoryUnknownFormat: Output format is not supported.

    """

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY = "anta_inventory"
    # Supported Output format
    INVENTORY_OUTPUT_FORMAT = ["native", "json"]
    # HW model definition in show version
    HW_MODEL_KEY = "modelName"

    # pylint: disable=R0913
    def __init__(
        self,
        inventory_file: str,
        username: str,
        password: str,
        enable_password: Optional[str] = None,
        timeout: Optional[float] = None,
        filter_hosts: Optional[List[str]] = None,
    ) -> None:
        """Class constructor.

        Args:
            inventory_file (str): Path to inventory YAML file where user has described his inputs
            username (str): Username to use to connect to devices
            password (str): Password to use to connect to devices
            timeout (float, optional): timeout in seconds for every API call.
            filter_hosts (str, optional): create inventory only with matching host name in this list.
        """
        self._username = username
        self._password = password
        self._enable_password = enable_password
        self.timeout = timeout
        self._inventory = InventoryDevices()

        with open(inventory_file, "r", encoding="UTF-8") as fd:
            data = yaml.load(fd, Loader=SafeLoader)

        # Load data using Pydantic
        try:
            self._read_inventory = AntaInventoryInput(**data[self.INVENTORY_ROOT_KEY])
        except KeyError as exc:
            logger.error(f"Inventory root key is missing: {self.INVENTORY_ROOT_KEY}")
            raise InventoryRootKeyErrors(
                f"Inventory root key ({self.INVENTORY_ROOT_KEY}) is not defined in your inventory"
            ) from exc
        except ValidationError as exc:
            logger.error("Inventory data are not compliant with inventory models")
            raise InventoryIncorrectSchema("Inventory is not following schema") from exc

        # Read data from input
        if self._read_inventory.dict()["hosts"] is not None:
            self._inventory_read_hosts()
        if self._read_inventory.dict()["networks"] is not None:
            self._inventory_read_networks()
        if self._read_inventory.dict()["ranges"] is not None:
            self._inventory_read_ranges()

        if filter_hosts:
            for device in self._inventory:
                if device.url.host not in filter_hosts:
                    del device

    ###########################################################################
    # Boolean methods
    ###########################################################################

    def _is_ip_exist(self, ip: str) -> bool:  # TODO mtache: unused, remove this ?
        """Check if an IP is part of the current inventory.

        Args:
            ip (str): IP address to search in our inventory

        Returns:
            bool: True if device is in our inventory, False if not
        """
        logger.debug(f"Checking if device {ip} is in our inventory")
        return (
            len([str(dev.host) for dev in self._inventory if str(ip) == str(dev.host)])
            == 1
        )

    ###########################################################################
    # Internal methods
    ###########################################################################

    async def _read_device_hw(self, device: InventoryDevice) -> None:
        """
        _read_device_hw Get HW model name from show version and update the hw_model attribute.

        Args:
            device (InventoryDevice): Device to update
        """
        logger.debug(f"Reading HW information for {device.name}")
        try:
            response = await device.session.cli(command="show version")
        except EapiCommandError as e:
            logger.warning(
                f"Cannot get HW information from device {device.name}: {e.errmsg}"
            )
        except (HTTPError, ConnectError) as e:
            logger.warning(
                f"Cannot get HW information from device {device.name}: {type(e).__name__}{'' if not str(e) else f' ({str(e)})'}"
            )
        else:
            if self.HW_MODEL_KEY in response:
                device.hw_model = response[self.HW_MODEL_KEY]
            else:
                logger.warning(
                    f"Cannot get HW information from device {device.name}: cannot parse 'show version'"
                )

    async def _refresh_device_fact(self, device: InventoryDevice) -> None:
        """
        _get_from_device Update the is_online and established flags for InventoryDevice.

        It updates following keys:
        - is_online: When a device IP is reachable and a port can be open
        - established: When a CLI command in EXEC mode succeed using eAPI
        - hw_model: The hardware model string of the device

        Args:
            device (InventoryDevice): Device to check using InventoryDevice structure.

        Returns:
            InventoryDevice: Updated structure with devices information
        """
        logger.debug(f"Refreshing device {device.name}")
        device.is_online = await device.session.check_connection()
        if device.is_online:
            await self._read_device_hw(device=device)
        else:
            logger.warning(
                f"Could not connect to device {device.name}: cannot open eAPI port"
            )
        device.established = bool(device.is_online and device.hw_model)

    def _add_device_to_inventory(
        self,
        host: str,
        port: Optional[int] = None,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Add a InventoryDevice to final inventory.

        Create InventoryDevice and append to existing inventory

        Args:
            host (str): IP address or hostname of the device
            port (int): eAPI port of the device
            name (str): Optional name of the device
        """
        kwargs: Dict[str, Any] = {
            "host": host,
            "username": self._username,
            "password": self._password,
        }
        if name:
            kwargs["name"] = name
        if port:
            kwargs["port"] = port
        if self._enable_password:
            kwargs["enable_password"] = self._enable_password
        if tags:
            kwargs["tags"] = tags
        if self.timeout:
            kwargs["timeout"] = self.timeout
        device = InventoryDevice(**kwargs)
        self._inventory.append(device)

    def _inventory_read_hosts(self) -> None:
        """Read input data from hosts section and create inventory structure.

        Build InventoryDevice structure for all hosts under hosts section
        """
        assert self._read_inventory.hosts is not None
        for host in self._read_inventory.hosts:
            self._add_device_to_inventory(
                host.host, host.port, host.name, tags=host.tags
            )

    def _inventory_read_networks(self) -> None:
        """Read input data from networks section and create inventory structure.

        Build InventoryDevice structure for all IPs available in each declared subnet
        """
        assert self._read_inventory.networks is not None
        for network in self._read_inventory.networks:
            for host_ip in IPNetwork(str(network.network)):
                self._add_device_to_inventory(host_ip, tags=network.tags)

    def _inventory_read_ranges(self) -> None:
        """Read input data from ranges section and create inventory structure.

        Build InventoryDevice structure for all IPs available in each declared range
        """
        assert self._read_inventory.ranges is not None
        for range_def in self._read_inventory.ranges:
            range_increment = IPAddress(str(range_def.start))
            range_stop = IPAddress(str(range_def.end))
            while range_increment <= range_stop:
                self._add_device_to_inventory(
                    str(range_increment), tags=range_def.tags)
                range_increment += 1

    ###########################################################################
    # Public methods
    ###########################################################################

    ###########################################################################
    # GET methods
    ###########################################################################

    def get_inventory(
        self, established_only: bool = False, tags: Optional[List[str]] = None
    ) -> InventoryDevices:
        """
        get_inventory Returns a new filtered inventory.

        Args:
            established_only (bool, optional): Whether or not including non-established devices in the Inventory.
                                               Default False.
            tags (List[str], optional): List of tags to use to filter devices.

        Returns:
            InventoryDevices: An inventory with concerned devices
        """

        def _filter_devices(device: InventoryDevice) -> bool:
            """
            Helper function to select the devices based on the input tags
            and the requirement for an established connection.
            """
            if tags is not None and all(tag not in tags for tag in device.tags):
                return False
            return bool(not established_only or device.established)

        result = InventoryDevices()
        result.__root__ = list(filter(_filter_devices, self._inventory))
        return result

    ###########################################################################
    # MISC methods
    ###########################################################################

    async def connect_inventory(self) -> None:
        """connect_inventory Helper to prepare inventory with network data."""
        logger.debug("Refreshing facts for current inventory")
        results = await asyncio.gather(
            *(self._refresh_device_fact(device) for device in self._inventory),
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                logger.error(
                    f"Error when initiating inventory: {r.__class__.__name__}{'' if not str(r) else f' ({str(r)})'}"
                )
