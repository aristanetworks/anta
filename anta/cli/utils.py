# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli module."""

from __future__ import annotations

import enum
import functools
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

import click
from yaml import YAMLError

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchemaError, InventoryRootKeyError
from anta.logger import anta_log_exception

if TYPE_CHECKING:
    from collections.abc import Callable

    from click import Option

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

logger = logging.getLogger(__name__)
R = TypeVar("R")


class ExitCode(enum.IntEnum):
    """Encodes the valid exit codes by anta inspired from pytest."""

    # Tests passed.
    OK = 0
    # An internal error got in the way.
    INTERNAL_ERROR = 1
    # CLI was misused
    USAGE_ERROR = 2
    # Test error
    TESTS_ERROR = 3
    # Tests failed
    TESTS_FAILED = 4


def parse_tags(_ctx: click.Context, _param: Option, value: str | None) -> set[str] | None:
    """Click option callback to parse an ANTA inventory tags."""
    if value is not None:
        return set(value.split(",")) if "," in value else {value}
    return None


def exit_with_code(ctx: click.Context) -> None:
    """Exit the Click application with an exit code.

    This function determines the global test status to be either `unset`, `skipped`, `success` or `error`
    from the `ResultManger` instance.
    If flag `ignore_error` is set, the `error` status will be ignored in all the tests.
    If flag `ignore_status` is set, the exit code will always be 0.
    Exit the application with the following exit code:
        * 0 if `ignore_status` is `True` or global test status is `unset`, `skipped` or `success`
        * 1 if status is `failure`
        * 2 if status is `error`.

    Parameters
    ----------
    ctx
        Click Context.

    """
    if ctx.obj.get("ignore_status"):
        ctx.exit(ExitCode.OK)

    # If ignore_error is True then status can never be "error"
    status = ctx.obj["result_manager"].get_status(ignore_error=bool(ctx.obj.get("ignore_error")))

    if status in {"unset", "skipped", "success"}:
        ctx.exit(ExitCode.OK)
    if status == "failure":
        ctx.exit(ExitCode.TESTS_FAILED)
    if status == "error":
        ctx.exit(ExitCode.TESTS_ERROR)

    logger.error("Please gather logs and open an issue on Github.")
    msg = f"Unknown status returned by the ResultManager: {status}. Please gather logs and open an issue on Github."
    raise ValueError(msg)


class AliasedGroup(click.Group):
    """Implements a subclass of Group that accepts a prefix for a command.

    If there were a command called push, it would accept pus as an alias (so long as it was unique)
    From Click documentation.
    """

    # Adding noqa because https://github.com/astral-sh/ruff/issues/5474, same for pylint
    @override  # noqa: RET503
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | click.Group | None:  # pylint: disable=R1710
        """Try to find a command name based on a prefix."""
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    @override
    def resolve_command(self, ctx: click.Context, args: list[str]) -> tuple[str | None, click.Command | None, list[str]]:
        """Return the full command name as first tuple element."""
        _, cmd, args = super().resolve_command(ctx, args)
        if not cmd or cmd.name is None:
            return None, None, []
        return cmd.name, cmd, args


