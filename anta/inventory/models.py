# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to inventory management."""

from __future__ import annotations

import logging
import math

import yaml
from pydantic import BaseModel, ConfigDict, FieldSerializationInfo, IPvAnyAddress, IPvAnyNetwork, field_serializer

from anta.custom_types import Hostname, Port

logger = logging.getLogger(__name__)


class AntaInventoryBaseModel(BaseModel):
    """Pydantic BaseModel for AntaInventory objects."""

    model_config = ConfigDict(extra="forbid")

    # Using check_fields as we plan to use this in the child classes
    @field_serializer("tags", when_used="json", check_fields=False)
    def serialize_tags(self, tags: set[str], _info: FieldSerializationInfo) -> list[str]:
        """Make sure the tags are always dumped in the same order."""
        return sorted(tags)


class AntaInventoryHost(AntaInventoryBaseModel):
    """Host entry of AntaInventoryInput.

    Attributes
    ----------
    host : Hostname | IPvAnyAddress
        IP Address or FQDN of the device.
    port : Port | None
        Custom eAPI port to use.
    name : str | None
        Custom name of the device.
    tags : set[str]
        Tags of the device.
    disable_cache : bool
        Disable cache for this device.

    """

    name: str | None = None
    host: Hostname | IPvAnyAddress
    port: Port | None = None
    tags: set[str] | None = None
    disable_cache: bool = False


class AntaInventoryNetwork(AntaInventoryBaseModel):
    """Network entry of AntaInventoryInput.

    Attributes
    ----------
    network : IPvAnyNetwork
        Subnet to use for scanning.
    tags : set[str]
        Tags of the devices in this network.
    disable_cache : bool
        Disable cache for all devices in this network.

    """

    network: IPvAnyNetwork
    tags: set[str] | None = None
    disable_cache: bool = False


class AntaInventoryRange(AntaInventoryBaseModel):
    """IP Range entry of AntaInventoryInput.

    Attributes
    ----------
    start : IPvAnyAddress
        IPv4 or IPv6 address for the beginning of the range.
    stop : IPvAnyAddress
        IPv4 or IPv6 address for the end of the range.
    tags : set[str]
        Tags of the devices in this IP range.
    disable_cache : bool
        Disable cache for all devices in this IP range.

    """

    start: IPvAnyAddress
    end: IPvAnyAddress
    tags: set[str] | None = None
    disable_cache: bool = False


class AntaInventoryInput(BaseModel):
    """Device inventory input model."""

    model_config = ConfigDict(extra="forbid")

    networks: list[AntaInventoryNetwork] | None = None
    hosts: list[AntaInventoryHost] | None = None
    ranges: list[AntaInventoryRange] | None = None

    def yaml(self) -> str:
        """Return a YAML representation string of this model.

        Returns
        -------
        str
            The YAML representation string of this model.
        """
        # TODO: Pydantic and YAML serialization/deserialization is not supported natively.
        # This could be improved.
        # https://github.com/pydantic/pydantic/issues/1043
        # Explore if this worth using this: https://github.com/NowanIlfideme/pydantic-yaml
        return yaml.safe_dump(yaml.safe_load(self.model_dump_json(serialize_as_any=True, exclude_unset=True)), width=math.inf)

    def to_json(self) -> str:
        """Return a JSON representation string of this model.

        Returns
        -------
            The JSON representation string of this model.
        """
        return self.model_dump_json(exclude_unset=True, indent=2)
