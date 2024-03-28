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
    """Host definition for user's inventory.

    Attributes
    ----------
        host (IPvAnyAddress): IPv4 or IPv6 address of the device
        port (int): (Optional) eAPI port to use Default is 443.
        name (str): (Optional) Name to display during tests report. Default is hostname:port
        tags (list[str]): List of attached tags read from inventory file.
        disable_cache (bool): Disable cache per host. Defaults to False.

    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    host: Hostname | IPvAnyAddress
    port: Port | None = None
    tags: list[str] | None = None
    disable_cache: bool = False


class AntaInventoryNetwork(BaseModel):
    """Network definition for user's inventory.

    Attributes
    ----------
        network (IPvAnyNetwork): Subnet to use for testing.
        tags (list[str]): List of attached tags read from inventory file.
        disable_cache (bool): Disable cache per network. Defaults to False.

    """

    model_config = ConfigDict(extra="forbid")

    network: IPvAnyNetwork
    tags: list[str] | None = None
    disable_cache: bool = False


class AntaInventoryRange(BaseModel):
    """IP Range definition for user's inventory.

    Attributes
    ----------
        start (IPvAnyAddress): IPv4 or IPv6 address for the begining of the range.
        stop (IPvAnyAddress): IPv4 or IPv6 address for the end of the range.
        tags (list[str]): List of attached tags read from inventory file.
        disable_cache (bool): Disable cache per range of hosts. Defaults to False.

    """

    model_config = ConfigDict(extra="forbid")

    start: IPvAnyAddress
    end: IPvAnyAddress
    tags: list[str] | None = None
    disable_cache: bool = False


class AntaInventoryInput(BaseModel):
    """User's inventory model.

    Attributes
    ----------
        networks (list[AntaInventoryNetwork],Optional): List of AntaInventoryNetwork objects for networks.
        hosts (list[AntaInventoryHost],Optional): List of AntaInventoryHost objects for hosts.
        range (list[AntaInventoryRange],Optional): List of AntaInventoryRange objects for ranges.

    """

    model_config = ConfigDict(extra="forbid")

    networks: list[AntaInventoryNetwork] | None = None
    hosts: list[AntaInventoryHost] | None = None
    ranges: list[AntaInventoryRange] | None = None
