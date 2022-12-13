#!/usr/bin/python
# coding: utf-8 -*-
# pylint: disable=W0622
# pylint: disable=C0116
#
# Copyright 2022 Arista Networks Thomas Grimonet
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http: //www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Internal ANTA Test script - should not be used in a production environment."""

import asyncio
import argparse
import logging
import sys
import itertools
from typing import Callable, List, Tuple, Dict, Any

from yaml import safe_load
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import Pretty, pprint

import anta.loader
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager, TestResult
from anta.reporter import ReportTable


FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logging.getLogger('anta.inventory').setLevel(logging.CRITICAL)
logging.getLogger('anta.result_manager').setLevel(logging.CRITICAL)
logging.getLogger('anta.reporter').setLevel(logging.CRITICAL)
logging.getLogger('anta.tests.configuration').setLevel(logging.ERROR)
logging.getLogger('anta.tests.hardware').setLevel(logging.ERROR)
logging.getLogger('anta.tests.interfaces').setLevel(logging.ERROR)
logging.getLogger('anta.tests.mlag').setLevel(logging.ERROR)
logging.getLogger('anta.tests.multicast').setLevel(logging.ERROR)
logging.getLogger('anta.tests.profiles').setLevel(logging.ERROR)
logging.getLogger('anta.tests.system').setLevel(logging.ERROR)
logging.getLogger('anta.tests.software').setLevel(logging.ERROR)
logging.getLogger('anta.tests.vxlan').setLevel(logging.ERROR)
logging.getLogger('anta.tests.routing.generic').setLevel(logging.ERROR)
logging.getLogger('anta.tests.routing.bgp').setLevel(logging.ERROR)
logging.getLogger('anta.tests.routing.ospf').setLevel(logging.ERROR)


