# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Toolkit for ANTA.
"""
from __future__ import annotations

from typing import Any


def get_failed_logs(expected_output: dict[Any, Any], actual_output: dict[Any, Any]) -> str:
    """
    Get the failed log for a test.
    Returns the failed log or an empty string if there is no difference between the expected and actual output.

    Parameters:
    expected_output (dict): Expected output of a test.
    actual_output (dict): Actual output of a test

    Returns:
    str: Failed log of a test.
    """
    failed_logs = []

    for element, expected_data in expected_output.items():
        actual_data = actual_output.get(element)

        if actual_data is None:
            failed_logs.append(f"\nExpected `{expected_data}` as the {element}, but it was not found in the actual output.")
        elif actual_data != expected_data:
            failed_logs.append(f"\nExpected `{expected_data}` as the {element}, but found `{actual_data}` instead.")

    return "".join(failed_logs)
