#!/usr/bin/python
# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# coding: utf-8 -*-
"""
Utils functions to use with anta.cli.debug module.
"""
from __future__ import annotations

import functools
import logging
from typing import Any

import click

from anta.cli.utils import ExitCode, inventory_options
from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)


def debug_options(f: Any) -> Any:
    """Click common options when requiring a test catalog to execute ANTA tests"""

    @inventory_options
    @click.option("--ofmt", type=click.Choice(["json", "text"]), default="json", help="EOS eAPI format to use. can be text or json")
    @click.option("--version", "-v", type=click.Choice(["1", "latest"]), default="latest", help="EOS eAPI version")
    @click.option("--revision", "-r", type=int, help="eAPI command revision", required=False)
    @click.option("--device", "-d", type=str, required=True, help="Device from inventory to use")
    @click.pass_context
    @functools.wraps(f)
    def wrapper(ctx: click.Context, inventory: AntaInventory, *args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
        try:
            kwargs["device"] = inventory[ctx.params["device"]]
        except KeyError as e:
            message = f"Device {ctx.params['device']} does not exist in Inventory"
            logger.error(e, message)
            ctx.exit(ExitCode.USAGE_ERROR)
        return f(*args, **kwargs)

    return wrapper
