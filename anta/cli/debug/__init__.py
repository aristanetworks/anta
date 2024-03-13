# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands to execute EOS commands on remote devices."""

import click

from anta.cli.debug import commands


@click.group
def debug() -> None:
    """Commands to execute EOS commands on remote devices."""


debug.add_command(commands.run_cmd)
debug.add_command(commands.run_template)
