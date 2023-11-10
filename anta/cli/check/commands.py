# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable = redefined-outer-name
"""
Commands for Anta CLI to run check commands.
"""
from __future__ import annotations

import logging

import click
from rich.pretty import pretty_repr

from anta.catalog import AntaCatalog
from anta.cli.console import console
from anta.cli.utils import parse_catalog

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--catalog",
    "-c",
    envvar="ANTA_CATALOG",
    show_envvar=True,
    help="Path to the test catalog YAML file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, resolve_path=True),
    required=True,
    callback=parse_catalog,
)
def catalog(catalog: AntaCatalog) -> None:
    """
    Check that the catalog is valid
    """
    console.print(f"[bold][green]Catalog {catalog.filename} is valid")
    console.print(pretty_repr(catalog.tests))
