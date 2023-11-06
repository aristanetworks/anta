# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Catalog related functions
"""
from __future__ import annotations

import importlib
import logging
from inspect import isclass
from types import ModuleType
from typing import Any, Dict, List, Type

from pydantic import BaseModel, RootModel, ValidationInfo, field_validator, model_serializer, model_validator
from pydantic.types import ImportString
from yaml import safe_load, YAMLError

from anta.device import AntaDevice
from anta.models import AntaTest

logger = logging.getLogger(__name__)


class AntaTestDefinition(BaseModel):
    """
    Define a test with its associated inputs.

    test: An AntaTest concrete subclass
    inputs: The associated AntaTest.Input subclass instance
    """

    test: Type[AntaTest]
    inputs: AntaTest.Input

    def __init__(self, **data: Any) -> None:
        """
        Inject test in the context to allow to instantiate Input in the BeforeValidator
        https://docs.pydantic.dev/2.0/usage/validators/#using-validation-context-with-basemodel-initialization
        """
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context={"test": data["test"]},
        )
        super(BaseModel, self).__init__()

    @model_serializer
    def ser_model(self) -> Dict[str, AntaTest.Input]:
        """
        Serialize an AntaTestDefinition as it is defined in a test catalog YAML file.
        """
        return {self.test.__name__: self.inputs}

    @field_validator("inputs", mode="before")
    @classmethod
    def instantiate_inputs(cls, data: AntaTest.Input | dict[str, Any] | None, info: ValidationInfo) -> AntaTest.Input:
        """
        If the test has no inputs, allow the user to omit providing the `inputs` field.
        If the test has inputs, allow the user to provide a valid dictionary of the input fields.
        This model validator will instantiate an Input class from the `test` class field.
        """
        if info.context is None:
            raise ValueError("Could not validate inputs as no test class could be identified")
        # Pydantic guarantees at this stage that test_class is a subclass of AntaTest because of the ordering
        # of fields in the class definition - so no need to check for this
        test_class = info.context["test"]
        if not (isclass(test_class) and issubclass(test_class, AntaTest)):
            raise ValueError(f"Could not validate inputs as no test class {test_class} is not a subclass of AntaTest")

        if data is None:
            return test_class.Input()
        if isinstance(data, AntaTest.Input):
            return data
        if isinstance(data, dict):
            return test_class.Input(**data)
        raise ValueError(f"Coud not instantiate inputs as type {type(data)} is not valid")

    @model_validator(mode="after")
    def check_inputs(self) -> "AntaTestDefinition":
        """
        The `inputs` class attribute needs to be an instance of the AntaTest.Input subclass defined in the class `test`.
        """
        if not isinstance(self.inputs, self.test.Input):
            raise ValueError(f"Test input has type {self.inputs.__class__.__qualname__} but expected type {self.test.Input.__qualname__}")
        return self


class AntaCatalogFile(RootModel[Dict[ImportString[Any], List[AntaTestDefinition]]]):  # pylint: disable=too-few-public-methods
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

    root: Dict[ImportString[Any], List[AntaTestDefinition]]

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
                try:
                    module: ModuleType = importlib.import_module(name=module_name, package=package)
                except ModuleNotFoundError as e:
                    module_str = module_name[1:] if module_name.startswith(".") else module_name
                    if package:
                        module_str += f" from package {package}"
                    raise ValueError(f"Module named {module_str} cannot be imported") from e
                if isinstance(tests, dict):
                    # This is an inner Python module
                    modules.update(flatten_modules(data=tests, package=module.__name__))
                else:
                    if not isinstance(tests, list):
                        raise ValueError(f"{tests} must be a list of AntaTestDefinition")
                    # This is a list of AntaTestDefinition
                    modules[module] = tests
            return modules

        if isinstance(data, dict):
            typed_data: dict[ModuleType, list[Any]] = flatten_modules(data)
            for module, tests in typed_data.items():
                test_definitions: list[AntaTestDefinition] = []
                for test_definition in tests:
                    if not isinstance(test_definition, dict):
                        raise ValueError("AntaTestDefinition must be a dictionary")
                    if len(test_definition) != 1:
                        raise ValueError("AntaTestDefinition must be a dictionary with a single entry")
                    for test_name, test_inputs in test_definition.copy().items():
                        test: type[AntaTest] | None = getattr(module, test_name, None)
                        if test is None:
                            raise ValueError(f"{test_name} is not defined in Python module {module}")
                        test_definitions.append(AntaTestDefinition(test=test, inputs=test_inputs))
                typed_data[module] = test_definitions
        return typed_data


class AntaCatalog:
    """
    Class representing an ANTA Catalog.

    It can be defined programmatically by providing the `tests` argument to the constructor
    or it can be loaded from a file using the `filename` argument.

    Attributes:
        filename: The path from which the catalog is loaded.
        tests: A list of tuple containing an AntaTest class and the associated input.
        file: The AntaCatalogFile model representing the catalog file.
    """

    def __init__(self, filename: str | None = None, tests: list[tuple[type[AntaTest], AntaTest.Input | dict[str, Any] | None]] | None = None) -> None:
        """
        Constructor of AntaCatalog

        Args:
            filename: The path from which the catalog is loaded. Use this argument if you want to load the catalog from a file.
            tests: A list of tuple containing an AntaTest class and the associated input. Use this argument if you want to define the catalog programmatically.
        """
        if filename is not None and tests:
            raise RuntimeError("'filename' and 'tests' arguments cannot be provided at the same time")
        self.filename: str | None = filename
        self._tests: list[AntaTestDefinition] = []
        if tests is not None:
            self._tests.extend(AntaTestDefinition(test=test, inputs=inputs) for test, inputs in tests)
        self.file: AntaCatalogFile | None = None
        if self.filename:
            self._parse_file()

    @property
    def tests(self) -> list[AntaTestDefinition]:
        """List of AntaTestDefinition in this catalog"""
        return self._tests

    @tests.setter
    def tests(self, value: list[AntaTestDefinition]) -> None:
        if not isinstance(value, list):
            raise ValueError("The catalog must contain a list of tests")
        for t in value:
            if not isinstance(t, AntaTestDefinition):
                raise ValueError("A test in the catalog must be an AntaTestDefinition instance")
        self._tests = value

    def _parse_file(self) -> None:
        """
        Parse the catalog YAML file

        TODO add a flag to prevent override ?
        """
        if self.filename:
            try:
                with open(file=self.filename, mode="r", encoding="UTF-8") as file:
                    data = safe_load(file)
            except YAMLError:
                logger.critical(f"Something went wrong while parsing {self.filename}")
                raise
        self.file = AntaCatalogFile(**data)
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
            if test.inputs.filters and (f := test.inputs.filters.tags):
                if (strict and all(t in tags for t in f)) or (not strict and any(t in tags for t in f)):
                    result.append(test)
        return result

    def get_tests_by_device(self, device: AntaDevice) -> list[AntaTestDefinition]:
        """
        Return all the tests that have the provided device in their input filters.
        """
        result: list[AntaTestDefinition] = []
        for test in self.tests:
            if test.inputs.filters and (f := test.inputs.filters.devices):
                if device.name in f:
                    result.append(test)
        return result
