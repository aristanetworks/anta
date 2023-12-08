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
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, ConfigDict, RootModel, ValidationError, ValidationInfo, field_validator, model_validator
from pydantic.types import ImportString
from yaml import YAMLError, safe_load

from anta.logger import anta_log_exception
from anta.models import AntaTest

logger = logging.getLogger(__name__)

# { <module_name> : [ { <test_class_name>: <input_as_dict_or_None> }, ... ] }
RawCatalogInput = Dict[str, List[Dict[str, Optional[Dict[str, Any]]]]]

# [ ( <AntaTest class>, <input_as AntaTest.Input or dict or None > ), ... ]
ListAntaTestTuples = List[Tuple[Type[AntaTest], Optional[Union[AntaTest.Input, Dict[str, Any]]]]]


class AntaTestDefinition(BaseModel):
    """
    Define a test with its associated inputs.

    test: An AntaTest concrete subclass
    inputs: The associated AntaTest.Input subclass instance
    """

    model_config = ConfigDict(frozen=True)

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
        raise ValueError(f"Coud not instantiate inputs as type {type(data).__name__} is not valid")

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

     A valid test catalog file must have the following structure:
        <Python module>:
            - <AntaTest subclass>:
                <AntaTest.Input compliant dictionary>
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
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # A test module is potentially user-defined code.
                    # We need to catch everything if we want to have meaningful logs
                    module_str = f"{module_name[1:] if module_name.startswith('.') else module_name}{f' from package {package}' if package else ''}"
                    message = f"Module named {module_str} cannot be imported. Verify that the module exists and there is no Python syntax issues."
                    anta_log_exception(e, message, logger)
                    raise ValueError(message) from e
                if isinstance(tests, dict):
                    # This is an inner Python module
                    modules.update(flatten_modules(data=tests, package=module.__name__))
                else:
                    if not isinstance(tests, list):
                        raise ValueError(f"Syntax error when parsing: {tests}\nIt must be a list of ANTA tests. Check the test catalog.")
                    # This is a list of AntaTestDefinition
                    modules[module] = tests
            return modules

        if isinstance(data, dict):
            typed_data: dict[ModuleType, list[Any]] = flatten_modules(data)
            for module, tests in typed_data.items():
                test_definitions: list[AntaTestDefinition] = []
                for test_definition in tests:
                    if not isinstance(test_definition, dict):
                        raise ValueError(f"Syntax error when parsing: {test_definition}\nIt must be a dictionary. Check the test catalog.")
                    if len(test_definition) != 1:
                        raise ValueError(
                            f"Syntax error when parsing: {test_definition}\nIt must be a dictionary with a single entry. Check the indentation in the test catalog."
                        )
                    for test_name, test_inputs in test_definition.copy().items():
                        test: type[AntaTest] | None = getattr(module, test_name, None)
                        if test is None:
                            raise ValueError(
                                f"{test_name} is not defined in Python module {module.__name__}{f' (from {module.__file__})' if module.__file__ is not None else ''}"
                            )
                        test_definitions.append(AntaTestDefinition(test=test, inputs=test_inputs))
                typed_data[module] = test_definitions
        return typed_data


class AntaCatalog:
    """
    Class representing an ANTA Catalog.

    It can be instantiated using its contructor or one of the static methods: `parse()`, `from_list()` or `from_dict()`
    """

    def __init__(self, tests: list[AntaTestDefinition] | None = None, filename: str | Path | None = None) -> None:
        """
        Constructor of AntaCatalog.

        Args:
            tests: A list of AntaTestDefinition instances.
            filename: The path from which the catalog is loaded.
        """
        self._tests: list[AntaTestDefinition] = []
        if tests is not None:
            self._tests = tests
        self._filename: Path | None = None
        if filename is not None:
            if isinstance(filename, Path):
                self._filename = filename
            else:
                self._filename = Path(filename)

    @property
    def filename(self) -> Path | None:
        """Path of the file used to create this AntaCatalog instance"""
        return self._filename

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

    @staticmethod
    def parse(filename: str | Path) -> AntaCatalog:
        """
        Create an AntaCatalog instance from a test catalog file.

        Args:
            filename: Path to test catalog YAML file
        """
        try:
            with open(file=filename, mode="r", encoding="UTF-8") as file:
                data = safe_load(file)
        except (TypeError, YAMLError, OSError) as e:
            message = f"Unable to parse ANTA Test Catalog file '{filename}'"
            anta_log_exception(e, message, logger)
            raise

        return AntaCatalog.from_dict(data, filename=filename)

    @staticmethod
    def from_dict(data: RawCatalogInput, filename: str | Path | None = None) -> AntaCatalog:
        """
        Create an AntaCatalog instance from a dictionary data structure.
        See RawCatalogInput type alias for details.
        It is the data structure returned by `yaml.load()` function of a valid
        YAML Test Catalog file.

        Args:
            data: Python dictionary used to instantiate the AntaCatalog instance
            filename: value to be set as AntaCatalog instance attribute
        """
        tests: list[AntaTestDefinition] = []
        if data is None:
            logger.warning("Catalog input data is empty")
            return AntaCatalog(filename=filename)

        if not isinstance(data, dict):
            raise ValueError(f"Wrong input type for catalog data{f' (from {filename})' if filename is not None else ''}, must be a dict, got {type(data).__name__}")

        try:
            catalog_data = AntaCatalogFile(**data)  # type: ignore[arg-type]
        except ValidationError as e:
            anta_log_exception(e, f"Test catalog is invalid!{f' (from {filename})' if filename is not None else ''}", logger)
            raise
        for t in catalog_data.root.values():
            tests.extend(t)
        return AntaCatalog(tests, filename=filename)

    @staticmethod
    def from_list(data: ListAntaTestTuples) -> AntaCatalog:
        """
        Create an AntaCatalog instance from a list data structure.
        See ListAntaTestTuples type alias for details.

        Args:
            data: Python list used to instantiate the AntaCatalog instance
        """
        tests: list[AntaTestDefinition] = []
        try:
            tests.extend(AntaTestDefinition(test=test, inputs=inputs) for test, inputs in data)
        except ValidationError as e:
            anta_log_exception(e, "Test catalog is invalid!", logger)
            raise
        return AntaCatalog(tests)

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
