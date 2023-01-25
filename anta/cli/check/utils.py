#!/usr/bin/python
# coding: utf-8 -*-

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