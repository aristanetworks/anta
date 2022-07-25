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

import argparse
import logging
import pprint
import sys
import itertools
from yaml import safe_load

from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import Pretty, pprint

import anta.loader
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.reporter import ReportTable


FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logging.getLogger('anta.inventory').setLevel(logging.CRITICAL)
logging.getLogger('anta.reporter').setLevel(logging.CRITICAL)


def cli_manager():
    parser = argparse.ArgumentParser(description='ANTA test & demo script')
    parser.add_argument('--inventory', '-i', required=False,
                        default='examples/inventory.yml', help='ANTA Inventory file')

    parser.add_argument('--catalog', '-c', required=False,
                        default='examples/tests_custom.yaml', help='ANTA Tests cagtalog')

    parser.add_argument('--username', '-u', required=False,
                        default='ansible', help='EOS Username')

    parser.add_argument('--password', '-p', required=False,
                        default='ansible', help='EOS Password')

    parser.add_argument('--search_ip', required=False,
                        default=None, help='search result for host')

    parser.add_argument('--search_test', required=False,
                        default=None, help='search result for test')

    parser.add_argument('--verbose', '-v', required=False, action='store_true',
                        help='Set script to verbose mode')

    parser.add_argument('--list', '-l', required=False, action='store_true',
                        help='Display internal data')

    parser.add_argument('--full', required=False, action='store_true',
                        help='Display all test cases results')

    parser.add_argument('--devices', required=False, action='store_true',
                        help='Provides summary of test results per device')

    parser.add_argument('--testcases', required=False, action='store_true',
                        help='Provides summary of test results per test case')

    parser.add_argument('--table', required=False, action='store_true',
                        help='Result represented in tables')

    parser.add_argument('--save', required=False, action='store_true',
                        help='Save result to file')

    parser.add_argument('--save_file', required=False,
                        default='report.txt', help='Generated report file')

    return parser.parse_args()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.info('ANTA program is loaded')
    console = Console()
    cli_options = cli_manager()

    if cli_options.verbose:
        logging.getLogger('anta.inventory').setLevel(logging.DEBUG)
        logging.getLogger('anta.reporter').setLevel(logging.DEBUG)

    logger.info('ANTA testing program started')

    ############################################################################
    # Inventory devices
    ############################################################################

    inventory_anta = AntaInventory(
        inventory_file=cli_options.inventory,
        username=cli_options.username,
        password=cli_options.password,
        timeout=0.5,
        auto_connect=True
    )
    logger.info(f'Inventory {cli_options.inventory} loaded')
    if cli_options.verbose:
        output = Pretty(
            inventory_anta.get_inventory(format_out="list"),
            # expand_all=True,
            max_string=5
        )
        console.print(
            Panel('Current Inventory (active devices only)', style='cyan'))
        console.print(output)

    logger.info('starting running test on devices...')

    ############################################################################
    # Test loader
    ############################################################################

    try:
        with open(cli_options.catalog, 'r', encoding='utf8') as file:
            test_catalog_input = safe_load(file)
    except FileNotFoundError:
        print('Error opening tests_catalog')
        sys.exit(1)

    tests_catalog = anta.loader.parse_catalog(test_catalog_input)

    ############################################################################
    # Test Execution
    ############################################################################

    manager = ResultManager()
    list_tests = []
    for device, test in itertools.product(inventory_anta.get_inventory(), tests_catalog):
        list_tests.append(str(test[0]))
        manager.add_test_result(
            test[0](
                device,
                **test[1]
            )
        )
    list_tests_name = [test[0].__name__ for test in tests_catalog]

    ############################################################################
    # Test Reporting
    ############################################################################

    logger.info('testing done !')
    if cli_options.list:
        console.print(Panel('Raw inventory for active device', style='cyan'))
        pprint(inventory_anta.get_inventory(format_out='list'))
        console.print(Panel('Raw results of all tests', style='cyan'))
        pprint(manager.get_results(output_format="list"))


    if cli_options.table:
        reporter = ReportTable()
        if cli_options.full:
            console.print(reporter.report_all(result_manager=manager,
                          host=cli_options.search_ip, testcase=cli_options.search_test))
        if cli_options.testcases:
            console.print(reporter.report_summary_tests(
                result_manager=manager, testcase=cli_options.search_test))
        if cli_options.devices:
            console.print(reporter.report_summary_hosts(
                result_manager=manager, host=cli_options.search_ip))

    if cli_options.save:
        reporter = ReportTable()
        with open(cli_options.save_file, "wt", encoding="utf-8") as report_file:
            output = reporter.report_summary_hosts(result_manager=manager)
            console = Console(file=report_file)
            console.rule(console.print(output))

            output = reporter.report_summary_tests(result_manager=manager)
            console = Console(file=report_file)
            console.rule(console.print(output))

            output = reporter.report_all(result_manager=manager)
            console = Console(file=report_file)
            console.rule(console.print(output))


    sys.exit(0)
