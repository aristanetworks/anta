# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.lanz."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.lanz import VerifyLANZ
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyLANZ, "success"): {"eos_data": [{"lanzEnabled": True}], "inputs": None, "expected": {"result": "success"}},
    (VerifyLANZ, "failure"): {"eos_data": [{"lanzEnabled": False}], "inputs": None, "expected": {"result": "failure", "messages": ["LANZ is not enabled"]}},
}
