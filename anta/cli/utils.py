#!/usr/bin/python
# coding: utf-8 -*-
"""
Utils functions to use with anta.cli module.
"""
from __future__ import annotations

import enum
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import click
from yaml import safe_load

import anta.loader
from anta.inventory import AntaInventory
from anta.result_manager.models import TestResult
from anta.tools.misc import anta_log_exception

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from click import Option

    from anta.result_manager import ResultManager


class ExitCode(enum.IntEnum):
    """
    Encodes the valid exit codes by anta
    inspired from pytest
    """

    # Tests passed.
    OK = 0
    #: Tests failed.
    TESTS_FAILED = 1
    # Test error
    TESTS_ERROR = 2
    # An internal error got in the way.
    INTERNAL_ERROR = 3
    #  pytest was misused.
    USAGE_ERROR = 4


def parse_inventory(ctx: click.Context, path: Path) -> AntaInventory:
    """
    Helper function parse an ANTA inventory YAML file
    """
    if ctx.obj.get("_anta_help"):
        # Currently looking for help for a subcommand so no
        # need to parse the Inventory, return an empty one
        return AntaInventory()
    try:
        inventory = AntaInventory.parse(
            inventory_file=str(path),
            username=ctx.params["username"],
            password=ctx.params["password"],
            enable=ctx.params["enable"],
            enable_password=ctx.params["enable_password"],
            timeout=ctx.params["timeout"],
            insecure=ctx.params["insecure"],
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        message = f"Unable to parse ANTA Inventory file '{path}'"
        anta_log_exception(e, message, logger)
        ctx.fail(message)
    return inventory


def parse_tags(ctx: click.Context, param: Option, value: str) -> Optional[List[str]]:
    # pylint: disable=unused-argument
    """
    Click option callback to parse an ANTA inventory tags
    """
    if value is not None:
        return value.split(",") if "," in value else [value]
    return None


def requires_enable(ctx: click.Context, param: Option, value: Optional[str]) -> Optional[str]:
    # pylint: disable=unused-argument
    """
    Click option callback to ensure that enable is True when the option is set
    """
    if value is not None and ctx.params.get("enable") is not True:
        raise click.BadParameter(f"'{param.opts[0]}' requires '--enable' (or setting associated env variable)")
    return value


def parse_catalog(ctx: click.Context, param: Option, value: str) -> List[Tuple[Callable[..., TestResult], Dict[Any, Any]]]:
    # pylint: disable=unused-argument
    """
    Click option callback to parse an ANTA tests catalog YAML file
    """
    if ctx.obj.get("_anta_help"):
        # Currently looking for help for a subcommand so no
        # need to parse the Catalog - return an empty list
        return []
    try:
        with open(value, "r", encoding="UTF-8") as file:
            data = safe_load(file)
    # TODO catch proper exception
    # pylint: disable-next=broad-exception-caught
    except Exception as e:
        message = f"Unable to parse ANTA Tests Catalog file '{value}'"
        anta_log_exception(e, message, logger)
        ctx.fail(message)

    return anta.loader.parse_catalog(data)


def setup_logging(ctx: click.Context, param: Option, value: str) -> str:
    # pylint: disable=unused-argument
    """
    Click option callback to set ANTA logging level
    """
    try:
        anta.loader.setup_logging(value)
    except Exception as e:  # pylint: disable=broad-exception-caught
        message = f"Unable to set ANTA logging level '{value}'"
        anta_log_exception(e, message, logger)
        ctx.fail(message)

    return value


def return_code(result_manager: ResultManager, ignore_error: bool, ignore_status: bool) -> int:
    """
    Args:
        result_manager (ResultManager)
        ignore_error (bool): Ignore error status
        ignore_status (bool): Ignore status completely and always return 0

    Returns:
        exit_code (int):
          * 0 if ignore_status is True or status is in ["unset", "skipped", "success"]
          * 1 if status is "failure"
          * 2 if status is "error"
    """

    if ignore_status:
        return 0

    # If ignore_error is True then status can never be "error"
    status = result_manager.get_status(ignore_error=ignore_error)

    if status in {"unset", "skipped", "success"}:
        return ExitCode.OK
    if status == "failure":
        return ExitCode.TESTS_FAILED
    if status == "error":
        return ExitCode.TESTS_ERROR

    logger.error("Please gather logs and open an issue on Github.")
    raise ValueError(f"Unknown status returned by the ResultManager: {status}. Please gather logs and open an issue on Github.")


class IgnoreRequiredWithHelp(click.Group):
    """
    https://stackoverflow.com/questions/55818737/python-click-application-required-parameters-have-precedence-over-sub-command-he
    Solution to allow help without required options on subcommand

    This is not planned to be fixed in click as per: https://github.com/pallets/click/issues/295#issuecomment-708129734
    """

    def parse_args(self, ctx: click.Context, args: List[str]) -> List[str]:
        """
        Ignore MissingParameter exception when parsing arguments if `--help`
        is present for a subcommand
        """
        # Adding a flag for potential callbacks
        ctx.ensure_object(dict)
        if "--help" in args:
            ctx.obj["_anta_help"] = True

        try:
            return super().parse_args(ctx, args)
        except click.MissingParameter:
            if "--help" not in args:
                raise

            # remove the required params so that help can display
            for param in self.params:
                param.required = False

            return super().parse_args(ctx, args)
