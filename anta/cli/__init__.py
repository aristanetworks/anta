# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA CLI."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from anta import __DEBUG__

if TYPE_CHECKING:
    from collections.abc import Callable

# Note: need to separate this file from _main to be able to fail on the import.
try:
    from ._main import anta, cli

except ImportError as exc:

    def build_cli(exception: ImportError) -> Callable[[], None]:
        """Build CLI function using the caught exception."""

        def wrap() -> None:
            """Error message if any CLI dependency is missing."""
            if not exception.name or "click" not in exception.name:
                raise exception

            msg = (
                "The ANTA command line client could not run because the required "
                "dependencies were not installed.\nMake sure you've installed "
                "everything with: pip install 'anta[cli]'"
            )
            print(msg)
            if __DEBUG__:
                print(f"The caught exception was: {exception}")

            sys.exit(1)

        return wrap

    cli = build_cli(exc)

__all__ = ["anta", "cli"]

if __name__ == "__main__":
    cli()
