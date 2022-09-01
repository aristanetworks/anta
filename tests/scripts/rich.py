#!/usr/bin/python
# coding: utf-8 -*-
"""
rich.py test
"""

import argparse
import logging
import sys
import itertools
from typing import List, Union
from yaml import safe_load

# rich is not nice as it does not expose most of its module in __init__.py
# from rich import print
from rich.console import Console  # pylint: disable=E0401
from rich.logging import RichHandler  # pylint: disable=E0401
from rich.panel import Panel  # pylint: disable=E0401,E0611
from rich.pretty import Pretty, pprint  # pylint: disable=E0401,E0611
from rich.style import Style  # pylint: disable=E0401,E0611
from rich.table import Table  # pylint: disable=E0401,E0611
from rich.text import Text  # pylint: disable=E0401,E0611
from rich.tree import Tree  # pylint: disable=E0401,E0611

import anta.loader
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.reporter import ReportTable


# logging.basicConfig(level=logging.DEBUG)
# logging.disable(sys.maxsize)
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logging.getLogger("anta.inventory").setLevel(logging.CRITICAL)
logging.getLogger("anta.reporter").setLevel(logging.CRITICAL)

STYLE_FAILURE = Style(color="orange3", bold=False)
STYLE_ERROR = Style(color="red3", bold=False)
STYLE_SUCCESS = Style(color="green")


class TestInputError(Exception):
    """Error raised when inventory root key is not found."""


def list_to_txt_list(usr_list: List[str], delimiter: str = "*") -> str:
    """
    Returns the inout list as a string
    """
    result = ""
    for line in usr_list:
        result = (
            f"{result}\n{delimiter} {line}" if result != "" else f"{delimiter} {line}"
        )
    return result


def color_result(result: str, output_type: str = "Text") -> Union[str, Text]:
    """
    Color the result based on the the output_type
    """
    if output_type == "str":
        if result == "success":
            return f"[green]{result}"
        if result == "failure":
            return f"[orange3]{result}"
        if result == "error":
            return f"[red3]{result}"
    # Default
    if result == "success":
        return Text(result, style=STYLE_SUCCESS)
    if result == "failure":
        return Text(result, style=STYLE_FAILURE)
    if result == "error":
        return Text(result, style=STYLE_ERROR)

    # Making the implicit return explicit for now to avoid mypy and pylint complaints
    # otherwise would need pylint: disable=R1710
    # TODO - make the method have a proper "default case"
    return f"[green]{result}"


def tree_report(inventory_anta: AntaInventory) -> None:
    """
    tree report
    """
    tree = Tree("Test Result by Host")
    for device in inventory_anta.get_inventory(format_out="list"):
        # Need to ignore type here because of the union type of get_inventory
        host = str(device.host)  # type: ignore
        results = manager.get_result_by_host(host, output_format="list")
        test_tree = tree.add(host)
        for result in results:
            message_tree = test_tree.add(
                f'{result.test}: {color_result(result=result.result,output_type="str")}'
            )
            if len(result.messages):
                for message in result.messages:
                    message_tree.add(f"{message}")
    console.print(tree)


def report(inventory_anta: AntaInventory, testcases: List[str]) -> None:
    """
    report
    """
    # Report all test results
    # console.print('ANTA Reporting\n\n')
    table = Table(title="All tests results")

    table.add_column("Test name", justify="left", style="cyan", no_wrap=True)
    table.add_column("Device IP", justify="left")
    table.add_column("Test Result", justify="right")
    table.add_column("Failure reason", justify="left")
    for result in manager.get_results(output_format="list"):
        state = color_result(result=str(result.result), output_type="str")
        message = (
            list_to_txt_list(result.messages) if len(result.messages) > 0 else "N/A"
        )
        table.add_row(result.test, str(result.host), state, message)
    console.print(table)

    # Aggregated result per test
    table = Table(title="Aggregated results per test case")

    table.add_column("Test name", justify="left", style="cyan", no_wrap=True)
    table.add_column("Number of success", justify="center", style="green")
    table.add_column("Number of failure", justify="center", style="orange3")
    table.add_column("List of failure IP", justify="left")

    for testcase in testcases:
        results = manager.get_result_by_test(testcase)
        # pprint(results)
        nb_failure = len([result for result in results if result.result == "failure"])
        list_failure = [
            str(result.host) for result in results if result.result == "failure"
        ]
        nb_success = len([result for result in results if result.result == "success"])
        table.add_row(testcase, str(nb_success), str(nb_failure), str(list_failure))
    console.print(table)

    # Aggregated result per device
    table = Table(title="Aggregated results per device")

    table.add_column("Device IP", justify="left", style="cyan", no_wrap=True)
    table.add_column("Number of success", justify="center", style="green")
    table.add_column("Number of failure", justify="center", style="orange3")
    table.add_column("List of failing tests", justify="left")

    for device in inventory_anta.get_inventory(format_out="list"):
        # Need to ignore type here because of the union type of get_inventory
        host = str(device.host)  # type: ignore
        results = manager.get_result_by_host(host, output_format="list")
        nb_failure = len([result for result in results if result.result == "failure"])
        list_failure = [
            str(result.test) for result in results if result.result == "failure"
        ]
        nb_success = len([result for result in results if result.result == "success"])
        table.add_row(host, str(nb_success), str(nb_failure), str(list_failure))
    console.print(table)


