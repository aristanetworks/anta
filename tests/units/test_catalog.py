# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.device.py."""

from __future__ import annotations

from json import load as json_load
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import pytest
from pydantic import ValidationError
from yaml import safe_load

from anta.catalog import AntaCatalog, AntaCatalogFile, AntaTestDefinition
from anta.models import AntaTest
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
from tests.units.test_models import FakeTestWithInput

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"

INIT_CATALOG_PARAMS: list[ParameterSet] = [
    pytest.param("test_catalog.yml", "yaml", [(VerifyEOSVersion, VerifyEOSVersion.Input(versions=["4.31.1F"]))], id="test_catalog_yaml"),
    pytest.param("test_catalog.json", "json", [(VerifyEOSVersion, VerifyEOSVersion.Input(versions=["4.31.1F"]))], id="test_catalog_json"),
    pytest.param(
        "test_catalog_with_tags.yml",
        "yaml",
        [
            (
                VerifyUptime,
                VerifyUptime.Input(
                    minimum=10,
                    filters=VerifyUptime.Input.Filters(tags={"spine"}),
                ),
            ),
            (
                VerifyUptime,
                VerifyUptime.Input(
                    minimum=9,
                    filters=VerifyUptime.Input.Filters(tags={"leaf"}),
                ),
            ),
            (VerifyReloadCause, {"filters": {"tags": ["spine", "leaf"]}}),
            (VerifyCoredump, VerifyCoredump.Input()),
            (VerifyAgentLogs, AntaTest.Input()),
            (VerifyCPUUtilization, None),
            (VerifyMemoryUtilization, None),
            (VerifyFileSystemUtilization, None),
            (VerifyNTP, {}),
            (VerifyMlagStatus, {"filters": {"tags": ["leaf"]}}),
            (VerifyL3MTU, {"mtu": 1500, "filters": {"tags": ["spine"]}}),
        ],
        id="test_catalog_with_tags",
    ),
    pytest.param("test_empty_catalog.yml", "yaml", [], id="test_empty_catalog"),
    pytest.param("test_empty_dict_catalog.yml", "yaml", [], id="test_empty_dict_catalog"),
]
CATALOG_PARSE_FAIL_PARAMS: list[ParameterSet] = [
    pytest.param(
        "test_catalog_wrong_format.toto",
        "toto",
        "'toto' is not a valid format for an AntaCatalog file. Only 'yaml' and 'json' are supported.",
        id="undefined_tests",
    ),
    pytest.param("test_catalog_invalid_json.json", "json", "JSONDecodeError", id="invalid_json"),
    pytest.param("test_catalog_with_undefined_tests.yml", "yaml", "FakeTest is not defined in Python module anta.tests.software", id="undefined_tests"),
    pytest.param("test_catalog_with_undefined_module.yml", "yaml", "Module named anta.tests.undefined cannot be imported", id="undefined_module"),
    pytest.param(
        "test_catalog_with_syntax_error_module.yml",
        "yaml",
        "Value error, Module named tests.data.syntax_error cannot be imported. Verify that the module exists and there is no Python syntax issues.",
        id="syntax_error",
    ),
    pytest.param(
        "test_catalog_with_undefined_module_nested.yml",
        "yaml",
        "Module named undefined from package anta.tests cannot be imported",
        id="undefined_module_nested",
    ),
    pytest.param(
        "test_catalog_not_a_list.yml",
        "yaml",
        "Value error, Syntax error when parsing: True\nIt must be a list of ANTA tests. Check the test catalog.",
        id="not_a_list",
    ),
    pytest.param(
        "test_catalog_test_definition_not_a_dict.yml",
        "yaml",
        "Value error, Syntax error when parsing: VerifyEOSVersion\nIt must be a dictionary. Check the test catalog.",
        id="test_definition_not_a_dict",
    ),
    pytest.param(
        "test_catalog_test_definition_multiple_dicts.yml",
        "yaml",
        "Value error, Syntax error when parsing: {'VerifyEOSVersion': {'versions': ['4.25.4M', '4.26.1F']}, 'VerifyTerminAttrVersion': {'versions': ['4.25.4M']}}\n"
        "It must be a dictionary with a single entry. Check the indentation in the test catalog.",
        id="test_definition_multiple_dicts",
    ),
    pytest.param("test_catalog_wrong_type.yml", "yaml", "must be a dict, got str", id="wrong_type_after_parsing"),
]
CATALOG_FROM_DICT_FAIL_PARAMS: list[ParameterSet] = [
    pytest.param("test_catalog_with_undefined_tests.yml", "FakeTest is not defined in Python module anta.tests.software", id="undefined_tests"),
    pytest.param("test_catalog_wrong_type.yml", "Wrong input type for catalog data, must be a dict, got str", id="wrong_type"),
]
CATALOG_FROM_LIST_FAIL_PARAMS: list[ParameterSet] = [
    pytest.param([(FakeTestWithInput, AntaTest.Input())], "Test input has type AntaTest.Input but expected type FakeTestWithInput.Input", id="wrong_inputs"),
    pytest.param([(None, None)], "Input should be a subclass of AntaTest", id="no_test"),
    pytest.param(
        [(FakeTestWithInput, None)],
        "FakeTestWithInput test inputs are not valid: 1 validation error for Input\n\tstring\n\t  Field required",
        id="no_input_when_required",
    ),
    pytest.param(
        [(FakeTestWithInput, {"string": True})],
        "FakeTestWithInput test inputs are not valid: 1 validation error for Input\n\tstring\n\t  Input should be a valid string",
        id="wrong_input_type",
    ),
]
TESTS_SETTER_FAIL_PARAMS: list[ParameterSet] = [
    pytest.param("not_a_list", "The catalog must contain a list of tests", id="not_a_list"),
    pytest.param([42, 43], "A test in the catalog must be an AntaTestDefinition instance", id="not_a_list_of_test_definitions"),
]


