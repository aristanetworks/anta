# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Catalog related functions
"""
from __future__ import annotations

import logging

from anta.device import AsyncEOSDevice
from anta.models import AntaTest
from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


def is_catalog_valid(catalog: list[tuple[AntaTest, AntaTest.Input]]) -> ResultManager:
    """
    TODO - for now a test requires a device but this may be revisited in the future
    """
    # Mock device
    mock_device = AsyncEOSDevice(name="mock", host="127.0.0.1", username="mock", password="mock")

    manager = ResultManager()
    # Instantiate each test to verify the Inputs are correct
    for test_class, test_inputs in catalog:
        # TODO - this is the same code with typing as in runner.py but somehow mypy complains that test_class
        # ot type AntaTest is not callable
        test_instance = test_class(device=mock_device, inputs=test_inputs)  # type: ignore[operator]
        manager.add_test_result(test_instance.result)
    return manager
