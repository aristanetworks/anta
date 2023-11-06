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

# Test classes used as expected values

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
        "error": "FakeTest is not defined in Python module <module 'anta.tests.software' from",
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
    {
        "name": "not_a_list",
        "filename": "test_catalog_not_a_list.yml",
        "error": "Value error, True must be a list of AntaTestDefinition",
    },
    {
        "name": "test_definition_not_a_dict",
        "filename": "test_catalog_test_definition_not_a_dict.yml",
        "error": "Value error, AntaTestDefinition must be a dictionary",
    },
    {
        "name": "test_definition_multiple_dicts",
        "filename": "test_catalog_test_definition_multiple_dicts.yml",
        "error": "Value error, AntaTestDefinition must be a dictionary with a single entry",
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
        "name": "no_input_when_required",
        "tests": [(FakeTestWithInput, None)],
        "error": "Field required",
    },
    {
        "name": "wrong_input_type",
        "tests": [(FakeTestWithInput, True)],
        "error": "Value error, Coud not instantiate inputs as type <class 'bool'> is not valid",
    },
]

TESTS_SETTER_FAIL_DATA: list[dict[str, Any]] = [
    {
        "name": "not_a_list",
        "tests": "not_a_list",
        "error": "The catalog must contain a list of tests",
    },
    {
        "name": "not_a_list_of_test_definitions",
        "tests": [42, 43],
        "error": "A test in the catalog must be an AntaTestDefinition instance",
    },
]


class Test_AntaCatalog:
    """
    Test for anta.catalog.AntaCatalog
    """

    def test__init__filename_and_tests(self) -> None:
        """
        Instantiate AntaCatalog from a file and give tests at the same time
        """
        with pytest.raises(RuntimeError, match="'filename' and 'tests' arguments cannot be provided at the same time"):
            AntaCatalog(filename=str(DATA_DIR / "test_catalog.yml"), tests=INIT_CATALOG_DATA[0]["tests"])

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test__init__filename(self, catalog_data: dict[str, Any]) -> None:
        """
        Instantiate AntaCatalog from a file
        """
        catalog = AntaCatalog(filename=str(DATA_DIR / catalog_data["filename"]))

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
        with pytest.raises(ValidationError) as exec_info:
            AntaCatalog(filename=str(DATA_DIR / catalog_data["filename"]))
        assert catalog_data["error"] in exec_info.value.errors()[0]["msg"]

    def test__init__filename_fail_parsing(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        Errors when instantiating AntaCatalog from a file
        """
        with pytest.raises(Exception) as exec_info:
            AntaCatalog(filename=str(DATA_DIR / "catalog_does_not_exist.yml"))
        assert "No such file or directory" in str(exec_info)
        assert len(caplog.record_tuples) == 1
        _, _, message = caplog.record_tuples[0]
        assert "Something went wrong while parsing" in message

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

    @pytest.mark.parametrize("catalog_data", TESTS_SETTER_FAIL_DATA, ids=generate_test_ids_list(TESTS_SETTER_FAIL_DATA))
    def test__tests_setter_fail(self, catalog_data: dict[str, Any]) -> None:
        """
        Errors when setting AntaCatalog.tests from a list of tuples
        """
        catalog = AntaCatalog()
        with pytest.raises(ValueError) as exec_info:
            catalog.tests = catalog_data["tests"]
        assert catalog_data["error"] in str(exec_info)

    def test_get_tests_by_tags(self) -> None:
        """
        Test AntaCatalog.test_get_tests_by_tags()
        """
        catalog = AntaCatalog(filename=str(DATA_DIR / "test_catalog_with_tags.yml"))
        tests: list[AntaTestDefinition] = catalog.get_tests_by_tags(tags=["leaf"])
        assert len(tests) == 2

    def test_get_tests_by_device(self, mocked_device: AntaDevice) -> None:
        """
        Test AntaCatalog.test_get_tests_by_device()
        """
        catalog = AntaCatalog(filename=str(DATA_DIR / "test_catalog_with_tags.yml"))
        tests: list[AntaTestDefinition] = catalog.get_tests_by_device(device=mocked_device)
        assert len(tests) == 1
