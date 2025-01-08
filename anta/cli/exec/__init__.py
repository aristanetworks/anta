# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands to execute various scripts on EOS devices."""

import click

from anta.cli.exec import commands


@click.group("exec")
def _exec() -> None:
    """Commands to execute various scripts on EOS devices."""


_exec.add_command(commands.clear_counters)
_exec.add_command(commands.snapshot)
_exec.add_command(commands.collect_tech_support)