def core_options(f: Callable[..., R]) -> Callable[..., R]:
    """Click common options when requiring an inventory to interact with devices."""

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
        envvar="ANTA_ENABLE_PASSWORD",
    )
    @click.option(
        "--enable",
        help="Some commands may require EOS Privileged EXEC mode. This option tries to access this mode before sending a command to the device.",
        default=False,
        show_envvar=True,
        envvar="ANTA_ENABLE",
        is_flag=True,
        show_default=True,
    )
    @click.option(
        "--prompt",
        "-P",
        help="Prompt for passwords if they are not provided.",
        default=False,
        show_envvar=True,
        envvar="ANTA_PROMPT",
        is_flag=True,
        show_default=True,
    )
    @click.option(
        "--timeout",
        help="Global API timeout. This value will be used for all devices.",
        default=30.0,
        show_envvar=True,
        envvar="ANTA_TIMEOUT",
        show_default=True,
        type=float,
    )
    @click.option(
        "--insecure",
        help="Disable SSH Host Key validation.",
        default=False,
        show_envvar=True,
        envvar="ANTA_INSECURE",
        is_flag=True,
        show_default=True,
    )
    @click.option(
        "--disable-cache",
        help="Disable cache globally.",
        show_envvar=True,
        envvar="ANTA_DISABLE_CACHE",
        show_default=True,
        is_flag=True,
        default=False,
    )
    @click.option(
        "--inventory",
        "-i",
        help="Path to the inventory YAML file.",
        envvar="ANTA_INVENTORY",
        show_envvar=True,
        required=True,
        type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=Path),
    )
    @click.option(
        "--inventory-format",
        envvar="ANTA_INVENTORY_FORMAT",
        show_envvar=True,
        help="Format of the inventory file, either 'yaml' or 'json'",
        default="yaml",
        type=click.Choice(["yaml", "json"], case_sensitive=False),
    )
    @click.pass_context
    @functools.wraps(f)
    def wrapper(
        ctx: click.Context,
        *,
        inventory: Path,
        username: str,
        password: str | None,
        enable_password: str | None,
        enable: bool,
        prompt: bool,
        timeout: float,
        insecure: bool,
        disable_cache: bool,
        inventory_format: Literal["json", "yaml"],
        **kwargs: Any,  # noqa: ANN401
    ) -> R:
        # If help is invoke somewhere, do not parse inventory
        if ctx.obj.get("_anta_help"):
            return f(inventory=None, **kwargs)
        if prompt:
            # User asked for a password prompt
            if password is None:
                password = click.prompt(
                    "Please enter a password to connect to EOS",
                    type=str,
                    hide_input=True,
                )
            if enable and enable_password is None and click.confirm("Is a password required to enter EOS privileged EXEC mode?"):
                enable_password = click.prompt(
                    "Please enter a password to enter EOS privileged EXEC mode",
                    type=str,
                    hide_input=True,
                )
        if password is None:
            msg = "EOS password needs to be provided by using either the '--password' option or the '--prompt' option."
            raise click.BadParameter(msg)
        if not enable and enable_password:
            msg = "Providing a password to access EOS Privileged EXEC mode requires '--enable' option."
            raise click.BadParameter(msg)
        try:
            i = AntaInventory.parse(
                filename=inventory,
                username=username,
                password=password,
                enable=enable,
                enable_password=enable_password,
                timeout=timeout,
                insecure=insecure,
                disable_cache=disable_cache,
                file_format=inventory_format,
            )
        except (TypeError, ValueError, YAMLError, OSError, InventoryIncorrectSchemaError, InventoryRootKeyError) as e:
            anta_log_exception(e, f"Failed to parse the inventory: {inventory}", logger)
            ctx.exit(ExitCode.USAGE_ERROR)
        return f(inventory=i, **kwargs)

    return wrapper


def inventory_options(f: Callable[..., R]) -> Callable[..., R]:
    """Click common options when requiring an inventory to interact with devices."""

    @core_options
    @click.option(
        "--tags",
        help="List of tags using comma as separator: tag1,tag2,tag3.",
        show_envvar=True,
        envvar="ANTA_TAGS",
        type=str,
        required=False,
        callback=parse_tags,
    )
    @click.pass_context
    @functools.wraps(f)
    def wrapper(
        ctx: click.Context,
        tags: set[str] | None,
        **kwargs: Any,  # noqa: ANN401
    ) -> R:
        # If help is invoke somewhere, do not parse inventory
        if ctx.obj.get("_anta_help"):
            return f(tags=tags, **kwargs)
        return f(tags=tags, **kwargs)

    return wrapper


def catalog_options(*, required: bool = True) -> Callable[..., Callable[..., object]]:
    """Click common options when requiring a test catalog to execute ANTA tests."""

    def wrapper(f: Callable[..., object]) -> Callable[..., object]:
        """Click common options when requiring a test catalog to execute ANTA tests."""

        @click.option(
            "--catalog",
            "-c",
            envvar="ANTA_CATALOG",
            show_envvar=True,
            help="Path to the test catalog file",
            type=click.Path(
                file_okay=True,
                dir_okay=False,
                exists=True,
                readable=True,
                path_type=Path,
            ),
            required=required,
        )
        @click.option(
            "--catalog-format",
            envvar="ANTA_CATALOG_FORMAT",
            show_envvar=True,
            help="Format of the catalog file, either 'yaml' or 'json'",
            default="yaml",
            type=click.Choice(["yaml", "json"], case_sensitive=False),
        )
        @click.pass_context
        @functools.wraps(f)
        def wrapper(
            ctx: click.Context,
            catalog: Path | None,
            catalog_format: Literal["yaml", "json"],
            **kwargs: Any,  # noqa: ANN401
        ) -> object:
            # If help is invoke somewhere, do not parse catalog
            if ctx.obj.get("_anta_help"):
                return f(catalog=None, **kwargs)
            if not catalog and not required:
                return f(catalog=None, **kwargs)
            if not catalog:
                # This should never happen
                msg = "Missing catalog in inputs"
                raise RuntimeError(msg)
            try:
                # the type checker needs help
                file_format = cast('Literal["json", "yaml"]', catalog_format.lower())
                c = AntaCatalog.parse(catalog, file_format=file_format)
            except (TypeError, ValueError, YAMLError, OSError) as e:
                anta_log_exception(e, f"Failed to parse the catalog: {catalog}", logger)
                ctx.exit(ExitCode.USAGE_ERROR)
            return f(catalog=c, **kwargs)

        return wrapper

    return wrapper
