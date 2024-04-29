# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Example script for ANTA.

usage:

python anta_runner.py
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from anta.catalog import AntaCatalog
from anta.cli.nrfu.utils import anta_progress_bar
from anta.inventory import AntaInventory
from anta.logger import Log, setup_logging
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.runner import main as anta_runner

# setup logging
setup_logging(Log.INFO, Path("/tmp/anta.log"))
LOGGER = logging.getLogger()


# NOTE: The inventory and catalog files are not delivered with this script
USERNAME = "anta"
PASSWORD = "formica"
CATALOG_PATH = Path("/tmp/anta_catalog.yml")
INVENTORY_PATH = Path("/tmp/anta_inventory.yml")

# Load catalog file
catalog = AntaCatalog.parse(CATALOG_PATH)
LOGGER.info("[bold magenta][ANTA RUNNER SCRIPT][/] Catalog loaded!")

# Load inventory
inventory = AntaInventory.parse(INVENTORY_PATH, username=USERNAME, password=PASSWORD)
LOGGER.info("[bold magenta][ANTA RUNNER SCRIPT][/] Inventory loaded!")

# Create result manager object
manager = ResultManager()

# Launch ANTA
LOGGER.info("[bold magenta][ANTA RUNNER SCRIPT][/] Starting ANTA runner...")
with anta_progress_bar() as AntaTest.progress:
    # Set dry_run to True to avoid connecting to the devices
    asyncio.run(anta_runner(manager, inventory, catalog, dry_run=False))

LOGGER.info("[bold magenta][ANTA RUNNER SCRIPT][/] ANTA run completed!")

# Manipulate the test result object

for test in manager.get_tests():
    LOGGER.info(test.name, test.result.status)
