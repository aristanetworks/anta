#!/usr/bin/python
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.cli module.
"""

import logging
from typing import Any, Literal, Optional, Union

import click
from click import Option

import anta.loader
from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)


def parse_inventory(ctx: click.Context, param: Option, value: str) -> AntaInventory:
    try:
        inventory = AntaInventory.parse(
            inventory_file=value,
            username=ctx.params["username"],
            password=ctx.params["password"],
            enable_password=ctx.params["enable_password"],
            timeout=ctx.params["timeout"],
            insecure=ctx.params["insecure"],
        )
        logger.info(f"Inventory {value} loaded")
        return inventory
    except Exception as exc:
        ctx.fail(f"Unable to parse ANTA Inventory file '{value}': {str(exc)}")
        return None


def setup_logging(ctx: click.Context, param: Option, value: str) -> str:
    try:
        anta.loader.setup_logging(value)
        return value
    except Exception as exc:
        ctx.fail(f"Unable to set ANTA logging level '{value}': {str(exc)}")
        return None


class EapiVersion(click.ParamType):
    """
    Click custom type for eAPI parameter
    """

    name = "eAPI Version"

    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Union[int, Literal["latest"]]:
        if isinstance(value, int):
            return value
        try:
            if value.lower() == "latest":
                return value
            return int(value)
        except ValueError:
            self.fail(f"{value!r} is not a valid eAPI version", param, ctx)
            return None
