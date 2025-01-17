# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands to validate configuration files."""

import click

from anta.cli.check import commands


@click.group
def check() -> None:
    """Commands to validate configuration files."""


check.add_command(commands.catalog)
