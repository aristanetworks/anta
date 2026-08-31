#!/usr/bin/env python
# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Generate the example ANTA test catalogs."""

import os
from contextlib import redirect_stdout
from pathlib import Path
from sys import path

from yaml import YAMLError

# Override global path to load anta from pwd instead of any installed version.
path.insert(0, str(Path(__file__).parents[2]))

from anta.catalog import AntaCatalog

examples_path = Path(__file__).parents[2] / "examples"
catalogs = {
    examples_path / "tests.yaml": "anta.tests",
    examples_path / "sa.yml": "anta.tests.advisories",
}


prev = os.environ.get("TERM", "")
os.environ["TERM"] = "dumb"
# imported after TERM is set to act upon rich console.
from anta.cli.get.commands import tests  # noqa: E402

for catalog_path, module in catalogs.items():
    try:
        with catalog_path.open("w") as file:
            file.write("---\n")
            with redirect_stdout(file):
                # Explicit arguments make generation independent of the script's argv.
                tests.main(args=["--module", module], standalone_mode=False)
    except SystemExit:
        pass

    try:
        _ = AntaCatalog.parse(catalog_path)
    except (TypeError, ValueError, YAMLError, OSError) as error:
        msg = f"Failed to parse catalog '{catalog_path}': {error}"
        raise ValueError(msg) from None

os.environ["TERM"] = prev
