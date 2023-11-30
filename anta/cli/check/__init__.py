# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

import click

from anta.cli.check import commands


@click.group
def check() -> None:
    """Check commands for building ANTA"""


check.add_command(commands.catalog)
