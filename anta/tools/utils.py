# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Toolkit for ANTA.
"""
from __future__ import annotations

import re
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


def custom_division(numerator: int | float, denominator: int | float) -> int | float:
    """
    Custom division that returns an integer if the result is an integer, otherwise a float.

    Parameters:
    numerator (float): The numerator.
    denominator (float): The denominator.

    Returns:
    Union[int, float]: The result of the division.
    """
    result = numerator / denominator
    return int(result) if result.is_integer() else result


def extract_speed_and_lane(input_speed: str) -> tuple[Any, Any]:
    """
    This function extracts the speed and lane information from the input string.

    Parameters:
        input_speed (str): The input string which contains the speed and lane information.

    Returns:
        tuple[Any, Any]: The extracted speed from the input string, and the extracted lane from the input string.
                         If no lane information is found, it returns None.

    Examples:
        100g-8: (100, 8)
        100g: (100, None)
        100-8: (100, 8)
        auto: (None, None)
        forced 100g: (100, None)
        auto 100g: (100, None)
        auto 100g-4: (100, 4)
    """

    # Regular expression pattern
    pattern = r"(auto |force(d)? )?(?P<speed>\d+(\.\d+)?)(g)?(-(?P<lane>\d+))?"

    # Find matches
    match = re.match(pattern, input_speed)

    if match:
        # If a match is found, extract the speed and lane information
        speed = match.group("speed")
        lane = int(match.group("lane")) if match.group("lane") else None
        return speed, lane

    return None, None
