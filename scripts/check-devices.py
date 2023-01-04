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

"""
Arista NRFU test runner script
"""

import argparse
import itertools
import logging
import sys
from typing import Any

from rich import print_json
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import pprint
from yaml import safe_load

import anta.loader
from anta.inventory import AntaInventory
from anta.inventory.models import DEFAULT_TAG
from anta.reporter import ReportTable
from anta.result_manager import ResultManager


def setup_logging(level: str = "critical") -> Any:
    """
    Configure logging for check-devices execution

    Helpers to set logging for
    * anta.inventory
    * anta.result_manager
    * check-devices

    Args:
        level (str, optional): level name to configure. Defaults to 'critical'.

    Returns:
        logging: Logger for script
    """
    loglevel = getattr(logging, level.upper())

    # FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logging.getLogger("anta.inventory").setLevel(loglevel)
    logging.getLogger("anta.result_manager").setLevel(loglevel)

    logging.getLogger("anta.reporter").setLevel(logging.CRITICAL)
    logging.getLogger("anta.tests").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.configuration").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.hardware").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.interfaces").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.mlag").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.multicast").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.profiles").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.system").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.software").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.vxlan").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.routing.generic").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.routing.bgp").setLevel(logging.ERROR)
    logging.getLogger("anta.tests.routing.ospf").setLevel(logging.ERROR)

    # pylint: disable=W0621
    logger = logging.getLogger(__name__)
    logger.setLevel(loglevel)
    return logger


def cli_manager() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Arista NRFU runner")

    #############################
    # ANTA options

    parser.add_argument(
        "--inventory",
        "-i",
        required=False,
        default="examples/inventory.yml",
        help="ANTA Inventory file",
    )

    parser.add_argument(
        "--catalog",
        "-c",
        required=False,
        default="examples/tests_custom.yaml",
        help="ANTA Tests catalog",
    )

    #############################
    # Device connectivity

    parser.add_argument(
        "--username", "-u", required=False, default="ansible", help="EOS Username"
    )

    parser.add_argument(
        "--password", "-p", required=False, default="ansible", help="EOS Password"
    )

    parser.add_argument(
        "--enable_password",
        "-e",
        required=False,
        default="ansible",
        help="EOS Enable Password",
    )

    parser.add_argument(
        "--timeout",
        "-t",
        required=False,
        type=float,
        default=1,
        help="eAPI connection timeout",
    )

    #############################
    # Search options

    parser.add_argument(
        "--hostip", required=False, default=None, help="search result for host"
    )

    parser.add_argument(
        "--test", required=False, default=None, help="search result for test"
    )

    parser.add_argument(
        "--tags",
        required=False,
        default=DEFAULT_TAG,
        help="List of device tags to limit scope of testing",
    )

    #############################
    # Display Options

    parser.add_argument(
        "--list", required=False, action="store_true", help="Display internal data"
    )

    parser.add_argument(
        "--json",
        required=False,
        action="store_true",
        help="Display data in json format",
    )

    # Display result using a table (default is TRUE)
    parser.add_argument(
        "--table",
        required=False,
        action="store_true",
        help="Result represented in tables",
    )

    #############################
    # Options for saving outputs
    parser.add_argument(
        "--save",
        required=False,
        default=None,
        help="Save output to file. Only valid for --list and --json",
    )

    #############################
    # Options for table report

    # List of all tests per device -- REQUIRE --table option
    parser.add_argument(
        "--all-results",
        required=False,
        action="store_true",
        help="Display all test cases results. Default table view (Only valid with --table)",
    )

    # Summary of tests results per device -- REQUIRE --table option
    parser.add_argument(
        "--by-host",
        required=False,
        action="store_true",
        help="Provides summary of test results per device (Only valid with --table)",
    )

    # Summary of tests results per test-case -- REQUIRE --table option
    parser.add_argument(
        "--by-test",
        required=False,
        action="store_true",
        help="Provides summary of test results per test case (Only valid with --table)",
    )

    # Logging option

    parser.add_argument(
        "-log",
        "--loglevel",
        default="critical",
        help="Provide logging level. Example --loglevel debug, default=critical",
    )

    return parser.parse_args()


if __name__ == "__main__":
    console = Console()
    cli_options = cli_manager()
    logger = setup_logging(level=cli_options.loglevel)

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {cli_options.inventory}\n\
              - Tests catalog: {cli_options.catalog}",
            title="[green]Settings",
        )
    )

    inventory_anta = AntaInventory(
        inventory_file=cli_options.inventory,
        username=cli_options.username,
        password=cli_options.password,
        enable_password=cli_options.enable_password,
        timeout=cli_options.timeout
    )

    scope_tags = (
        cli_options.tags.split(",") if "," in cli_options.tags else [cli_options.tags]
    )

    ############################################################################
    # Test loader
    ############################################################################

    with open(cli_options.catalog, "r", encoding="utf8") as file:
        test_catalog_input = safe_load(file)

    tests_catalog = anta.loader.parse_catalog(test_catalog_input)
    logger.info(f"Inventory {cli_options.inventory} loaded")

    ############################################################################
    # Test Execution
    ############################################################################

    logger.info("starting running test on inventory ...")
    manager = ResultManager()
    list_tests = []
    for device, test in itertools.product(
        inventory_anta.get_inventory(tags=scope_tags), tests_catalog
    ):
        if (cli_options.hostip is None or cli_options.hostip == str(device.host)) and (
            cli_options.test is None or cli_options.test == str(test[0].__name__)
        ):
            list_tests.append(str(test[0]))
            manager.add_test_result(test[0](device, **test[1]))

    ############################################################################
    # Test Reporting
    ############################################################################

    logger.info("testing done !")
    if cli_options.list:
        console.print(Panel.fit("List results of all tests", style="cyan"))
        pprint(manager.get_results(output_format="list"))
        if cli_options.save is not None:
            with open(cli_options.save, "w", encoding="utf-8") as fout:
                fout.write(str(manager.get_results(output_format="list")))

    if cli_options.json:
        console.print(Panel("JSON results of all tests", style="cyan"))
        print_json(manager.get_results(output_format="json"))
        if cli_options.save is not None:
            with open(cli_options.save, "w", encoding="utf-8") as fout:
                fout.write(manager.get_results(output_format="json"))

    if cli_options.table:
        reporter = ReportTable()
        if cli_options.all_results or (
            not cli_options.by_test and not cli_options.by_host
        ):
            console.print(
                reporter.report_all(
                    result_manager=manager,
                    host=cli_options.hostip,
                    testcase=cli_options.test,
                )
            )

        # To print only report per Test case
        if cli_options.by_test:
            console.print(
                reporter.report_summary_tests(
                    result_manager=manager, testcase=cli_options.test
                )
            )

        # To print only report per Device
        if cli_options.by_host:
            console.print(
                reporter.report_summary_hosts(
                    result_manager=manager, host=cli_options.hostip
                )
            )

    sys.exit(0)
