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
import sys
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
USERNAME = "admin"
PASSWORD = "admin"
CATALOG_PATH = Path("/tmp/anta_catalog.yml")
INVENTORY_PATH = Path("/tmp/anta_inventory.yml")

# Load catalog file
try:
    catalog = AntaCatalog.parse(CATALOG_PATH)
except Exception:
    LOGGER.exception("[bold magenta][ANTA RUNNER SCRIPT][/] Catalog failed to load!")
    sys.exit(1)
LOGGER.info("[bold magenta][ANTA RUNNER SCRIPT][/] Catalog loaded!")

# Load inventory
try:
    inventory = AntaInventory.parse(INVENTORY_PATH, username=USERNAME, password=PASSWORD)
except Exception:
    LOGGER.exception("[bold magenta][ANTA RUNNER SCRIPT][/] Inventory failed to load!")
    sys.exit(1)
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
for test_result in manager.results:
    LOGGER.info("[bold magenta][ANTA RUNNER SCRIPT][/] %s:%s:%s", test_result.name, test_result.test, test_result.result)
