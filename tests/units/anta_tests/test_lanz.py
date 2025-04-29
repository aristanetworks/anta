# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.lanz."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

from anta.models import AntaTest
from anta.tests.lanz import VerifyLANZ
from tests.units.anta_tests import AntaUnitTest, test

AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestDataDict = {
    (VerifyLANZ, "success"): {"eos_data": [{"lanzEnabled": True}], "inputs": None, "expected": {"result": "success"}},
    (VerifyLANZ, "failure"): {"eos_data": [{"lanzEnabled": False}], "inputs": None, "expected": {"result": "failure", "messages": ["LANZ is not enabled"]}},
}
