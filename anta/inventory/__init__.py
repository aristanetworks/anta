# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Inventory module for ANTA."""

from __future__ import annotations

import asyncio
import logging
from ipaddress import ip_address, ip_network
from json import load as json_load
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import ValidationError
from yaml import YAMLError, safe_load

from anta.device import AntaDevice, AsyncEOSDevice
from anta.inventory.exceptions import InventoryIncorrectSchemaError, InventoryRootKeyError
from anta.inventory.models import AntaInventoryHost, AntaInventoryInput
from anta.logger import anta_log_exception

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing_extensions import TypeIs


class AntaInventory(dict[str, AntaDevice]):
    """Inventory abstraction for ANTA framework."""

    # Root key of inventory part of the inventory file
    INVENTORY_ROOT_KEY: str = "anta_inventory"
    # Supported Output format
    INVENTORY_OUTPUT_FORMAT: ClassVar[list[str]] = ["native", "json"]

    def __str__(self) -> str:
        """Human readable string representing the inventory."""
        devs = {}
        for dev in self.values():
            if (dev_type := dev.__class__.__name__) not in devs:
                devs[dev_type] = 1
            else:
                devs[dev_type] += 1
        return f"ANTA Inventory contains {' '.join([f'{n} devices ({t})' for t, n in devs.items()])}"

    @staticmethod
    def _update_disable_cache(kwargs: dict[str, Any], *, inventory_disable_cache: bool) -> dict[str, Any]:
        """Return new dictionary, replacing kwargs with added disable_cache value from inventory_value if disable_cache has not been set by CLI.

        Parameters
        ----------
        inventory_disable_cache
            The value of disable_cache in the inventory.
        kwargs
            The kwargs to instantiate the device.

        """
        updated_kwargs = kwargs.copy()
        updated_kwargs["disable_cache"] = inventory_disable_cache or kwargs.get("disable_cache")
        return updated_kwargs

    @staticmethod
    def _parse_hosts(
        inventory_input: AntaInventoryInput,
        inventory: AntaInventory,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Parse the host section of an AntaInventoryInput and add the devices to the inventory.

        Parameters
        ----------
        inventory_input
            AntaInventoryInput used to parse the devices.
        inventory
            AntaInventory to add the parsed devices to.
        **kwargs
            Additional keyword arguments to pass to the device constructor.

        """
        if inventory_input.hosts is None:
            return

        for host in inventory_input.hosts:
            updated_kwargs = AntaInventory._update_disable_cache(kwargs, inventory_disable_cache=host.disable_cache)
            device = AsyncEOSDevice(
                name=host.name,
                host=str(host.host),
                port=host.port,
                tags=host.tags,
                **updated_kwargs,
            )
            inventory.add_device(device)

    @staticmethod
    def _parse_networks(
        inventory_input: AntaInventoryInput,
        inventory: AntaInventory,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Parse the network section of an AntaInventoryInput and add the devices to the inventory.

        Parameters
        ----------
        inventory_input
            AntaInventoryInput used to parse the devices.
        inventory
            AntaInventory to add the parsed devices to.
        **kwargs
           Additional keyword arguments to pass to the device constructor.

        Raises
        ------
        InventoryIncorrectSchemaError
            Inventory file is not following AntaInventory Schema.

        """
        if inventory_input.networks is None:
            return

        try:
            for network in inventory_input.networks:
                updated_kwargs = AntaInventory._update_disable_cache(kwargs, inventory_disable_cache=network.disable_cache)
                for host_ip in ip_network(str(network.network)):
                    device = AsyncEOSDevice(host=str(host_ip), tags=network.tags, **updated_kwargs)
                    inventory.add_device(device)
        except ValueError as e:
            message = "Could not parse the network section in the inventory"
            anta_log_exception(e, message, logger)
            raise InventoryIncorrectSchemaError(message) from e

    @staticmethod
    def _parse_ranges(
        inventory_input: AntaInventoryInput,
        inventory: AntaInventory,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Parse the range section of an AntaInventoryInput and add the devices to the inventory.

        Parameters
        ----------
        inventory_input
            AntaInventoryInput used to parse the devices.
        inventory
            AntaInventory to add the parsed devices to.
        **kwargs
            Additional keyword arguments to pass to the device constructor.

        Raises
        ------
        InventoryIncorrectSchemaError
            Inventory file is not following AntaInventory Schema.

        """
        if inventory_input.ranges is None:
            return

        try:
            for range_def in inventory_input.ranges:
                updated_kwargs = AntaInventory._update_disable_cache(kwargs, inventory_disable_cache=range_def.disable_cache)
                range_increment = ip_address(str(range_def.start))
                range_stop = ip_address(str(range_def.end))
                while range_increment <= range_stop:  # type: ignore[operator]
                    # mypy raise an issue about comparing IPv4Address and IPv6Address
                    # but this is handled by the ipaddress module natively by raising a TypeError
                    device = AsyncEOSDevice(host=str(range_increment), tags=range_def.tags, **updated_kwargs)
                    inventory.add_device(device)
                    range_increment += 1
        except ValueError as e:
            message = "Could not parse the range section in the inventory"
            anta_log_exception(e, message, logger)
            raise InventoryIncorrectSchemaError(message) from e
        except TypeError as e:
            message = "A range in the inventory has different address families (IPv4 vs IPv6)"
            anta_log_exception(e, message, logger)
            raise InventoryIncorrectSchemaError(message) from e

    @staticmethod
    def parse(
        filename: str | Path,
        username: str,
        password: str,
        enable_password: str | None = None,
        timeout: float | None = None,
        file_format: Literal["yaml", "json"] = "yaml",
        *,
        enable: bool = False,
        insecure: bool = False,
        disable_cache: bool = False,
    ) -> AntaInventory:
        """Create an AntaInventory instance from an inventory file.

        The inventory devices are AsyncEOSDevice instances.

        Parameters
        ----------
        filename
            Path to device inventory YAML file.
        username
            Username to use to connect to devices.
        password
            Password to use to connect to devices.
        enable_password
            Enable password to use if required.
        timeout
            Global timeout value in seconds for outgoing eAPI calls. None means no timeout.
        file_format
            Whether the inventory file is in JSON or YAML.
        enable
            Whether or not the commands need to be run in enable mode towards the devices.
        insecure
            Disable SSH Host Key validation.
        disable_cache
            Disable cache globally.

        Raises
        ------
        InventoryRootKeyError
            Root key of inventory is missing.
        InventoryIncorrectSchemaError
            Inventory file is not following AntaInventory Schema.

        """
        if file_format not in ["yaml", "json"]:
            message = f"'{file_format}' is not a valid format for an AntaInventory file. Only 'yaml' and 'json' are supported."
            raise ValueError(message)

        inventory = AntaInventory()
        kwargs: dict[str, Any] = {
            "username": username,
            "password": password,
            "enable": enable,
            "enable_password": enable_password,
            "timeout": timeout,
            "insecure": insecure,
            "disable_cache": disable_cache,
        }

        try:
            filename = Path(filename)
            with filename.open(encoding="UTF-8") as file:
                data = safe_load(file) if file_format == "yaml" else json_load(file)
        except (TypeError, YAMLError, OSError, ValueError) as e:
            message = f"Unable to parse ANTA Device Inventory file '{filename}'"
            anta_log_exception(e, message, logger)
            raise

        if AntaInventory.INVENTORY_ROOT_KEY not in data:
            exc = InventoryRootKeyError(f"Inventory root key ({AntaInventory.INVENTORY_ROOT_KEY}) is not defined in your inventory")
            anta_log_exception(exc, f"Device inventory is invalid! (from {filename})", logger)
            raise exc

        try:
            inventory_input = AntaInventoryInput(**data[AntaInventory.INVENTORY_ROOT_KEY])
        except ValidationError as e:
            anta_log_exception(e, f"Device inventory is invalid! (from {filename})", logger)
            raise

        # Read data from input
        AntaInventory._parse_hosts(inventory_input, inventory, **kwargs)
        AntaInventory._parse_networks(inventory_input, inventory, **kwargs)
        AntaInventory._parse_ranges(inventory_input, inventory, **kwargs)

        return inventory

    @property
    def devices(self) -> list[AntaDevice]:
        """List of AntaDevice in this inventory."""
        return list(self.values())

    @property
    def max_potential_connections(self) -> int | None:
        """Max potential connections of this inventory."""
        return self._get_potential_connections()

    ###########################################################################
    # Public methods
    ###########################################################################

    ###########################################################################
    # GET methods
    ###########################################################################

    def get_inventory(self, *, established_only: bool = False, tags: set[str] | None = None, devices: set[str] | None = None) -> AntaInventory:
        """Return a filtered inventory.

        Parameters
        ----------
        established_only
            Whether or not to include only established devices.
        tags
            Tags to filter devices.
        devices
            Names to filter devices.

        Returns
        -------
        AntaInventory
            An inventory with filtered AntaDevice objects.
        """

        def _filter_devices(device: AntaDevice) -> bool:
            """Select the devices based on the inputs `tags`, `devices` and `established_only`."""
            if tags is not None and all(tag not in tags for tag in device.tags):
                return False
            if devices is None or device.name in devices:
                return bool(not established_only or device.established)
            return False

        filtered_devices: list[AntaDevice] = list(filter(_filter_devices, self.values()))
        result = AntaInventory()
        for device in filtered_devices:
            result.add_device(device)
        return result

    def _get_potential_connections(self) -> int | None:
        """Calculate the total potential concurrent connections for the current inventory.

        This method sums the maximum concurrent connections allowed for each
        AntaDevice in the inventory.

        Returns
        -------
        int | None
            The total sum of the `max_connections` attribute for all AntaDevice objects
            in the inventory. Returns None if any AntaDevice does not have a `max_connections`
            attribute or if its value is None, as the total count cannot be determined.
        """
        potential_connections = 0
        all_have_connections = True
        for device in self.devices:
            if device.max_connections is None:
                all_have_connections = False
                logger.debug("Device %s 'max_connections' is not available", device.name)
                break
            potential_connections += device.max_connections
        return None if not all_have_connections else potential_connections

    ###########################################################################
    # SET methods
    ###########################################################################

    def __setitem__(self, key: str, value: AntaDevice) -> None:
        """Set a device in the inventory."""
        if key != value.name:
            msg = f"The key must be the device name for device '{value.name}'. Use AntaInventory.add_device()."
            raise RuntimeError(msg)
        return super().__setitem__(key, value)

    def add_device(self, device: AntaDevice) -> None:
        """Add a device to final inventory.

        Parameters
        ----------
        device
            Device object to be added.

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
                anta_log_exception(r, message, logger)

    def is_base_class(self, device: AntaDevice) -> TypeIs[AntaDevice]:
        """Check the type of device, return True if the device is an AntaDevice."""
        return not hasattr(device, "host") and not hasattr(device, "port")

    def dump(self) -> AntaInventoryInput:
        """Dump the AntaInventory to an AntaInventoryInput.

        Each hosts is dumped individually.
        """
        hosts = [
            AntaInventoryHost(
                name=device.name,
                host=device.host if not self.is_base_class(device) else device.name,
                port=device.port if not self.is_base_class(device) else None,
                tags=device.tags,
                disable_cache=device.cache is None,
            )
            for device in self.devices
        ]
        return AntaInventoryInput(hosts=hosts)
