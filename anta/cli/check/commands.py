#!/usr/bin/python
# coding: utf-8 -*-

import logging
import click

from rich.console import Console
from rich.panel import Panel

from anta.reporter import ReportTable
from anta.cli.cli import anta as anta
from .utils import check_run, display_table, display_json, display_list

logger = logging.getLogger(__name__)

# Command to run live check of the network and provides a human readable ouput.
# Not to be used in a CI pipeline.
#
# Usage:
#
# Usage: cli.py check [OPTIONS]
#
# ANTA command to check network states
#
# Options:
#   -i, --inventory PATH            Path to your inventory file[env var:
#                                                               ANTA_CHECK_INVENTORY]
#   -c, --catalog PATH              Path for tests catalog[env var:
#                                                          ANTA_CHECK_CATALOG]
#   -t, --tags TEXT                 List of tags
#   --search TEXT                   Value to search in result
#   --group-by[none | host | test]
#   --log-level, --log[debug | info | warning | critical]
#   --help                          Show this message and exit.
#
# Example:
#
# python anta/cli/cli.py check --tags spine --group-by host --search clab-fabric-avd-spine1:443 --log critical
# ╭────────────────────────────────────────────────────────── Settings ──────────────────────────────────────────────────────────╮
# │ Running check-devices with:                                                                                                  │
# │               - Inventory: /home/tom/Projects/arista/ansible-arista-network-lab-automation/network-tests/anta-inventory.yml  │
# │               - Tests catalog: /home/tom/Projects/arista/ansible-arista-network-lab-automation/network-tests/tests-bases.yml │
# ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
#                                                                                                         Summary per host
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Host IP                    ┃ # of success ┃ # of skipped ┃ # of failure ┃ # of errors ┃ List of failed ortest case                                                                                                            ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ clab-fabric-avd-spine1:443 │ 17           │ 9            │ 5            │ 0           │ ['verify_interface_errors', 'verify_interface_discards', 'verify_interfaces_status', 'verify_vxlan', 'verify_bgp_ipv4_unicast_count'] │
# └────────────────────────────┴──────────────┴──────────────┴──────────────┴─────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
#
#

@anta.command()
@click.pass_context
# Generic options
@click.option('--inventory', '-i', show_envvar=True, prompt='Inventory path', help='Path to your inventory file', type=click.Path())
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=click.Path())
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
@click.option('--display', default='table', type=click.Choice(['table', 'json', 'list'], case_sensitive=False), help='output format selection. default is table')
# Options valid with --display table
@click.option('--search', default=None, help='Value to search in result. Can be test name or host name', type=str)
@click.option('--group-by', default='none', type=click.Choice(['none', 'host', 'test'], case_sensitive=False),help='Group result by test or host. default none')
# Options valid with --display json
@click.option('--output', '-o', default=None, help='Path to save output in json or list', type=click.Path())
# Debug stuf
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def check(ctx, inventory, catalog, display, tags, group_by, search, output, log_level):
    """ANTA command to check network states"""
    console = Console()

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(
        inventory=inventory,
        catalog=catalog,
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        timeout=ctx.obj['timeout'],
        enable_password='unset',
        tags=tags,
        loglevel=log_level
    )
    if display == 'table':
        display_table(console=console, results=results, group_by=group_by, search=search)
    elif display == 'json':
        display_json(console=console, results=results, output_file=output)
    elif display == 'list':
        display_list(console=console, results=results, output_file=output)
