# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
test anta.device.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.device import AntaDevice
from anta.models import AntaTest

# Test classes used as expected values
from anta.tests.configuration import VerifyZeroTouch
from anta.tests.hardware import VerifyTemperature
from anta.tests.interfaces import VerifyL3MTU
from anta.tests.mlag import VerifyMlagStatus
from anta.tests.software import VerifyEOSVersion
from anta.tests.system import (
    VerifyAgentLogs,
    VerifyCoredump,
    VerifyCPUUtilization,
    VerifyFileSystemUtilization,
    VerifyMemoryUtilization,
    VerifyNTP,
    VerifyReloadCause,
    VerifyUptime,
)
from tests.lib.utils import generate_test_ids_list
from tests.units.test_models import FakeTestWithInput

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"

INIT_CATALOG_DATA: list[dict[str, Any]] = [
    {
        "name": "test_catalog",
        "filename": "test_catalog.yml",
        "tests": [
            (VerifyZeroTouch, None),
            (VerifyTemperature, None),
            (VerifyEOSVersion, VerifyEOSVersion.Input(versions=["4.25.4M", "4.26.1F"])),
            (VerifyUptime, {"minimum": 86400}),
        ],
    },
    {
        "name": "test_catalog_with_tags",
        "filename": "test_catalog_with_tags.yml",
        "tests": [
            (
                VerifyUptime,
                VerifyUptime.Input(
                    minimum=10,
                    filters=VerifyUptime.Input.Filters(tags=["fabric"]),
                ),
            ),
            (VerifyReloadCause, {"filters": {"tags": ["leaf", "spine"]}}),
            (VerifyCoredump, VerifyCoredump.Input()),
            (VerifyAgentLogs, AntaTest.Input()),
            (VerifyCPUUtilization, VerifyCPUUtilization.Input(filters=VerifyCPUUtilization.Input.Filters(tags=["leaf"]))),
            (VerifyMemoryUtilization, VerifyMemoryUtilization.Input(filters=VerifyMemoryUtilization.Input.Filters(devices=["testdevice"]))),
            (VerifyFileSystemUtilization, None),
            (VerifyNTP, {}),
            (VerifyMlagStatus, None),
            (VerifyL3MTU, {"mtu": 1500, "filters": {"tags": ["demo"]}}),
        ],
    },
]
INIT_CATALOG_FILENAME_FAIL_DATA: list[dict[str, Any]] = [
    {
        "name": "undefined_tests",
        "filename": "test_catalog_with_undefined_tests.yml",
        "error": "FakeTest is not defined in Python module <module 'anta.tests.software' from '/mnt/lab/projects/anta/anta/tests/software.py'>",
    },
    {
        "name": "undefined_module",
        "filename": "test_catalog_with_undefined_module.yml",
        "error": "Module named anta.tests.undefined cannot be imported",
    },
    {
        "name": "undefined_module_nested",
        "filename": "test_catalog_with_undefined_module_nested.yml",
        "error": "Module named undefined from package anta.tests cannot be imported",
    },
]
INIT_CATALOG_TESTS_FAIL_DATA: list[dict[str, Any]] = [
    {
        "name": "wrong_inputs",
        "tests": [
            (
                FakeTestWithInput,
                AntaTest.Input(),
            ),
        ],
        "error": "Test input has type AntaTest.Input but expected type FakeTestWithInput.Input",
    },
    {
        "name": "no_test",
        "tests": [(None, None)],
        "error": "Input should be a subclass of AntaTest",
    },
    {
        "name": "no_test",
        "tests": [(FakeTestWithInput, None)],
        "error": "Field required",
    },
]


class Test_AntaCatalog:
    """
    Test for anta.catalog.AntaCatalog
    """

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test__init__filename(self, catalog_data: dict[str, Any]) -> None:
        """
        Instantiate AntaCatalog from a file
        """
        catalog = AntaCatalog(filename=DATA_DIR / catalog_data["filename"])
        catalog.check()

        assert len(catalog.tests) == len(catalog_data["tests"])
        for test_id, (test, inputs) in enumerate(catalog_data["tests"]):
            assert catalog.tests[test_id].test == test
            if inputs is not None:
                if isinstance(inputs, dict):
                    inputs = test.Input(**inputs)
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_FILENAME_FAIL_DATA, ids=generate_test_ids_list(INIT_CATALOG_FILENAME_FAIL_DATA))
    def test__init__filename_fail(self, catalog_data: dict[str, Any]) -> None:
        """
        Errors when instantiating AntaCatalog from a file
        """
        catalog = AntaCatalog(filename=DATA_DIR / catalog_data["filename"])
        with pytest.raises(ValidationError) as exec_info:
            catalog.check()
        assert catalog_data["error"] in exec_info.value.errors()[0]["msg"]

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test__init__tests(self, catalog_data: dict[str, Any]) -> None:
        """
        Instantiate AntaCatalog from a list of tuples
        """
        catalog = AntaCatalog(tests=catalog_data["tests"])

        assert len(catalog.tests) == len(catalog_data["tests"])
        for test_id, (test, inputs) in enumerate(catalog_data["tests"]):
            assert catalog.tests[test_id].test == test
            if inputs is not None:
                if isinstance(inputs, dict):
                    inputs = test.Input(**inputs)
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_TESTS_FAIL_DATA, ids=generate_test_ids_list(INIT_CATALOG_TESTS_FAIL_DATA))
    def test__init__tests_fail(self, catalog_data: dict[str, Any]) -> None:
        """
        Errors when instantiating AntaCatalog from a list of tuples
        """
        with pytest.raises(ValidationError) as exec_info:
            AntaCatalog(tests=catalog_data["tests"])
        assert catalog_data["error"] in exec_info.value.errors()[0]["msg"]

    def test_get_tests_by_tags(self) -> None:
        catalog = AntaCatalog(filename=DATA_DIR / "test_catalog_with_tags.yml")
        catalog.check()
        tests: list[AntaTestDefinition] = catalog.get_tests_by_tags(tags=["leaf"])
        assert len(tests) == 2

    def test_get_tests_by_device(self, mocked_device: AntaDevice) -> None:
        catalog = AntaCatalog(filename=DATA_DIR / "test_catalog_with_tags.yml")
        catalog.check()
        tests: list[AntaTestDefinition] = catalog.get_tests_by_device(device=mocked_device)
        assert len(tests) == 1
