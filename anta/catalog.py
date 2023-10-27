# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Catalog related functions
"""
from __future__ import annotations

import importlib
import logging
from types import ModuleType
from typing import Any

from pydantic import BaseModel, RootModel, model_serializer, model_validator
from pydantic.types import ImportString
from yaml import safe_load

from anta.device import AntaDevice
from anta.models import AntaTest

logger = logging.getLogger(__name__)


class AntaTestDefinition(BaseModel):
    test: type[AntaTest]
    inputs: AntaTest.Input

    @model_serializer
    def ser_model(self) -> dict[str, AntaTest.Input]:
        return {self.test.__name__: self.inputs}

    @model_validator(mode="after")
    def check_inputs(self) -> "AntaTestDefinition":
        assert isinstance(self.inputs, self.test.Input), f"{self.inputs} object must be a instance of {self.test.Input}"
        return self


class AntaCatalogFile(RootModel[dict[ImportString, list[AntaTestDefinition]]]):
    """
    This model represents an ANTA Test Catalog File.

     A valid test catalog file must follow the following structure:
        <Python module>:
            - <AntaTest subclass>:
                <AntaTest.Input compliant dictionary>

        Example:
            ```
            anta.tests.connectivity:
                - VerifyReachability:
                    hosts:
                        - dst: 8.8.8.8
                          src: 172.16.0.1
                        - dst: 1.1.1.1
                          src: 172.16.0.1
                    result_overwrite:
                        categories:
                            - "Overwritten category 1"
                        description: "Test with overwritten description"
                        custom_field: "Test run by John Doe"
            ```

        Also supports nesting for Python module definition:
            ```
            anta.tests:
                connectivity:
                    - VerifyReachability:
                        hosts:
                            - dst: 8.8.8.8
                              src: 172.16.0.1
                            - dst: 1.1.1.1
                              src: 172.16.0.1
                        result_overwrite:
                            categories:
                                - "Overwritten category 1"
                            description: "Test with overwritten description"
                            custom_field: "Test run by John Doe"
            ```
    """

    root: dict[ImportString, list[AntaTestDefinition]]

    @model_validator(mode="before")
    @classmethod
    def check_tests(cls, data: Any) -> Any:
        """
        Allow the user to provide a Python data structure that only has string values.
        This validator will try to flatten and import Python modules, check if the tests classes
        are actually defined in their respective Python module and instantiate Input instances
        with provided value to validate test inputs.
        """

        def flatten_modules(data: dict[str, Any], package: str | None = None) -> dict[ModuleType, list[Any]]:
            """
            Allow the user to provide a data structure with nested Python modules.

                Example:
                ```
                anta.tests.routing:
                  generic:
                    - <AntaTestDefinition>
                  bgp:
                    - <AntaTestDefinition>
                ```
                `anta.tests.routing.generic` and `anta.tests.routing.bgp` are importable Python modules.
            """
            modules: dict[ModuleType, list[Any]] = {}
            for module_name, tests in data.items():
                if package and not module_name.startswith("."):
                    module_name = f".{module_name}"
                module: ModuleType = importlib.import_module(name=module_name, package=package)
                if isinstance(tests, dict):
                    # This is an inner Python module
                    modules.update(flatten_modules(data=tests, package=module.__name__))
                else:
                    assert isinstance(tests, list), f"{tests} must be a list of AntaTestDefinition"
                    # This is a list of AntaTestDefinition
                    modules[module] = tests
            return modules

        if isinstance(data, dict):
            typed_data: dict[ModuleType, list[Any]] = flatten_modules(data)
            for module, tests in typed_data.items():
                test_definitions: list[AntaTestDefinition] = []
                for test_definition in tests:
                    assert isinstance(test_definition, dict), "AntaTestDefinition must be a dictionary"
                    assert len(test_definition) == 1, "AntaTestDefinition must be a dictionary with a single entry"
                    for test_name, test_inputs in test_definition.copy().items():
                        test: type[AntaTest] | None = getattr(module, test_name, None)
                        assert test, f"{test_name} is not defined in Python module {module}"
                        inputs: AntaTest.Input = test.Input(**test_inputs) if test_inputs else test.Input()
                        test_definitions.append(AntaTestDefinition(test=test, inputs=inputs))
                typed_data[module] = test_definitions
        return typed_data


class AntaCatalog:
    """
    Class representing an ANTA Catalog.

    It can be defined programmatically by providing the `tests` argument to the constructor
    or it can be loaded from a file using the `filename` argument.

    Attributes:
        filename: The path from which the catalog is loaded.
        file: The AntaCatalogFile model representinf the catalog file.
        tests: A list of tuple containing an AntaTest class and the associated input.
    """

    def __init__(self, filename: str | None = None, tests: list[AntaTestDefinition] = []) -> None:
        """
        Constructor of AntaCatalog

        Args:
            filename: The path from which the catalog is loaded. Use this argument if you want to load the catalog from a file.
            tests: A list of tuple containing an AntaTest class and the associated input. Use this argument if you want to define the catalog programmatically.
        """
        if filename is not None and tests:
            raise RuntimeError("'filename' and 'tests' arguments cannot be provided at the same time")
        self.filename: str | None = filename
        self.file: AntaCatalogFile | None = None
        self._data = None
        if self.filename:
            self._parse_file()
        self.tests: list[AntaTestDefinition] = tests

    @property
    def tests(self) -> list[AntaTestDefinition]:
        return self._tests

    @tests.setter
    def tests(self, value: list[AntaTestDefinition]) -> None:
        assert isinstance(value, list), "The catalog must contain a list of tests"
        for t in value:
            assert isinstance(t, AntaTestDefinition), "A test in the catalog must be an AntaTestDefinition instance"
        self._tests = value

    def _parse_file(self) -> None:
        """
        Parse the catalog YAML file
        """
        if self.filename:
            try:
                with open(file=self.filename, mode="r", encoding="UTF-8") as file:
                    self._data = safe_load(file)
            # pylint: disable-next=broad-exception-caught
            except Exception:
                logger.critical(f"Something went wrong while parsing {self.filename}")
                raise

    def check(self: AntaCatalog) -> None:
        """
        Check if the data in the catalog file is valid
        and populate `tests` instance attribute.
        """
        if self._data is not None:
            self.file = AntaCatalogFile(**self._data)
            if self._tests:
                logger.warning(f"Overriding AntaCatalog data from file {self.filename}")
            self._tests = []
            for tests in self.file.root.values():
                self._tests.extend(tests)

    def get_tests_by_tags(self, tags: list[str], strict: bool = False) -> list[AntaTestDefinition]:
        """
        Return all the tests that have matching tags in their input filters.
        If strict=True, returns only tests that match all the tags provided as input.
        If strict=False, return all the tests that match at least one tag provided as input.
        """
        result: list[AntaTestDefinition] = []
        for test in self.tests:
            if test.inputs.filters and (filter := test.inputs.filters.tags):
                if (strict and all(t in tags for t in filter)) or (not strict and any(t in tags for t in filter)):
                    result.append(test)
        return result

    def get_tests_by_device(self, device: AntaDevice) -> list[AntaTestDefinition]:
        """
        Return all the tests that have the provided device in their input filters.
        """
        result: list[AntaTestDefinition] = []
        for test in self.tests:
            if test.inputs.filters and (filter := test.inputs.filters.devices):
                if device.name in filter:
                    result.append(test)
        return result
