"""
Inventory Module for ANTA.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from netaddr import IPAddress, IPNetwork
from pydantic import ValidationError
from yaml import safe_load

from anta import __DEBUG__
from anta.device import AntaDevice, AsyncEOSDevice
from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyError
from anta.inventory.models import AntaInventoryInput
from anta.tools.misc import exc_to_str

logger = logging.getLogger(__name__)


class AntaInventory(dict):  # type: ignore
    # dict[str, AntaDevice] - not working in python 3.8 hence the ignore
    """
    Inventory abstraction for ANTA framework.
    """

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY = "anta_inventory"
    # Supported Output format
    INVENTORY_OUTPUT_FORMAT = ["native", "json"]

    def __str__(self) -> str:
        """Human readable string representing the inventory"""
        devs = {}
        for dev in self.values():
            if (dev_type := dev.__class__.__name__) not in devs:
                devs[dev_type] = 1
            else:
                devs[dev_type] += 1
        return f"ANTA Inventory contains {' '.join([f'{n} devices ({t})' for t, n in devs.items()])}"

    @staticmethod
    def parse(
        inventory_file: str, username: str, password: str, enable_password: Optional[str] = None, timeout: Optional[float] = None, insecure: bool = False
    ) -> AntaInventory:
        # pylint: disable=too-many-arguments
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
        kwargs: Dict[str, Any] = {"username": username, "password": password, "enable_password": enable_password, "timeout": timeout, "insecure": insecure}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        with open(inventory_file, "r", encoding="UTF-8") as file:
            data = safe_load(file)

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

        devices: List[AntaDevice] = list(filter(_filter_devices, self.values()))
        result = AntaInventory()
        for device in devices:
            result.add_device(device)
        return result

    ###########################################################################
    # SET methods
    ###########################################################################

    def __setitem__(self, key: str, value: AntaDevice) -> None:
        if key != value.name:
            raise RuntimeError(f"The key must be the device name for device '{value.name}'. Use AntaInventory.add_device().")
        return super().__setitem__(key, value)

    def add_device(self, device: AntaDevice) -> None:
        """Add a device to final inventory.

        Args:
            device: Device object to be added
        """
        self[device.name] = device

    ###########################################################################
    # MISC methods
    ###########################################################################

    async def connect_inventory(self) -> None:
        """Run `refresh()` coroutines for all AntaDevice objects in this inventory."""
        logger.debug("Refreshing devices...")
        results = await asyncio.gather(
            *(device.refresh() for device in self.values()),
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                message = "Error when refreshing inventory"
                if __DEBUG__:
                    logger.exception(message, exc_info=r)
                else:
                    logger.error(f"{message}: {exc_to_str(r)}")
