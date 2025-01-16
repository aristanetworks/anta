# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Top-level Console.

https://rich.readthedocs.io/en/stable/console.html#console-api.
"""

from rich.console import Console
from rich.theme import Theme

from anta import RICH_COLOR_THEME

console = Console(theme=Theme(RICH_COLOR_THEME))
