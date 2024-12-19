# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA CLI."""

from __future__ import annotations

import logging
import sys
from typing import Callable

from anta import __DEBUG__

# Note: need to separate this file from _main to be able to fail on the import.
try:
    from ._main import cli

except (ImportError, ModuleNotFoundError) as exc:
    if exc.name == "click":

        def build_cli(exception: Exception) -> Callable[[], None]:
            """Build CLI function using the caught exception."""

            def wrap() -> None:
                """Error message if any CLI dependency is missing."""
                logging.error(
                    "The ANTA command line client could not run because the required "
                    "dependencies were not installed.\nMake sure you've installed "
                    "everything with: pip install 'anta[cli]'"
                )
                if __DEBUG__:
                    logging.debug("The caught exception was: %s", exception)

                sys.exit(1)

            return wrap

        cli = build_cli(exc)
    else:
        # if this is not click re-raise the original Exception
        raise

if __name__ == "__main__":
    cli()
