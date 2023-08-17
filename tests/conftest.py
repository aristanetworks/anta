# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
conftest.py - used to store anta specific fixtures used for tests
"""

import logging

# Load fixtures from dedicated file tests/lib/fixture.py
pytest_plugins = [
    "tests.lib.fixture",
]

# Placeholder to disable logging of some external libs
for _ in ("asyncio", "httpx"):
    logging.getLogger(_).setLevel(logging.CRITICAL)
