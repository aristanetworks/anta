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

from anta.cli.console import console
from anta.cli.utils import parse_catalog
from anta.device import AsyncEOSDevice
from anta.models import AntaTest
from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


@click.command(no_args_is_help=True)
@click.pass_context
@click.option(
    "--catalog",
    "-c",
    show_envvar=True,
    help="Path to the tests catalog YAML file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, resolve_path=True),
    required=True,
    callback=parse_catalog,
)
def catalog(ctx: click.Context, catalog: list[tuple[AntaTest, AntaTest.Input]]) -> None:
    """
    Check that the catalog is valid
    """
    logger.info(f"Checking syntax of catalog {ctx.obj['catalog_path']}")
    mock_device = AsyncEOSDevice(name="mock", host="127.0.0.1", username="mock", password="mock")
    manager = ResultManager()
    # Instantiate each test to verify the Inputs are correct
    for test_class, test_inputs in catalog:
        # TODO - this is the same code with typing as in runner.py but somehow mypy complains that test_class
        # ot type AntaTest is not callable
        test_instance = test_class(device=mock_device, inputs=test_inputs)  # type: ignore[operator]
        manager.add_test_result(test_instance.result)
    if manager.error_status:
        console.print(f"[bold][red]Catalog {ctx.obj['catalog_path']} is invalid")
        # TODO print nice report
        ctx.exit(1)
    else:
        console.print(f"[bold][green]Catalog {ctx.obj['catalog_path']} is valid")
