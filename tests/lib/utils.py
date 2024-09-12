# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""tests.lib.utils."""

from __future__ import annotations

from typing import Any


def generate_test_ids_dict(val: dict[str, Any], key: str = "name") -> str:
    """generate_test_ids Helper to generate test ID for parametrize."""
    return val.get(key, "unamed_test")


def generate_test_ids(data: list[dict[str, Any]]) -> list[str]:
    """Build id for a unit test of an AntaTest subclass.

    {
        "name": "meaniful test name",
        "test": <AntaTest instance>,
        ...
    }
    """
    return [f"{val['test'].module}.{val['test'].__name__}-{val['name']}" for val in data]
