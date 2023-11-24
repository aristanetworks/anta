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
import os
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

import click
from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchema
from anta.inventory.exceptions import InventoryRootKeyError
from pydantic import ValidationError
from yaml import YAMLError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from click import Option


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
            filename=str(path),
            username=ctx.params["username"],
            password=ctx.params["password"],
            enable=ctx.params["enable"],
            enable_password=ctx.params["enable_password"],
            timeout=ctx.params["timeout"],
            insecure=ctx.params["insecure"],
            disable_cache=ctx.params["disable_cache"],
        )
    except (ValidationError, YAMLError, OSError, InventoryIncorrectSchema, InventoryRootKeyError):
        ctx.exit(ExitCode.USAGE_ERROR)
    return inventory


def parse_tags(ctx: click.Context, param: Option, value: str) -> list[str] | None:
    # pylint: disable=unused-argument
    """
    Click option callback to parse an ANTA inventory tags
    """
    if value is not None:
        return value.split(",") if "," in value else [value]
    return None


def parse_catalog(ctx: click.Context, param: Option, value: Path) -> AntaCatalog:
    # pylint: disable=unused-argument
    """
    Click option callback to parse an ANTA test catalog YAML file

    Store the orignal value (catalog path) in the ctx.obj
    """
    if ctx.obj.get("_anta_help"):
        # Currently looking for help for a subcommand so no
        # need to parse the Catalog - return an empty catalog
        return AntaCatalog()
    try:
        catalog: AntaCatalog = AntaCatalog.parse(value)
    except (ValidationError, YAMLError, OSError):
        ctx.exit(ExitCode.USAGE_ERROR)
    return catalog


def maybe_required_username_cb(ctx: click.Context, param: Option, value: str) -> Any:
    """
    Replace the "required" true with a callback to handle our specificies

    TODO: evaluate if moving the options to the groups is not better than this ..
    """
    if ctx.obj.get("_anta_help"):
        # If help then don't do anything
        return value
    if "get" in ctx.obj["args"]:
        if "from-cvp" in ctx.obj["args"] or "from-ansible" in ctx.obj["args"]:
            ctx.obj["skip_password"] = True
            return value
    if param.value_is_missing(value):
        raise click.exceptions.MissingParameter(ctx=ctx, param=param)
    return value


def maybe_required_inventory_cb(ctx: click.Context, param: Option, value: str) -> Any:
    """
    Replace the "required" true with a callback to handle our specificies

    TODO: evaluate if moving the options to the groups is not better than this ..
    """
    if ctx.obj.get("_anta_help"):
        # If help then don't do anything
        return value
    if "get" in ctx.obj["args"]:
        # the group has put the args from cli in the ctx.obj
        # This is a bit convoluted
        if "from-cvp" in ctx.obj["args"] or "from-ansible" in ctx.obj["args"]:
            ctx.obj["skip_inventory"] = True
            return value
    if param.value_is_missing(value):
        raise click.exceptions.MissingParameter(ctx=ctx, param=param)
    # Need to check that the inventory file exist
    # TODO, makes this better
    try:
        os.stat(value)
        return value
    except OSError as exc:
        # We want the file to exist
        raise click.exceptions.BadParameter(
            f"{param.name} {click.utils.format_filename(value)!r} does not exist.",
            ctx,
            param,
        ) from exc


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


class IgnoreRequiredWithHelp(AliasedGroup):
    """
    https://stackoverflow.com/questions/55818737/python-click-application-required-parameters-have-precedence-over-sub-command-he
    Solution to allow help without required options on subcommand

    This is not planned to be fixed in click as per: https://github.com/pallets/click/issues/295#issuecomment-708129734
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """
        Ignore MissingParameter exception when parsing arguments if `--help`
        is present for a subcommand
        """
        # Adding a flag for potential callbacks
        ctx.ensure_object(dict)
        if "--help" in args:
            ctx.obj["_anta_help"] = True

        # Storing full CLI call in ctx to get it in callbacks
        ctx.obj["args"] = args

        try:
            return super().parse_args(ctx, args)
        except click.MissingParameter:
            if "--help" not in args:
                raise

            # remove the required params so that help can display
            for param in self.params:
                param.required = False

            return super().parse_args(ctx, args)


def inventory_options(f):
    """
    Click common options when manipulating devices
    """

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
    @click.option(
        "--inventory",
        "-i",
        help="Path to the inventory YAML file",
        envvar="ANTA_INVENTORY",
        show_envvar=True,
        required=True,
        type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=Path),
    )
    @click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
    @functools.wraps(f)
    def wrapper_common_options(ctx: click.Context, *args, **kwargs):
        if not ctx.obj.get("_anta_help"):
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

        ctx.ensure_object(dict)
        inventory = ctx.params.get("inventory")
        ctx.obj["inventory_path"] = inventory
        ctx.obj["inventory"] = parse_inventory(ctx, inventory)
        return f(ctx, *args, **kwargs)

    return wrapper_common_options


def catalog_options(f):
    @click.option(
        "--catalog",
        "-c",
        envvar="ANTA_CATALOG",
        show_envvar=True,
        help="Path to the test catalog YAML file",
        type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True),
        required=True,
        callback=parse_catalog,
    )
    @functools.wraps(f)
    def wrapper_common_options(ctx: click.Context, *args, **kwargs):
        return f(ctx, *args, **kwargs)

    return wrapper_common_options
