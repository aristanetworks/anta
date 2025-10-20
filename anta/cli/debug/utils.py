# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.debug module."""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any, TypeVar

import click

from anta.cli.utils import ExitCode, core_options

if TYPE_CHECKING:
    from collections.abc import Callable

    from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)

R = TypeVar("R")


def debug_options(f: Callable[..., R]) -> Callable[..., R]:
    """Click common options required to execute a command on a specific device."""

    @core_options
    @click.option(
        "--ofmt",
        type=click.Choice(["json", "text"]),
        default="json",
        help="EOS eAPI format to use. can be text or json",
    )
    @click.option(
        "--version",
        "-v",
        type=click.Choice(["1", "latest"]),
        default="latest",
        help="EOS eAPI version",
    )
    @click.option("--revision", "-r", type=int, help="eAPI command revision", required=False)
    @click.option("--device", "-d", type=str, required=True, help="Device from inventory to use")
    @click.pass_context
    @functools.wraps(f)
    def wrapper(
        ctx: click.Context,
        inventory: AntaInventory,
        device: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> R:
        if (d := inventory.get(device)) is None:
            logger.error("Device '%s' does not exist in Inventory", device)
            ctx.exit(ExitCode.USAGE_ERROR)
        return f(device=d, **kwargs)

    return wrapper
