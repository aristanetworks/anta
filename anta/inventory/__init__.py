"""
Inventory Module for ANTA.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

import yaml
from netaddr import IPAddress, IPNetwork
from pydantic import ValidationError
from yaml.loader import SafeLoader

from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyError
from anta.inventory.models import AntaDevice, AntaInventoryInput, AsyncEOSDevice

logger = logging.getLogger(__name__)


class AntaInventory:
    """
    Inventory abstraction for ANTA framework.
    """

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY = "anta_inventory"
    # Supported Output format
    INVENTORY_OUTPUT_FORMAT = ["native", "json"]

    def __init__(self) -> None:
        """Class constructor"""
        self._inventory: List[AntaDevice] = []

    def __iter__(self) -> Iterator[AntaDevice]:
        """Make AntaInventory iterable"""
        return iter(self._inventory)

    # https://github.com/python/mypy/issues/6523
    if TYPE_CHECKING:
        __dict__ = {}  # type: Dict[str, Any]
    else:

        @property
        def __dict__(self) -> dict[str, Any]:
            """
            Returns a dictionary that represents the AntaInventory object.
            """
            result = {}
            for dev in self._inventory:
                result[dev.name] = vars(dev)
            return result

    @staticmethod
    def parse(inventory_file: str, username: str, password: str, enable_password: Optional[str] = None, timeout: Optional[float] = None) -> AntaInventory:
        """
        Create an AntaInventory object from an inventory file.
        Instantiate AntaDevice objects using the AsyncEOSDevice subclass.

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
                device = AsyncEOSDevice(name=host.name, host=str(host.host), port=host.port, tags=host.tags, **kwargs)
                inventory.add_device(device)
        if inventory_input.networks is not None:
            for network in inventory_input.networks:
                for host_ip in IPNetwork(str(network.network)):
                    device = AsyncEOSDevice(host=str(host_ip), tags=network.tags, **kwargs)
                    inventory.add_device(device)
        if inventory_input.ranges is not None:
            for range_def in inventory_input.ranges:
                range_increment = IPAddress(str(range_def.start))
                range_stop = IPAddress(str(range_def.end))
                while range_increment <= range_stop:
                    device = AsyncEOSDevice(host=str(range_increment), tags=range_def.tags, **kwargs)
                    inventory.add_device(device)
                    range_increment += 1

        return inventory

    ###########################################################################
    # Public methods
    ###########################################################################

    ###########################################################################
    # GET methods
    ###########################################################################

    def get_inventory(self, established_only: bool = False, tags: Optional[List[str]] = None) -> AntaInventory:
        """
        Returns a filtered inventory.

        Args:
            established_only: Whether or not to include only established devices. Default False.
            tags: List of tags to filter devices.

        Returns:
            AntaInventory: An inventory with filtered AntaDevice objects.
        """

        def _filter_devices(device: AntaDevice) -> bool:
            """
            Helper function to select the devices based on the input tags
            and the requirement for an established connection.
            """
            if tags is not None and all(tag not in tags for tag in device.tags):
                return False
            return bool(not established_only or device.established)

        devices: List[AntaDevice] = list(filter(_filter_devices, self._inventory))
        result = AntaInventory()
        for device in devices:
            result.add_device(device)
        return result

    ###########################################################################
    # SET methods
    ###########################################################################

    def add_device(self, device: AntaDevice) -> None:
        """Add a device to final inventory.

        Args:
            device: Device object to be added
        """
        self._inventory.append(device)

    ###########################################################################
    # MISC methods
    ###########################################################################

    async def connect_inventory(self) -> None:
        """connect_inventory Helper to prepare inventory with network data."""
        logger.debug("Refreshing facts for current inventory")
        results = await asyncio.gather(
            *(device.refresh() for device in self._inventory),
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Error when initiating inventory: {r.__class__.__name__}{'' if not str(r) else f' ({str(r)})'}")
