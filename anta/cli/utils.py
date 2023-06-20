#!/usr/bin/python
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.cli module.
"""

import logging
from typing import Any, Literal, Optional, Union

import click
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])


def setup_logging(level: str = "info") -> None:
    """
    Configure logging

    Args:
        level (str, optional): level name to configure. Defaults to 'critical'.
    """
    loglevel = getattr(logging, level.upper())
    logging.getLogger("anta").setLevel(loglevel)


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
