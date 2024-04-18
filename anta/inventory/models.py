# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to inventory management."""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, IPvAnyAddress, IPvAnyNetwork

from anta.custom_types import Hostname, Port

logger = logging.getLogger(__name__)


class AntaInventoryHost(BaseModel):
    """Host entry of AntaInventoryInput.

    Attributes
    ----------
        host: IP Address or FQDN of the device.
        port: Custom eAPI port to use.
        name: Custom name of the device.
        tags: Tags of the device.
        disable_cache: Disable cache for this device.

    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    host: Hostname | IPvAnyAddress
    port: Port | None = None
    tags: set[str] | None = None
    disable_cache: bool = False


class AntaInventoryNetwork(BaseModel):
    """Network entry of AntaInventoryInput.

    Attributes
    ----------
        network: Subnet to use for scanning.
        tags: Tags of the devices in this network.
        disable_cache: Disable cache for all devices in this network.

    """

    model_config = ConfigDict(extra="forbid")

    network: IPvAnyNetwork
    tags: set[str] | None = None
    disable_cache: bool = False


class AntaInventoryRange(BaseModel):
    """IP Range entry of AntaInventoryInput.

    Attributes
    ----------
        start: IPv4 or IPv6 address for the beginning of the range.
        stop: IPv4 or IPv6 address for the end of the range.
        tags: Tags of the devices in this IP range.
        disable_cache: Disable cache for all devices in this IP range.

    """

    model_config = ConfigDict(extra="forbid")

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
