#!/usr/bin/env python
# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
ANTA CLI
"""
from __future__ import annotations

import logging
import pathlib

import click

from anta import __version__
from anta.cli.check import check
from anta.cli.debug import debug
from anta.cli.exec import exec
from anta.cli.get import get
from anta.cli.nrfu import nrfu
from anta.cli.utils import AliasedGroup
from anta.logger import Log, LogLevel, setup_logging


@click.group(cls=AliasedGroup)
@click.pass_context
@click.version_option(__version__)
@click.option(
    "--log-file",
    help="Send the logs to a file. If logging level is DEBUG, only INFO or higher will be sent to stdout.",
    show_envvar=True,
    type=click.Path(file_okay=True, dir_okay=False, writable=True, path_type=pathlib.Path),
)
@click.option(
    "--log-level",
    "--log",
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
    """Arista Network Test Automation (ANTA) CLI"""
    ctx.ensure_object(dict)
    setup_logging(log_level, log_file)


anta.add_command(nrfu)
anta.add_command(check)
anta.add_command(exec)
anta.add_command(get)
anta.add_command(debug)


def cli() -> None:
    """Entrypoint for pyproject.toml"""
    anta(obj={}, auto_envvar_prefix="ANTA")


if __name__ == "__main__":
    cli()
