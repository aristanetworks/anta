#!/usr/bin/env python
# coding: utf-8 -*-
"""
ANTA Top-level Console
https://rich.readthedocs.io/en/stable/console.html#console-api
"""

from rich.console import Console
from rich.theme import Theme

from anta import RICH_COLOR_THEME

console = Console(theme=Theme(RICH_COLOR_THEME))
