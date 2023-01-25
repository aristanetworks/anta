#!/usr/bin/python
# coding: utf-8 -*-

import asyncio
import logging
import sys

from rich.console import Console
from rich.panel import Panel
from rich import print_json
from rich.pretty import pprint
from yaml import safe_load

from anta.inventory import AntaInventory
from anta.reporter import ReportTable
from anta.inventory.models import DEFAULT_TAG
from anta.loader import parse_catalog
from anta.result_manager import ResultManager
from anta.runner import main
from anta.cli.utils import setup_logging

logger = logging.getLogger(__name__)


def check_run(inventory, catalog, username, password, enable_password, timeout, tags, loglevel):
    console = Console()
    setup_logging(level=loglevel)

    inventory_anta = AntaInventory(
        inventory_file=inventory,
        username=username,
        password=password,
        enable_password=enable_password,
        timeout=timeout
    )
    logger.info(f"Inventory {inventory} loaded")

    ############################################################################
    # Test loader
    ############################################################################

    with open(catalog, "r", encoding="utf8") as file:
        test_catalog_input = safe_load(file)

    tests_catalog = parse_catalog(test_catalog_input)

    ############################################################################
    # Test Execution
    ############################################################################

    logger.info("starting running test on inventory ...")

    tags = (
        tags.split(",") if "," in tags else [tags]
    )

    results = ResultManager()
    asyncio.run(main(results, inventory_anta,
                tests_catalog, tags=tags), debug=False)

    return results


def display_table(console: Console, results: ResultManager, group_by: str = 'none', search: str = None):
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


def display_json(console: Console, results: ResultManager, output_file: str = None):
    console.print(Panel("JSON results of all tests", style="cyan"))
    print_json(results.get_results(output_format="json"))
    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as fout:
            fout.write(results.get_results(output_format="json"))


def display_list(console: Console, results: ResultManager, output_file: str = None):
    console.print(Panel.fit("List results of all tests", style="cyan"))
    pprint(results.get_results(output_format="list"))
    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as fout:
            fout.write(str(results.get_results(output_format="list")))