class TestAntaCatalog:
    """Tests for anta.catalog.AntaCatalog."""

    @pytest.mark.parametrize(("filename", "file_format", "tests"), INIT_CATALOG_PARAMS)
    def test_parse(self, filename: str, file_format: Literal["yaml", "json"], tests: list[tuple[type[AntaTest], AntaTest.Input | dict[str, Any] | None]]) -> None:
        """Instantiate AntaCatalog from a file."""
        catalog: AntaCatalog = AntaCatalog.parse(DATA_DIR / filename, file_format=file_format)

        assert len(catalog.tests) == len(tests)
        for test_id, (test, inputs_data) in enumerate(tests):
            assert catalog.tests[test_id].test == test
            if inputs_data is not None:
                inputs = test.Input(**inputs_data) if isinstance(inputs_data, dict) else inputs_data
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize(("filename", "file_format", "tests"), INIT_CATALOG_PARAMS)
    def test_from_list(
        self, filename: str, file_format: Literal["yaml", "json"], tests: list[tuple[type[AntaTest], AntaTest.Input | dict[str, Any] | None]]
    ) -> None:
        """Instantiate AntaCatalog from a list."""
        catalog: AntaCatalog = AntaCatalog.from_list(tests)

        assert len(catalog.tests) == len(tests)
        for test_id, (test, inputs_data) in enumerate(tests):
            assert catalog.tests[test_id].test == test
            if inputs_data is not None:
                inputs = test.Input(**inputs_data) if isinstance(inputs_data, dict) else inputs_data
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize(("filename", "file_format", "tests"), INIT_CATALOG_PARAMS)
    def test_from_dict(
        self, filename: str, file_format: Literal["yaml", "json"], tests: list[tuple[type[AntaTest], AntaTest.Input | dict[str, Any] | None]]
    ) -> None:
        """Instantiate AntaCatalog from a dict."""
        file = DATA_DIR / filename
        with file.open(encoding="UTF-8") as f:
            data = safe_load(f) if file_format == "yaml" else json_load(f)
            catalog: AntaCatalog = AntaCatalog.from_dict(data)

        assert len(catalog.tests) == len(tests)
        for test_id, (test, inputs_data) in enumerate(tests):
            assert catalog.tests[test_id].test == test
            if inputs_data is not None:
                inputs = test.Input(**inputs_data) if isinstance(inputs_data, dict) else inputs_data
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize(("filename", "file_format", "error"), CATALOG_PARSE_FAIL_PARAMS)
    def test_parse_fail(self, filename: str, file_format: Literal["yaml", "json"], error: str) -> None:
        """Errors when instantiating AntaCatalog from a file."""
        with pytest.raises((ValidationError, TypeError, ValueError, OSError)) as exec_info:
            AntaCatalog.parse(DATA_DIR / filename, file_format=file_format)
        if isinstance(exec_info.value, ValidationError):
            assert error in exec_info.value.errors()[0]["msg"]
        else:
            assert error in str(exec_info)

    def test_parse_fail_parsing(self, caplog: pytest.LogCaptureFixture) -> None:
        """Errors when instantiating AntaCatalog from a file."""
        with pytest.raises(FileNotFoundError) as exec_info:
            AntaCatalog.parse(DATA_DIR / "catalog_does_not_exist.yml")
        assert "No such file or directory" in str(exec_info)
        assert len(caplog.record_tuples) >= 1
        _, _, message = caplog.record_tuples[0]
        assert "Unable to parse ANTA Test Catalog file" in message
        assert "FileNotFoundError: [Errno 2] No such file or directory" in message

    @pytest.mark.parametrize(("tests", "error"), CATALOG_FROM_LIST_FAIL_PARAMS)
    def test_from_list_fail(self, tests: list[tuple[type[AntaTest], AntaTest.Input | dict[str, Any] | None]], error: str) -> None:
        """Errors when instantiating AntaCatalog from a list of tuples."""
        with pytest.raises(ValidationError) as exec_info:
            AntaCatalog.from_list(tests)
        assert error in exec_info.value.errors()[0]["msg"]

    @pytest.mark.parametrize(("filename", "error"), CATALOG_FROM_DICT_FAIL_PARAMS)
    def test_from_dict_fail(self, filename: str, error: str) -> None:
        """Errors when instantiating AntaCatalog from a list of tuples."""
        file = DATA_DIR / filename
        with file.open(encoding="UTF-8") as f:
            data = safe_load(f)
        with pytest.raises((ValidationError, TypeError)) as exec_info:
            AntaCatalog.from_dict(data)
        if isinstance(exec_info.value, ValidationError):
            assert error in exec_info.value.errors()[0]["msg"]
        else:
            assert error in str(exec_info)

    def test_filename(self) -> None:
        """Test filename."""
        catalog = AntaCatalog(filename="test")
        assert catalog.filename == Path("test")
        catalog = AntaCatalog(filename=Path("test"))
        assert catalog.filename == Path("test")

    @pytest.mark.parametrize(("filename", "file_format", "tests"), INIT_CATALOG_PARAMS)
    def test__tests_setter_success(
        self,
        filename: str,
        file_format: Literal["yaml", "json"],
        tests: list[tuple[type[AntaTest], AntaTest.Input | dict[str, Any] | None]],
    ) -> None:
        """Success when setting AntaCatalog.tests from a list of tuples."""
        catalog = AntaCatalog()
        catalog.tests = [AntaTestDefinition(test=test, inputs=inputs) for test, inputs in tests]
        assert len(catalog.tests) == len(tests)
        for test_id, (test, inputs_data) in enumerate(tests):
            assert catalog.tests[test_id].test == test
            if inputs_data is not None:
                inputs = test.Input(**inputs_data) if isinstance(inputs_data, dict) else inputs_data
                assert inputs == catalog.tests[test_id].inputs

    @pytest.mark.parametrize(("tests", "error"), TESTS_SETTER_FAIL_PARAMS)
    def test__tests_setter_fail(self, tests: list[Any], error: str) -> None:
        """Errors when setting AntaCatalog.tests from a list of tuples."""
        catalog = AntaCatalog()
        with pytest.raises(TypeError) as exec_info:
            catalog.tests = tests
        assert error in str(exec_info)

    def test_build_indexes_all(self) -> None:
        """Test AntaCatalog.build_indexes()."""
        catalog: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog_with_tags.yml")
        catalog.build_indexes()
        assert len(catalog.tag_to_tests[None]) == 6
        assert "leaf" in catalog.tag_to_tests
        assert len(catalog.tag_to_tests["leaf"]) == 3
        all_unique_tests = catalog.tag_to_tests[None]
        for tests in catalog.tag_to_tests.values():
            all_unique_tests.update(tests)
        assert len(all_unique_tests) == 11
        assert catalog.indexes_built is True

    def test_build_indexes_filtered(self) -> None:
        """Test AntaCatalog.build_indexes()."""
        catalog: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog_with_tags.yml")
        catalog.build_indexes({"VerifyUptime", "VerifyCoredump", "VerifyL3MTU"})
        assert "leaf" in catalog.tag_to_tests
        assert len(catalog.tag_to_tests["leaf"]) == 1
        assert len(catalog.tag_to_tests[None]) == 1
        all_unique_tests = catalog.tag_to_tests[None]
        for tests in catalog.tag_to_tests.values():
            all_unique_tests.update(tests)
        assert len(all_unique_tests) == 4
        assert catalog.indexes_built is True

    def test_get_tests_by_tags(self) -> None:
        """Test AntaCatalog.get_tests_by_tags()."""
        catalog: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog_with_tags.yml")
        catalog.build_indexes()
        tests: set[AntaTestDefinition] = catalog.get_tests_by_tags(tags={"leaf"})
        assert len(tests) == 3
        tests = catalog.get_tests_by_tags(tags={"leaf", "spine"}, strict=True)
        assert len(tests) == 1

    def test_merge_catalogs(self) -> None:
        """Test the merge_catalogs function."""
        # Load catalogs of different sizes
        small_catalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
        medium_catalog = AntaCatalog.parse(DATA_DIR / "test_catalog_medium.yml")
        tagged_catalog = AntaCatalog.parse(DATA_DIR / "test_catalog_with_tags.yml")

        # Merge the catalogs and check the number of tests
        final_catalog = AntaCatalog.merge_catalogs([small_catalog, medium_catalog, tagged_catalog])
        assert len(final_catalog.tests) == len(small_catalog.tests) + len(medium_catalog.tests) + len(tagged_catalog.tests)

    def test_merge(self) -> None:
        """Test AntaCatalog.merge()."""
        catalog1: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
        assert len(catalog1.tests) == 1
        catalog2: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
        assert len(catalog2.tests) == 1
        catalog3: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog_medium.yml")
        assert len(catalog3.tests) == 228

        with pytest.deprecated_call():
            merged_catalog = catalog1.merge(catalog2)
        assert len(merged_catalog.tests) == 2
        assert len(catalog1.tests) == 1
        assert len(catalog2.tests) == 1

        with pytest.deprecated_call():
            merged_catalog = catalog2.merge(catalog3)
        assert len(merged_catalog.tests) == 229
        assert len(catalog2.tests) == 1
        assert len(catalog3.tests) == 228

    def test_dump(self) -> None:
        """Test AntaCatalog.dump()."""
        catalog: AntaCatalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
        assert len(catalog.tests) == 1
        file: AntaCatalogFile = catalog.dump()
        assert sum(len(tests) for tests in file.root.values()) == 1

        catalog = AntaCatalog.parse(DATA_DIR / "test_catalog_medium.yml")
        assert len(catalog.tests) == 228
        file = catalog.dump()
        assert sum(len(tests) for tests in file.root.values()) == 228


class TestAntaCatalogFile:  # pylint: disable=too-few-public-methods
    """Test for anta.catalog.AntaCatalogFile."""

    def test_yaml(self) -> None:
        """Test AntaCatalogFile.yaml()."""
        file = DATA_DIR / "test_catalog_medium.yml"
        catalog = AntaCatalog.parse(file)
        assert len(catalog.tests) == 228
        catalog_yaml_str = catalog.dump().yaml()
        with file.open(encoding="UTF-8") as f:
            assert catalog_yaml_str == f.read()
