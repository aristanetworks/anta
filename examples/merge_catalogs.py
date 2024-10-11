# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Script that merge a collection of catalogs into one AntaCatalog."""
from pathlib import Path

from anta.catalog import AntaCatalog
from anta.models import AntaTest

CATALOG_SUFFIX = "-catalog.yml"
CATALOG_DIR = "intended/test_catalogs/"

if __name__ == "__main__":
    catalogs = []
    for file in Path(CATALOG_DIR).glob("*" + CATALOG_SUFFIX):
        device = str(file).removesuffix(CATALOG_SUFFIX).removeprefix(CATALOG_DIR)
        print(f"Loading test catalog for device {device}")
        catalog = AntaCatalog.parse(file)
        # Add the device name as a tag to all tests in the catalog
        for test in catalog.tests:
            test.inputs.filters = AntaTest.Input.Filters(tags={device})
        catalogs.append(catalog)

    # Merge all catalogs
    merged_catalog = AntaCatalog.merge_catalogs(catalogs)

    # Save the merged catalog to a file
    with Path("anta-catalog.yml").open("w") as f:
        f.write(merged_catalog.dump().yaml())
