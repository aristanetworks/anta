"""
tests.lib.utils
"""
from __future__ import annotations

from pathlib import Path

from typing import Any, Dict


def generate_test_ids_dict(val: Dict[str, Any], key: str = "name") -> str:
    """
    generate_test_ids Helper to generate test ID for parametrize
    """
    return val.get(key, "unamed_test")


def generate_test_ids_list(val: list[dict[str, Any]], key: str = "name") -> list[str]:
    """
    generate_test_ids Helper to generate test ID for parametrize
    """
    return [entry[key] if key in entry.keys() else "unamed_test" for entry in val]


def default_anta_env() -> Dict[str, str]:
    """
    Return a default_anta_environement which can be passed to a cliRunner.invoke method
    """
    return {
        "ANTA_USERNAME": "anta",
        "ANTA_PASSWORD": "formica",
        "ANTA_INVENTORY": str(Path(__file__).parent.parent / "data" / "test_inventory.yml"),
    }