def cli_manager() -> argparse.Namespace:
    """
    cli manager
    """
    parser = argparse.ArgumentParser(description="ANTA test & demo script")
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
        help="ANTA Tests cagtalog",
    )

    parser.add_argument(
        "--username", "-u", required=False, default="ansible", help="EOS Username"
    )

    parser.add_argument(
        "--password", "-p", required=False, default="ansible", help="EOS Password"
    )

    parser.add_argument(
        "--search", "-s", required=False, default=None, help="search result for host"
    )

    parser.add_argument(
        "--search_test",
        "-st",
        required=False,
        default=None,
        help="search result for test",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        required=False,
        action="store_true",
        help="Set script to verbose mode",
    )

    parser.add_argument(
        "--list",
        "-l",
        required=False,
        action="store_true",
        help="Display internal data",
    )

    parser.add_argument(
        "--full",
        "-f",
        required=False,
        action="store_true",
        help="Display all test cases results",
    )

    parser.add_argument(
        "--devices",
        "-d",
        required=False,
        action="store_true",
        help="Provides summary of test results per device",
    )

    parser.add_argument(
        "--testcases",
        required=False,
        action="store_true",
        help="Provides summary of test results per test case",
    )

    parser.add_argument(
        "--table",
        required=False,
        action="store_true",
        help="Result represented in tables",
    )

    parser.add_argument(
        "--save", required=False, action="store_true", help="Save result to file"
    )

    parser.add_argument(
        "--old_report",
        required=False,
        action="store_true",
        help="Use builtin report (not maintained anymore)",
    )

    parser.add_argument(
        "--tree",
        required=False,
        action="store_true",
        help="Result represented in a tree",
    )

    return parser.parse_args()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("ANTA program is loaded")
    console = Console()
    cli_options = cli_manager()

    if cli_options.verbose:
        logging.getLogger("anta.inventory").setLevel(logging.DEBUG)
        logging.getLogger("anta.reporter").setLevel(logging.DEBUG)

    logger.info("ANTA testing program started")

    ############################################################################
    # Inventory devices
    ############################################################################

    inventory = AntaInventory(
        inventory_file=cli_options.inventory,
        username=cli_options.username,
        password=cli_options.password,
        timeout=0.5,
        auto_connect=True,
    )
    logger.info(f"Inventory {cli_options.inventory} loaded")
    if cli_options.verbose:
        output = Pretty(
            inventory.get_inventory(format_out="list"),
            # expand_all=True,
            max_string=5,
        )
        console.print(Panel("Current Inventory (active devices only)", style="cyan"))
        console.print(output)

    logger.info("starting running test on devices...")

    ############################################################################
    # Test loader
    ############################################################################

    try:
        with open(cli_options.catalog, "r", encoding="utf8") as file:
            test_catalog_input = safe_load(file)
    except FileNotFoundError:
        print("Error opening tests_catalog")
        sys.exit(1)

    tests_catalog = anta.loader.parse_catalog(test_catalog_input)

    ############################################################################
    # Test Execution
    ############################################################################

    manager = ResultManager()
    list_tests = []
    for device_name, test in itertools.product(
        inventory.get_inventory(), tests_catalog
    ):
        list_tests.append(str(test[0]))
        manager.add_test_result(test[0](device_name, **test[1]))
    list_tests_name = [test[0].__name__ for test in tests_catalog]

    ############################################################################
    # Test Reporting
    ############################################################################

    logger.info("testing done !")
    if cli_options.list:
        console.print(Panel("Raw results of all tests", style="cyan"))
        pprint(manager.get_results(output_format="list"))

    if cli_options.old_report:
        report(inventory_anta=inventory, testcases=list_tests_name)

    if cli_options.table:
        reporter = ReportTable()
        if cli_options.full:
            console.print(
                reporter.report_all(
                    result_manager=manager,
                    host=cli_options.search,
                    testcase=cli_options.search_test,
                )
            )
        if cli_options.testcases:
            console.print(
                reporter.report_summary_tests(
                    result_manager=manager, testcase=cli_options.search_test
                )
            )
        if cli_options.devices:
            console.print(
                reporter.report_summary_hosts(
                    result_manager=manager, host=cli_options.search
                )
            )

    if cli_options.save:
        reporter = ReportTable()
        with open("report.txt", "wt", encoding="utf-8") as report_file:
            output = reporter.report_summary_hosts(result_manager=manager)
            console = Console(file=report_file)
            console.rule(console.print(output))

            output = reporter.report_summary_tests(result_manager=manager)
            console = Console(file=report_file)
            console.rule(console.print(output))

            output = reporter.report_all(result_manager=manager)
            console = Console(file=report_file)
            console.rule(console.print(output))

    if cli_options.tree:
        tree_report(inventory_anta=inventory)

    sys.exit(0)
