# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations
from typing import Any

def get_failed_logs(expected_output: dict[Any, Any], actual_output: dict[Any, Any]) -> Any:
    """
    Get the failed log for a test.
    Returns the failed log or empty string if no difference between the expected and actual output.
    Parameters
    ----------
    expected_output : dict
        Expected output of a test.
    actual_output : dict
        Actual output of a test
    Returns
    -------
    str
        Failed log of a test.
    """
    failed_log = ""
    for element, data in expected_output.items():
        if actual_output[element] != data:
            failed_log += f"\nExpected {element} is `{data}` however in actual found as `{actual_output[element]}`."

    return failed_log
