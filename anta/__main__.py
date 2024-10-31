# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA CLI."""

from __future__ import annotations

import sys
from typing import Callable

# Note: need to separate this file from _main to be able to fail on the import.
from anta import __DEBUG__

try:
    from anta.cli import cli

except ImportError as exc:
    if exc.name == "click":

        def build_cli(exception: Exception) -> Callable[[], None]:
            """Build CLI function using the caught exception."""

            def wrap() -> None:
                """Error message if any CLI dependency is missing."""
                print(
                    "The ANTA command line client could not run because the required "
                    "dependencies were not installed.\nMake sure you've installed "
                    "everything with: pip install 'anta[cli]'"
                )
                if __DEBUG__:
                    print(f"The caught exception was: {exception}")

                sys.exit(1)

            return wrap

        cli = build_cli(exc)
    else:
        # if this is not click re-raise the original Exception
        raise

if __name__ == "__main__":
    cli()
