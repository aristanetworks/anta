"""Data for testing anta.tests.configuration"""

from typing import Any, Dict, List

INPUT_ZEROTOUCH: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [{"mode": "disabled"}],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [{"mode": "enabled"}],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["ZTP is NOT disabled"]
    },
]


INPUT_RUNNING_CONFIG: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [''],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": ["blah blah"],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["blah blah"]
    },
]
