#!/usr/bin/python
# coding: utf-8 -*-

import logging
import click

from rich.console import Console
from rich.panel import Panel

from anta.reporter import ReportTable
from anta.cli.cli import anta as anta
from .utils import check_run

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
@click.option('--inventory', '-i', show_envvar=True, prompt='Inventory path', help='Path to your inventory file', type=click.Path())
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=click.Path())
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator', type=str)
@click.option('--search', default=None, help='Value to search in result', type=str)
@click.option('--group-by', default='none', type=click.Choice(['none', 'host', 'test'], case_sensitive=False),help='Group result by test or host. default no grouping')
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def check(ctx, inventory, catalog, tags, group_by, search, log_level):
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

    reporter = ReportTable()
    if group_by == 'none':
        console.print(
            reporter.report_all(result_manager=results)
        )
    elif group_by == 'host':
        console.print(
            reporter.report_summary_hosts(
                result_manager=results,
                host=search
            )
        )
    elif group_by == 'test':
        console.print(
            reporter.report_summary_tests(
                result_manager=results, testcase=search
            )
        )
