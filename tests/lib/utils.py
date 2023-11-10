# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
tests.lib.utils
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_test_ids_dict(val: dict[str, Any], key: str = "name") -> str:
    """
    generate_test_ids Helper to generate test ID for parametrize
    """
    return val.get(key, "unamed_test")


def generate_test_ids_list(val: list[dict[str, Any]], key: str = "name") -> list[str]:
    """
    generate_test_ids Helper to generate test ID for parametrize
    """
    return [entry[key] if key in entry.keys() else "unamed_test" for entry in val]


def generate_test_ids(data: list[dict[str, Any]]) -> list[str]:
    """
    build id for a unit test of an AntaTest subclass

    {
        "name": "meaniful test name",
        "test": <AntaTest instance>,
        ...
    }
    """
    return [f"{val['test'].__module__}.{val['test'].__name__}-{val['name']}" for val in data]


def default_anta_env() -> dict[str, str]:
    """
    Return a default_anta_environement which can be passed to a cliRunner.invoke method
    """
    return {
        "ANTA_USERNAME": "anta",
        "ANTA_PASSWORD": "formica",
        "ANTA_INVENTORY": str(Path(__file__).parent.parent / "data" / "test_inventory.yml"),
        "ANTA_CATALOG": str(Path(__file__).parent.parent / "data" / "test_catalog.yml"),
    }


class FakeEAPIException(Exception):
    """
    Dummy exception for the tests
    """
