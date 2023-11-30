#!/usr/bin/python
# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# coding: utf-8 -*-
"""
Utils functions to use with anta.cli module.
"""
from __future__ import annotations

import enum
import functools
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
from pydantic import ValidationError
from yaml import YAMLError

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyError

if TYPE_CHECKING:
    from click import Option

logger = logging.getLogger(__name__)


class ExitCode(enum.IntEnum):
    """
    Encodes the valid exit codes by anta
    inspired from pytest
    """

    # Tests passed.
    OK = 0
    #: Tests failed.
    TESTS_FAILED = 1
    # CLI was misused
    USAGE_ERROR = 2
    # Test error
    TESTS_ERROR = 3
    # An internal error got in the way.
    INTERNAL_ERROR = 4


def parse_tags(ctx: click.Context, param: Option, value: str) -> list[str] | None:
    # pylint: disable=unused-argument
    """
    Click option callback to parse an ANTA inventory tags
    """
    if value is not None:
        return value.split(",") if "," in value else [value]
    return None


def exit_with_code(ctx: click.Context) -> None:
    """
    Exit the Click application with an exit code.
    This function determines the global test status to be either `unset`, `skipped`, `success` or `error`
    from the `ResultManger` instance.
    If flag `ignore_error` is set, the `error` status will be ignored in all the tests.
    If flag `ignore_status` is set, the exit code will always be 0.
    Exit the application with the following exit code:
        * 0 if `ignore_status` is `True` or global test status is `unset`, `skipped` or `success`
        * 1 if status is `failure`
        * 2 if status is `error`

    Args:
        ctx: Click Context
    """

    if ctx.params.get("ignore_status"):
        ctx.exit(0)

    # If ignore_error is True then status can never be "error"
    status = ctx.obj["result_manager"].get_status(ignore_error=bool(ctx.params.get("ignore_error")))

    if status in {"unset", "skipped", "success"}:
        ctx.exit(ExitCode.OK)
    if status == "failure":
        ctx.exit(ExitCode.TESTS_FAILED)
    if status == "error":
        ctx.exit(ExitCode.TESTS_ERROR)

    logger.error("Please gather logs and open an issue on Github.")
    raise ValueError(f"Unknown status returned by the ResultManager: {status}. Please gather logs and open an issue on Github.")


class AliasedGroup(click.Group):
    """
    Implements a subclass of Group that accepts a prefix for a command.
    If there were a command called push, it would accept pus as an alias (so long as it was unique)
    From Click documentation
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> Any:
        """Todo: document code"""
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")
        return None

    def resolve_command(self, ctx: click.Context, args: Any) -> Any:
        """Todo: document code"""
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args  # type: ignore


def inventory_options(f: Any) -> Any:
    """Click common options when requiring an inventory to interact with devices"""

    @click.option(
        "--username",
        "-u",
        help="Username to connect to EOS",
        envvar="ANTA_USERNAME",
        show_envvar=True,
        required=True,
    )
    @click.option(
        "--password",
        "-p",
        help="Password to connect to EOS that must be provided. It can be prompted using '--prompt' option.",
        show_envvar=True,
        envvar="ANTA_PASSWORD",
    )
    @click.option(
        "--enable-password",
        help="Password to access EOS Privileged EXEC mode. It can be prompted using '--prompt' option. Requires '--enable' option.",
        show_envvar=True,
    )
    @click.option(
        "--enable",
        help="Some commands may require EOS Privileged EXEC mode. This option tries to access this mode before sending a command to the device.",
        default=False,
        show_envvar=True,
        is_flag=True,
        show_default=True,
    )
    @click.option(
        "--prompt",
        "-P",
        help="Prompt for passwords if they are not provided.",
        default=False,
        is_flag=True,
        show_default=True,
    )
    @click.option(
        "--timeout",
        help="Global connection timeout",
        default=30,
        show_envvar=True,
        show_default=True,
    )
    @click.option(
        "--insecure",
        help="Disable SSH Host Key validation",
        default=False,
        show_envvar=True,
        is_flag=True,
        show_default=True,
    )
    @click.option("--disable-cache", help="Disable cache globally", show_envvar=True, show_default=True, is_flag=True, default=False)
    @click.option(
        "--inventory",
        "-i",
        help="Path to the inventory YAML file",
        envvar="ANTA_INVENTORY",
        show_envvar=True,
        required=True,
        type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=Path),
    )
    @click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
    @click.pass_context
    @functools.wraps(f)
    def wrapper(ctx: click.Context, *args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
        if ctx.params.get("prompt"):
            # User asked for a password prompt
            if ctx.params.get("password") is None:
                ctx.params["password"] = click.prompt("Please enter a password to connect to EOS", type=str, hide_input=True, confirmation_prompt=True)
            if ctx.params.get("enable"):
                if ctx.params.get("enable_password") is None:
                    if click.confirm("Is a password required to enter EOS privileged EXEC mode?"):
                        ctx.params["enable_password"] = click.prompt(
                            "Please enter a password to enter EOS privileged EXEC mode", type=str, hide_input=True, confirmation_prompt=True
                        )
        if ctx.params.get("password") is None:
            raise click.BadParameter("EOS password needs to be provided by using either the '--password' option or the '--prompt' option.")
        if not ctx.params.get("enable") and ctx.params.get("enable_password"):
            raise click.BadParameter("Providing a password to access EOS Privileged EXEC mode requires '--enable' option.")
        try:
            inventory = AntaInventory.parse(
                filename=ctx.params["inventory"],
                username=ctx.params["username"],
                password=ctx.params["password"],
                enable=ctx.params["enable"],
                enable_password=ctx.params["enable_password"],
                timeout=ctx.params["timeout"],
                insecure=ctx.params["insecure"],
                disable_cache=ctx.params["disable_cache"],
            )
        except (ValidationError, TypeError, ValueError, YAMLError, OSError, InventoryIncorrectSchema, InventoryRootKeyError):
            ctx.exit(ExitCode.USAGE_ERROR)
        for arg in ["inventory", "username", "password", "enable", "prompt", "timeout", "insecure", "enable_password", "disable_cache", "tags"]:
            kwargs.pop(arg)
        return f(*args, inventory, ctx.params["tags"], **kwargs)

    return wrapper


def catalog_options(f: Any) -> Any:
    """Click common options when requiring a test catalog to execute ANTA tests"""

    @click.option(
        "--catalog",
        "-c",
        envvar="ANTA_CATALOG",
        show_envvar=True,
        help="Path to the test catalog YAML file",
        type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=Path),
        required=True,
    )
    @click.pass_context
    @functools.wraps(f)
    def wrapper(ctx: click.Context, *args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
        try:
            catalog = AntaCatalog.parse(ctx.params["catalog"])
        except (ValidationError, TypeError, ValueError, YAMLError, OSError):
            ctx.exit(ExitCode.USAGE_ERROR)
        kwargs.pop("catalog")
        return f(*args, catalog, **kwargs)

    return wrapper