async def main(manager: ResultManager, inventory: AntaInventory, tests: List[Tuple[Callable[..., TestResult], Dict[Any, Any]]]) -> None:
    await inventory.connect_inventory()
    res = await asyncio.gather(*(test[0](device, **test[1]) for device, test in itertools.product(inventory.get_inventory(), tests)), return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            logger.error(f"Error when running tests: {r.__class__.__name__}: {r}")
    manager.add_test_results(res)


def cli_manager() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='ANTA test & demo script')

    #############################
    # ANTA options

    parser.add_argument('--inventory', '-i', required=False,
                        default='examples/inventory.yml', help='ANTA Inventory file')

    parser.add_argument('--catalog', '-c', required=False,
                        default='examples/tests_custom.yaml', help='ANTA Tests cagtalog')

    #############################
    # Device connectivity

    parser.add_argument('--username', '-u', required=False,
                        default='ansible', help='EOS Username')

    parser.add_argument('--password', '-p', required=False,
                        default='ansible', help='EOS Password')

    parser.add_argument('--enable_password', '-e', required=False,
                        default='ansible', help='EOS Enable Password')

    parser.add_argument('--timeout', required=False,
                        default=0.5, help='eAPI connection timeout')

    #############################
    # Search options

    parser.add_argument('--search_host', '--host', required=False,
                        default=None, help='search result for host')

    parser.add_argument('--search_test', '--test', required=False,
                        default=None, help='search result for test')

    #############################
    # Display content using PPRINT

    parser.add_argument('--list', '-l', required=False, action='store_true',
                        help='Display internal data')

    #############################
    # Options for table report

    parser.add_argument('--table', required=False, action='store_true',
                        help='Result represented in tables')

    # List of all tests per device -- REQUIRE --table option
    parser.add_argument('--full', required=False, action='store_true',
                        help='Display all test cases results')

    # Summary of tests results per device -- REQUIRE --table option
    parser.add_argument('--devices', required=False, action='store_true',
                        help='Provides summary of test results per device')

    # Summary of tests results per test-case -- REQUIRE --table option
    parser.add_argument('--testcases', required=False, action='store_true',
                        help='Provides summary of test results per test case')

    #############################
    # Options to save reports

    parser.add_argument('--save', required=False, action='store_true',
                        help='Save result to file')

    parser.add_argument('--save_file', required=False,
                        default='report.txt', help='Generated report file')

    #############################
    # Verbosity management.
    # If enable, print all logs in debug (including from modules)

    parser.add_argument('--verbose', '-v', required=False, action='store_true',
                        help='Set script to verbose mode (INFO)')

    parser.add_argument('--very-verbose', '-vv', required=False, action='store_true',
                        help='Set script to very verbose mode (DEBUG)')

    parser.add_argument('--verbose-test', '-vt', required=False, action='store_true',
                        help='Set script to be in verbose mode for anta.tests only (DEBUG)')

    return parser.parse_args()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.info('ANTA program is loaded')
    console = Console()
    cli_options = cli_manager()

    if cli_options.verbose:
        logging.getLogger('anta.inventory').setLevel(logging.INFO)
        logging.getLogger('anta.result_manager').setLevel(logging.INFO)
        logging.getLogger('anta.reporter').setLevel(logging.INFO)
    elif cli_options.very_verbose:
        logging.getLogger('anta.inventory').setLevel(logging.DEBUG)
        logging.getLogger('anta.result_manager').setLevel(logging.DEBUG)
        logging.getLogger('anta.reporter').setLevel(logging.DEBUG)

    if cli_options.verbose_test:
        logging.getLogger('anta.tests.hardware').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.interfaces').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.mlag').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.multicast').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.profiles').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.system').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.software').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.vxlan').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.routing.generic').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.routing.bgp').setLevel(logging.DEBUG)
        logging.getLogger('anta.tests.routing.ospf').setLevel(logging.DEBUG)

    if cli_options.verbose or cli_options.verbose_test:
        console.print(Panel('Active logger for testing', style='orange3'))
        # pylint: disable=E1101
        loggers = [logging.getLogger(name)
                   for name in logging.root.manager.loggerDict]
        pprint(loggers)

    logger.info('ANTA testing program started')

    ############################################################################
    # Inventory devices
    ############################################################################

    inventory_anta = AntaInventory(
        inventory_file=cli_options.inventory,
        username=cli_options.username,
        password=cli_options.password,
        enable_password=cli_options.enable_password,
        timeout=0.5,
        filter_hosts=cli_options.search_host
        )
    logger.info(f'Inventory {cli_options.inventory} loaded')
    if cli_options.verbose:
        output = Pretty(
            inventory_anta.get_inventory(format_out="list"),
        )
        console.print(
            Panel('Current Inventory (active devices only)', style='cyan'))
        console.print(output)

    if cli_options.search_host is not None:
        logger.info(f'starting running test on device {cli_options.search_host} ...')
    else:
        logger.info('starting running test on devices ...')

    ############################################################################
    # Test loader
    ############################################################################

    with open(cli_options.catalog, 'r', encoding='utf8') as file:
        test_catalog_input = safe_load(file)

    tests_catalog = anta.loader.parse_catalog(test_catalog_input)

    ############################################################################
    # Test Execution
    ############################################################################

    if cli_options.search_test:
        all_tests = tests_catalog
        tests_catalog = []
        for test in all_tests:
            if test[0].__name__ == cli_options.search_test:
                tests_catalog = [test]

    results = ResultManager()
    asyncio.run(main(results, inventory_anta, tests_catalog), debug=False)

    ############################################################################
    # Test Reporting
    ############################################################################

    logger.info('testing done !')
    if cli_options.list:
        console.print(Panel('Raw inventory for active device', style='cyan'))
        pprint(inventory_anta.get_inventory(format_out='list'))
        console.print(Panel('Raw results of all tests', style='cyan'))
        pprint(results.get_results(output_format="list"))

    if cli_options.table:
        reporter = ReportTable()
        if cli_options.full:
            console.print(reporter.report_all(result_manager=results,
                          host=cli_options.search_ip, testcase=cli_options.search_test))
        if cli_options.testcases:
            console.print(reporter.report_summary_tests(
                result_manager=results, testcase=cli_options.search_test))
        if cli_options.devices:
            console.print(reporter.report_summary_hosts(
                result_manager=results, host=cli_options.search_ip))

    if cli_options.save:
        reporter = ReportTable()
        with open(cli_options.save_file, "wt", encoding="utf-8") as report_file:
            output = reporter.report_summary_hosts(result_manager=results)
            console = Console(file=report_file)
            console.rule(console.print(output))

            output = reporter.report_summary_tests(result_manager=results)
            console = Console(file=report_file)
            console.rule(console.print(output))

            output = reporter.report_all(result_manager=results)
            console = Console(file=report_file)
            console.rule(console.print(output))

    sys.exit(0)
