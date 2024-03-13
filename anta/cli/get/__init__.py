# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands to get information from or generate inventories."""

import click

from anta.cli.get import commands


@click.group
def get() -> None:
    """Commands to get information from or generate inventories."""


get.add_command(commands.from_cvp)
get.add_command(commands.from_ansible)
get.add_command(commands.inventory)
get.add_command(commands.tags)
