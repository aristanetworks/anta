"""
Inventory Module for ANTA.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import yaml
from aioeapi.errors import EapiCommandError
from httpx import ConnectError, HTTPError
from netaddr import IPAddress, IPNetwork
from pydantic import ValidationError
from yaml.loader import SafeLoader

from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyError
from anta.inventory.models import AntaInventoryInput, InventoryDevice, InventoryDevices

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

            test = AntaInventory.parse(
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
    """

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY = "anta_inventory"
    # Supported Output format
    INVENTORY_OUTPUT_FORMAT = ["native", "json"]
    # HW model definition in show version
    HW_MODEL_KEY = "modelName"

    def __init__(self) -> None:
        """Class constructor"""
        self._inventory = InventoryDevices()

    @staticmethod
    def parse(inventory_file: str, username: str, password: str, enable_password: Optional[str] = None, timeout: Optional[float] = None) -> AntaInventory:
        """
        Create an AntaInventory object from an inventory file.

        Args:
            inventory_file (str): Path to inventory YAML file where user has described his inputs
            username (str): Username to use to connect to devices
            password (str): Password to use to connect to devices
            timeout (float, optional): timeout in seconds for every API call.

        Raises:
            InventoryRootKeyError: Root key of inventory is missing.
            InventoryIncorrectSchema: Inventory file is not following AntaInventory Schema.
            InventoryUnknownFormat: Output format is not supported.
        """

        inventory = AntaInventory()
        kwargs: Dict[str, Any] = {"username": username, "password": password, "enable_password": enable_password, "timeout": timeout}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        with open(inventory_file, "r", encoding="UTF-8") as fd:
            data = yaml.load(fd, Loader=SafeLoader)

        # Load data using Pydantic
        try:
            inventory_input = AntaInventoryInput(**data[AntaInventory.INVENTORY_ROOT_KEY])
        except KeyError as exc:
            logger.error(f"Inventory root key is missing: {AntaInventory.INVENTORY_ROOT_KEY}")
            raise InventoryRootKeyError(f"Inventory root key ({AntaInventory.INVENTORY_ROOT_KEY}) is not defined in your inventory") from exc
        except ValidationError as exc:
            logger.error("Inventory data are not compliant with inventory models")
            raise InventoryIncorrectSchema(f"Inventory is not following the schema: {str(exc)}") from exc

        # Read data from input
        if inventory_input.hosts is not None:
            for host in inventory_input.hosts:
                device = InventoryDevice(name=str(host.name), host=str(host.host), port=host.port, tags=host.tags, **kwargs)
                inventory.add_device(device)
        if inventory_input.networks is not None:
            for network in inventory_input.networks:
                for host_ip in IPNetwork(str(network.network)):
                    device = InventoryDevice(host=str(host_ip), tags=network.tags, **kwargs)
                    inventory.add_device(device)
        if inventory_input.ranges is not None:
            for range_def in inventory_input.ranges:
                range_increment = IPAddress(str(range_def.start))
                range_stop = IPAddress(str(range_def.end))
                while range_increment <= range_stop:
                    device = InventoryDevice(host=str(range_increment), tags=range_def.tags, **kwargs)
                    inventory.add_device(device)
                    range_increment += 1

        return inventory

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
            logger.warning(f"Cannot get HW information from device {device.name}: {e.errmsg}")
        except (HTTPError, ConnectError) as e:
            logger.warning(f"Cannot get HW information from device {device.name}: {type(e).__name__}{'' if not str(e) else f' ({str(e)})'}")
        else:
            if self.HW_MODEL_KEY in response:
                device.hw_model = response[self.HW_MODEL_KEY]
            else:
                logger.warning(f"Cannot get HW information from device {device.name}: cannot parse 'show version'")

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
            logger.warning(f"Could not connect to device {device.name}: cannot open eAPI port")
        device.established = bool(device.is_online and device.hw_model)

    ###########################################################################
    # Public methods
    ###########################################################################

    ###########################################################################
    # GET methods
    ###########################################################################

    def get_inventory(self, established_only: bool = False, tags: Optional[List[str]] = None) -> InventoryDevices:
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
    # SET methods
    ###########################################################################

    def add_device(self, device: InventoryDevice) -> None:
        """Add a InventoryDevice to final inventory.

        Args:
            device (InventoryDevice): Device object to be added
        """
        self._inventory.append(device)

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
                logger.error(f"Error when initiating inventory: {r.__class__.__name__}{'' if not str(r) else f' ({str(r)})'}")
