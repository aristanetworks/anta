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
from yaml import safe_load

from anta.catalog import AntaCatalog, AntaTestDefinition
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
            (VerifyMemoryUtilization, VerifyMemoryUtilization.Input(filters=VerifyMemoryUtilization.Input.Filters(tags=["testdevice"]))),
            (VerifyFileSystemUtilization, None),
            (VerifyNTP, {}),
            (VerifyMlagStatus, None),
            (VerifyL3MTU, {"mtu": 1500, "filters": {"tags": ["demo"]}}),
        ],
    },
    {
        "name": "test_empty_catalog",
        "filename": "test_empty_catalog.yml",
        "tests": [],
    },
]
CATALOG_PARSE_FAIL_DATA: list[dict[str, Any]] = [
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
    {"name": "wrong_type_after_parsing", "filename": "test_catalog_wrong_type.yml", "error": " does not have the correct format, Aborting..."},
]
CATALOG_FROM_DICT_FAIL_DATA: list[dict[str, Any]] = [
    {
        "name": "undefined_tests",
        "filename": "test_catalog_with_undefined_tests.yml",
        "error": "FakeTest is not defined in Python module <module 'anta.tests.software' from",
    },
    {
        "name": "wrong_type",
        "filename": "test_catalog_wrong_type.yml",
        "error": "Wrong input type for catalog data, must be a dict, got <class 'str'>",
    },
]
CATALOG_FROM_LIST_FAIL_DATA: list[dict[str, Any]] = [
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

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test_parse(self, catalog_data: dict[str, Any]) -> None:
        """
        Instantiate AntaCatalog from a file
        """
        catalog: AntaCatalog = AntaCatalog.parse(str(DATA_DIR / catalog_data["filename"]))

        assert len(catalog.tests) == len(catalog_data["tests"])
        for test_id, (test, inputs) in enumerate(catalog_data["tests"]):
            assert catalog.tests[test_id].test == test
            if inputs is not None:
                if isinstance(inputs, dict):
                    inputs = test.Input(**inputs)
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test_from_list(self, catalog_data: dict[str, Any]) -> None:
        """
        Instantiate AntaCatalog from a list
        """
        catalog: AntaCatalog = AntaCatalog.from_list(catalog_data["tests"])

        assert len(catalog.tests) == len(catalog_data["tests"])
        for test_id, (test, inputs) in enumerate(catalog_data["tests"]):
            assert catalog.tests[test_id].test == test
            if inputs is not None:
                if isinstance(inputs, dict):
                    inputs = test.Input(**inputs)
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test_from_dict(self, catalog_data: dict[str, Any]) -> None:
        """
        Instantiate AntaCatalog from a dict
        """
        with open(file=str(DATA_DIR / catalog_data["filename"]), mode="r", encoding="UTF-8") as file:
            data = safe_load(file)
            catalog: AntaCatalog = AntaCatalog.from_dict(data)

        assert len(catalog.tests) == len(catalog_data["tests"])
        for test_id, (test, inputs) in enumerate(catalog_data["tests"]):
            assert catalog.tests[test_id].test == test
            if inputs is not None:
                if isinstance(inputs, dict):
                    inputs = test.Input(**inputs)
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize("catalog_data", CATALOG_PARSE_FAIL_DATA, ids=generate_test_ids_list(CATALOG_PARSE_FAIL_DATA))
    def test_parse_fail(self, catalog_data: dict[str, Any]) -> None:
        """
        Errors when instantiating AntaCatalog from a file
        """
        with pytest.raises((ValidationError, ValueError)) as exec_info:
            AntaCatalog.parse(str(DATA_DIR / catalog_data["filename"]))
        if isinstance(exec_info.value, ValidationError):
            assert catalog_data["error"] in exec_info.value.errors()[0]["msg"]
        else:
            assert catalog_data["error"] in str(exec_info)

    def test_parse_fail_parsing(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        Errors when instantiating AntaCatalog from a file
        """
        with pytest.raises(Exception) as exec_info:
            AntaCatalog.parse(str(DATA_DIR / "catalog_does_not_exist.yml"))
        assert "No such file or directory" in str(exec_info)
        assert len(caplog.record_tuples) == 1
        _, _, message = caplog.record_tuples[0]
        assert "Unable to parse ANTA Test Catalog file" in message
        assert "FileNotFoundError ([Errno 2] No such file or directory" in message

    @pytest.mark.parametrize("catalog_data", CATALOG_FROM_LIST_FAIL_DATA, ids=generate_test_ids_list(CATALOG_FROM_LIST_FAIL_DATA))
    def test_from_list_fail(self, catalog_data: dict[str, Any]) -> None:
        """
        Errors when instantiating AntaCatalog from a list of tuples
        """
        with pytest.raises(ValidationError) as exec_info:
            AntaCatalog.from_list(catalog_data["tests"])
        assert catalog_data["error"] in exec_info.value.errors()[0]["msg"]

    @pytest.mark.parametrize("catalog_data", CATALOG_FROM_DICT_FAIL_DATA, ids=generate_test_ids_list(CATALOG_FROM_DICT_FAIL_DATA))
    def test_from_dict_fail(self, catalog_data: dict[str, Any]) -> None:
        """
        Errors when instantiating AntaCatalog from a list of tuples
        """
        with open(file=str(DATA_DIR / catalog_data["filename"]), mode="r", encoding="UTF-8") as file:
            data = safe_load(file)
        with pytest.raises((ValidationError, ValueError)) as exec_info:
            AntaCatalog.from_dict(data)
        if isinstance(exec_info.value, ValidationError):
            assert catalog_data["error"] in exec_info.value.errors()[0]["msg"]
        else:
            assert catalog_data["error"] in str(exec_info)

    def test_filename(self) -> None:
        """
        Test filename
        """
        catalog = AntaCatalog(filename="test")
        assert catalog.filename == Path("test")
        catalog = AntaCatalog(filename=Path("test"))
        assert catalog.filename == Path("test")

    @pytest.mark.parametrize("catalog_data", INIT_CATALOG_DATA, ids=generate_test_ids_list(INIT_CATALOG_DATA))
    def test__tests_setter_success(self, catalog_data: dict[str, Any]) -> None:
        """
        Success when setting AntaCatalog.tests from a list of tuples
        """
        catalog = AntaCatalog()
        catalog.tests = [AntaTestDefinition(test=test, inputs=inputs) for test, inputs in catalog_data["tests"]]
        assert len(catalog.tests) == len(catalog_data["tests"])
        for test_id, (test, inputs) in enumerate(catalog_data["tests"]):
            assert catalog.tests[test_id].test == test
            if inputs is not None:
                if isinstance(inputs, dict):
                    inputs = test.Input(**inputs)
                assert inputs == catalog.tests[test_id].inputs

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
        catalog: AntaCatalog = AntaCatalog.parse(str(DATA_DIR / "test_catalog_with_tags.yml"))
        tests: list[AntaTestDefinition] = catalog.get_tests_by_tags(tags=["leaf"])
        assert len(tests) == 2
