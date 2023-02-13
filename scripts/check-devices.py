#!/usr/bin/env python3
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
import asyncio
import logging
import sys

from rich import print_json
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import pprint
from yaml import safe_load

from anta.inventory import AntaInventory
from anta.inventory.models import DEFAULT_TAG
from anta.loader import parse_catalog
from anta.reporter import ReportTable
from anta.result_manager import ResultManager
from anta.runner import main as runner_main

logger = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    """
    Configure logging for check-devices execution

    Helpers to set logging for
    * anta.inventory
    * anta.result_manager
    * check-devices

    By default, configure INFO for the script,
    WARNING for anta.inventory and anta.report_manager
    and CRITICAL for others

    Args:
        level (str): level name to configure.
    """

    if level is not None:
        loglevel = getattr(logging, level.upper())
    else:
        loglevel = getattr(logging, 'WARNING')

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=loglevel, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
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

    logger.setLevel(loglevel)

    # Set default logging
    if level is None:
        logger.setLevel(logging.INFO)


def cli_manager() -> argparse.Namespace:
    """
    Define CLI arguments and options
    """
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
        default=10,
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
        help="Provide logging level. Example --loglevel debug, By default INFO only for the script, others are configured to WARNING and CRITICAL",
    )

    return parser.parse_args()


def main() -> None:
    """main"""
    console = Console()
    cli_options = cli_manager()
    setup_logging(level=cli_options.loglevel)

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
        timeout=cli_options.timeout,
    )
    logger.info(f"Inventory {cli_options.inventory} loaded")

    ############################################################################
    # Test loader
    ############################################################################

    with open(cli_options.catalog, "r", encoding="utf8") as file:
        test_catalog_input = safe_load(file)

    tests_catalog = parse_catalog(test_catalog_input)

    ############################################################################
    # Test Execution
    ############################################################################

    logger.info("starting running test on inventory ...")

    tags = (
        cli_options.tags.split(",") if "," in cli_options.tags else [cli_options.tags]
    )

    results = ResultManager()
    asyncio.run(
        runner_main(results, inventory_anta, tests_catalog, tags=tags), debug=False
    )

    ############################################################################
    # Test Reporting
    ############################################################################

    logger.info("testing done !")
    if cli_options.list:
        console.print(Panel.fit("List results of all tests", style="cyan"))
        pprint(results.get_results(output_format="list"))
        if cli_options.save is not None:
            with open(cli_options.save, "w", encoding="utf-8") as fout:
                fout.write(str(results.get_results(output_format="list")))

    if cli_options.json:
        console.print(Panel("JSON results of all tests", style="cyan"))
        print_json(results.get_results(output_format="json"))
        if cli_options.save is not None:
            with open(cli_options.save, "w", encoding="utf-8") as fout:
                fout.write(results.get_results(output_format="json"))

    if cli_options.table:
        reporter = ReportTable()
        if cli_options.all_results or (
            not cli_options.by_test and not cli_options.by_host
        ):
            console.print(
                reporter.report_all(
                    result_manager=results,
                    host=cli_options.hostip,
                    testcase=cli_options.test,
                )
            )

        # To print only report per Test case
        if cli_options.by_test:
            console.print(
                reporter.report_summary_tests(
                    result_manager=results, testcase=cli_options.test
                )
            )

        # To print only report per Device
        if cli_options.by_host:
            console.print(
                reporter.report_summary_hosts(
                    result_manager=results, host=cli_options.hostip
                )
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
