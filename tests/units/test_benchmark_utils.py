# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for benchmark utilities."""

from __future__ import annotations

from typing import Any

import pytest

from anta.result_manager.models import AntaTestStatus
from tests.benchmark.utils import _has_error_result


@pytest.mark.parametrize(
    ("expected", "result"),
    [
        pytest.param({"result": AntaTestStatus.ERROR}, True, id="parent-error"),
        pytest.param(
            {
                "result": AntaTestStatus.FAILURE,
                "atomic_results": [{"description": "check", "result": AntaTestStatus.ERROR}],
            },
            True,
            id="atomic-error",
        ),
        pytest.param(
            {
                "result": AntaTestStatus.FAILURE,
                "atomic_results": [{"description": "check", "result": AntaTestStatus.FAILURE}],
            },
            False,
            id="atomic-failure",
        ),
        pytest.param({"result": AntaTestStatus.INCONCLUSIVE}, False, id="parent-inconclusive"),
        pytest.param(
            {
                "result": AntaTestStatus.INCONCLUSIVE,
                "atomic_results": [{"description": "check", "result": AntaTestStatus.INCONCLUSIVE}],
            },
            False,
            id="atomic-inconclusive",
        ),
        pytest.param({"result": AntaTestStatus.SUCCESS}, False, id="success-without-atomic-results"),
    ],
)
def test_has_error_result(expected: dict[str, Any], *, result: bool) -> None:
    """Verify parent and atomic error results are detected for benchmark filtering."""
    assert _has_error_result({"expected": expected}) is result
