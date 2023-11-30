# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
import click

from anta.cli.exec import commands


@click.group
def exec() -> None:
    """Execute commands to inventory devices"""


exec.add_command(commands.clear_counters)
exec.add_command(commands.snapshot)
exec.add_command(commands.collect_tech_support)
