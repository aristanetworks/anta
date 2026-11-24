# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.lanz."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.result_manager.models import AntaTestStatus
from anta.tests.lanz import VerifyLANZ
from tests.units.anta_tests import test  # noqa: F401 - Pytest collects this imported test function.

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyLANZ, "success"): {"eos_data": [{"lanzEnabled": True}], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyLANZ, "failure"): {
        "eos_data": [{"lanzEnabled": False}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["LANZ is not enabled"]},
    },
}
