# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA CLI."""

from __future__ import annotations

import logging
import pathlib
import sys

import click

from anta import GITHUB_SUGGESTION, __version__
from anta.cli.check import check as check_command
from anta.cli.debug import debug as debug_command
from anta.cli.exec import _exec as exec_command
from anta.cli.get import get as get_command
from anta.cli.nrfu import nrfu as nrfu_command
from anta.cli.utils import AliasedGroup, ExitCode
from anta.logger import Log, LogLevel, anta_log_exception, setup_logging

logger = logging.getLogger(__name__)


@click.group(cls=AliasedGroup)
@click.pass_context
@click.help_option(allow_from_autoenv=False)
@click.version_option(__version__, allow_from_autoenv=False)
@click.option(
    "--log-file",
    help="Send the logs to a file. If logging level is DEBUG, only INFO or higher will be sent to stdout.",
    show_envvar=True,
    type=click.Path(file_okay=True, dir_okay=False, writable=True, path_type=pathlib.Path),
)
@click.option(
    "--log-level",
    "-l",
    help="ANTA logging level",
    default=logging.getLevelName(logging.INFO),
    show_envvar=True,
    show_default=True,
    type=click.Choice(
        [Log.CRITICAL, Log.ERROR, Log.WARNING, Log.INFO, Log.DEBUG],
        case_sensitive=False,
    ),
)
def anta(ctx: click.Context, log_level: LogLevel, log_file: pathlib.Path) -> None:
    """Arista Network Test Automation (ANTA) CLI."""
    _ = ctx.ensure_object(dict)
    setup_logging(log_level, log_file)


anta.add_command(nrfu_command)
anta.add_command(check_command)
anta.add_command(exec_command)
anta.add_command(get_command)
anta.add_command(debug_command)


def cli() -> None:
    """Entrypoint for pyproject.toml."""
    try:
        anta(obj={}, auto_envvar_prefix="ANTA")
    except Exception as exc:  # noqa: BLE001
        anta_log_exception(
            exc,
            f"Uncaught Exception when running ANTA CLI\n{GITHUB_SUGGESTION}",
            logger,
        )
        sys.exit(ExitCode.INTERNAL_ERROR)
