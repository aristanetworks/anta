# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Catalog related functions."""

from __future__ import annotations

import importlib
import logging
import math
from collections import defaultdict
from inspect import isclass
from itertools import chain
from json import load as json_load
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union
from warnings import warn

from pydantic import BaseModel, ConfigDict, RootModel, ValidationError, ValidationInfo, field_validator, model_serializer, model_validator
from pydantic.types import ImportString
from pydantic_core import PydanticCustomError
from yaml import YAMLError, safe_dump, safe_load

from anta.logger import anta_log_exception
from anta.models import AntaTest

if TYPE_CHECKING:
    import sys
    from types import ModuleType

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

logger = logging.getLogger(__name__)

# { <module_name> : [ { <test_class_name>: <input_as_dict_or_None> }, ... ] }
RawCatalogInput = dict[str, list[dict[str, Optional[dict[str, Any]]]]]

# [ ( <AntaTest class>, <input_as AntaTest.Input or dict or None > ), ... ]
ListAntaTestTuples = list[tuple[type[AntaTest], Optional[Union[AntaTest.Input, dict[str, Any]]]]]


class AntaTestDefinition(BaseModel):
    """Define a test with its associated inputs.

    Attributes
    ----------
    test
        An AntaTest concrete subclass.
    inputs
        The associated AntaTest.Input subclass instance.
    """

    model_config = ConfigDict(frozen=True)

    test: type[AntaTest]
    inputs: AntaTest.Input

    @model_serializer()
    def serialize_model(self) -> dict[str, AntaTest.Input]:
        """Serialize the AntaTestDefinition model.

        The dictionary representing the model will be look like:
        ```
        <AntaTest subclass name>:
                <AntaTest.Input compliant dictionary>
        ```

        Returns
        -------
        dict
            A dictionary representing the model.
        """
        return {self.test.__name__: self.inputs}

    def __init__(self, **data: type[AntaTest] | AntaTest.Input | dict[str, Any] | None) -> None:
        """Inject test in the context to allow to instantiate Input in the BeforeValidator.

        https://docs.pydantic.dev/2.0/usage/validators/#using-validation-context-with-basemodel-initialization.
        """
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context={"test": data["test"]},
        )
        super(BaseModel, self).__init__()

    @field_validator("inputs", mode="before")
    @classmethod
    def instantiate_inputs(
        cls: type[AntaTestDefinition],
        data: AntaTest.Input | dict[str, Any] | None,
        info: ValidationInfo,
    ) -> AntaTest.Input:
        """Ensure the test inputs can be instantiated and thus are valid.

        If the test has no inputs, allow the user to omit providing the `inputs` field.
        If the test has inputs, allow the user to provide a valid dictionary of the input fields.
        This model validator will instantiate an Input class from the `test` class field.
        """
        if info.context is None:
            msg = "Could not validate inputs as no test class could be identified"
            raise ValueError(msg)
        # Pydantic guarantees at this stage that test_class is a subclass of AntaTest because of the ordering
        # of fields in the class definition - so no need to check for this
        test_class = info.context["test"]
        if not (isclass(test_class) and issubclass(test_class, AntaTest)):
            msg = f"Could not validate inputs as no test class {test_class} is not a subclass of AntaTest"
            raise ValueError(msg)

        if isinstance(data, AntaTest.Input):
            return data
        try:
            if data is None:
                return test_class.Input()
            if isinstance(data, dict):
                return test_class.Input(**data)
        except ValidationError as e:
            inputs_msg = str(e).replace("\n", "\n\t")
            err_type = "wrong_test_inputs"
            raise PydanticCustomError(
                err_type,
                f"{test_class.name} test inputs are not valid: {inputs_msg}\n",
                {"errors": e.errors()},
            ) from e
        msg = f"Could not instantiate inputs as type {type(data).__name__} is not valid"
        raise ValueError(msg)

    @model_validator(mode="after")
    def check_inputs(self) -> Self:
        """Check the `inputs` field typing.

        The `inputs` class attribute needs to be an instance of the AntaTest.Input subclass defined in the class `test`.
        """
        if not isinstance(self.inputs, self.test.Input):
            msg = f"Test input has type {self.inputs.__class__.__qualname__} but expected type {self.test.Input.__qualname__}"
            raise ValueError(msg)  # noqa: TRY004 pydantic catches ValueError or AssertionError, no TypeError
        return self


class AntaCatalogFile(RootModel[dict[ImportString[Any], list[AntaTestDefinition]]]):  # pylint: disable=too-few-public-methods
    """Represents an ANTA Test Catalog File.

    Example
    -------
    A valid test catalog file must have the following structure:
    ```
    <Python module>:
        - <AntaTest subclass>:
            <AntaTest.Input compliant dictionary>
    ```

    """

    root: dict[ImportString[Any], list[AntaTestDefinition]]

    @staticmethod
    def flatten_modules(data: dict[str, Any], package: str | None = None) -> dict[ModuleType, list[Any]]:
        """Allow the user to provide a data structure with nested Python modules.

        Example
        -------
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
                # PLW2901 - we redefine the loop variable on purpose here.
                module_name = f".{module_name}"  # noqa: PLW2901
            try:
                module: ModuleType = importlib.import_module(name=module_name, package=package)
            except Exception as e:
                # A test module is potentially user-defined code.
                # We need to catch everything if we want to have meaningful logs
                module_str = f"{module_name[1:] if module_name.startswith('.') else module_name}{f' from package {package}' if package else ''}"
                message = f"Module named {module_str} cannot be imported. Verify that the module exists and there is no Python syntax issues."
                anta_log_exception(e, message, logger)
                raise ValueError(message) from e
            if isinstance(tests, dict):
                # This is an inner Python module
                modules.update(AntaCatalogFile.flatten_modules(data=tests, package=module.__name__))
            elif isinstance(tests, list):
                # This is a list of AntaTestDefinition
                modules[module] = tests
            else:
                msg = f"Syntax error when parsing: {tests}\nIt must be a list of ANTA tests. Check the test catalog."
                raise ValueError(msg)  # noqa: TRY004 pydantic catches ValueError or AssertionError, no TypeError
        return modules

    # ANN401 - Any ok for this validator as we are validating the received data
    # and cannot know in advance what it is.
    @model_validator(mode="before")
    @classmethod
    def check_tests(cls: type[AntaCatalogFile], data: Any) -> Any:  # noqa: ANN401
        """Allow the user to provide a Python data structure that only has string values.

        This validator will try to flatten and import Python modules, check if the tests classes
        are actually defined in their respective Python module and instantiate Input instances
        with provided value to validate test inputs.
        """
        if isinstance(data, dict):
            if not data:
                return data
            typed_data: dict[ModuleType, list[Any]] = AntaCatalogFile.flatten_modules(data)
            for module, tests in typed_data.items():
                test_definitions: list[AntaTestDefinition] = []
                for test_definition in tests:
                    if isinstance(test_definition, AntaTestDefinition):
                        test_definitions.append(test_definition)
                        continue
                    if not isinstance(test_definition, dict):
                        msg = f"Syntax error when parsing: {test_definition}\nIt must be a dictionary. Check the test catalog."
                        raise ValueError(msg)  # noqa: TRY004 pydantic catches ValueError or AssertionError, no TypeError
                    if len(test_definition) != 1:
                        msg = (
                            f"Syntax error when parsing: {test_definition}\n"
                            "It must be a dictionary with a single entry. Check the indentation in the test catalog."
                        )
                        raise ValueError(msg)
                    for test_name, test_inputs in test_definition.copy().items():
                        test: type[AntaTest] | None = getattr(module, test_name, None)
                        if test is None:
                            msg = (
                                f"{test_name} is not defined in Python module {module.__name__}"
                                f"{f' (from {module.__file__})' if module.__file__ is not None else ''}"
                            )
                            raise ValueError(msg)
                        test_definitions.append(AntaTestDefinition(test=test, inputs=test_inputs))
                typed_data[module] = test_definitions
            return typed_data
        return data

    def yaml(self) -> str:
        """Return a YAML representation string of this model.

        Returns
        -------
        str
            The YAML representation string of this model.
        """
        # TODO: Pydantic and YAML serialization/deserialization is not supported natively.
        # This could be improved.
        # https://github.com/pydantic/pydantic/issues/1043
        # Explore if this worth using this: https://github.com/NowanIlfideme/pydantic-yaml
        return safe_dump(safe_load(self.model_dump_json(serialize_as_any=True, exclude_unset=True)), indent=2, width=math.inf)

    def to_json(self) -> str:
        """Return a JSON representation string of this model.

        Returns
        -------
        str
            The JSON representation string of this model.
        """
        return self.model_dump_json(serialize_as_any=True, exclude_unset=True, indent=2)


class AntaCatalog:
    """Class representing an ANTA Catalog.

    It can be instantiated using its constructor or one of the static methods: `parse()`, `from_list()` or `from_dict()`
    """

    def __init__(
        self,
        tests: list[AntaTestDefinition] | None = None,
        filename: str | Path | None = None,
    ) -> None:
        """Instantiate an AntaCatalog instance.

        Parameters
        ----------
        tests
            A list of AntaTestDefinition instances.
        filename
            The path from which the catalog is loaded.

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

        self.indexes_built: bool
        self.tag_to_tests: defaultdict[str | None, set[AntaTestDefinition]]
        self._init_indexes()

    def _init_indexes(self) -> None:
        """Init indexes related variables."""
        self.tag_to_tests = defaultdict(set)
        self.indexes_built = False

    @property
    def filename(self) -> Path | None:
        """Path of the file used to create this AntaCatalog instance."""
        return self._filename

    @property
    def tests(self) -> list[AntaTestDefinition]:
        """List of AntaTestDefinition in this catalog."""
        return self._tests

    @tests.setter
    def tests(self, value: list[AntaTestDefinition]) -> None:
        if not isinstance(value, list):
            msg = "The catalog must contain a list of tests"
            raise TypeError(msg)
        for t in value:
            if not isinstance(t, AntaTestDefinition):
                msg = "A test in the catalog must be an AntaTestDefinition instance"
                raise TypeError(msg)
        self._tests = value

    @staticmethod
    def parse(filename: str | Path, file_format: Literal["yaml", "json"] = "yaml") -> AntaCatalog:
        """Create an AntaCatalog instance from a test catalog file.

        Parameters
        ----------
        filename
            Path to test catalog YAML or JSON file.
        file_format
            Format of the file, either 'yaml' or 'json'.

        Returns
        -------
        AntaCatalog
            An AntaCatalog populated with the file content.
        """
        if file_format not in ["yaml", "json"]:
            message = f"'{file_format}' is not a valid format for an AntaCatalog file. Only 'yaml' and 'json' are supported."
            raise ValueError(message)

        try:
            file: Path = filename if isinstance(filename, Path) else Path(filename)
            with file.open(encoding="UTF-8") as f:
                data = safe_load(f) if file_format == "yaml" else json_load(f)
        except (TypeError, YAMLError, OSError, ValueError) as e:
            message = f"Unable to parse ANTA Test Catalog file '{filename}'"
            anta_log_exception(e, message, logger)
            raise

        return AntaCatalog.from_dict(data, filename=filename)

    @staticmethod
    def from_dict(data: RawCatalogInput, filename: str | Path | None = None) -> AntaCatalog:
        """Create an AntaCatalog instance from a dictionary data structure.

        See RawCatalogInput type alias for details.
        It is the data structure returned by `yaml.load()` function of a valid
        YAML Test Catalog file.

        Parameters
        ----------
        data
            Python dictionary used to instantiate the AntaCatalog instance.
        filename
            value to be set as AntaCatalog instance attribute

        Returns
        -------
        AntaCatalog
            An AntaCatalog populated with the 'data' dictionary content.
        """
        tests: list[AntaTestDefinition] = []
        if data is None:
            logger.warning("Catalog input data is empty")
            return AntaCatalog(filename=filename)

        if not isinstance(data, dict):
            msg = f"Wrong input type for catalog data{f' (from {filename})' if filename is not None else ''}, must be a dict, got {type(data).__name__}"
            raise TypeError(msg)

        try:
            catalog_data = AntaCatalogFile(data)  # type: ignore[arg-type]
        except ValidationError as e:
            anta_log_exception(
                e,
                f"Test catalog is invalid!{f' (from {filename})' if filename is not None else ''}",
                logger,
            )
            raise
        for t in catalog_data.root.values():
            tests.extend(t)
        return AntaCatalog(tests, filename=filename)

    @staticmethod
    def from_list(data: ListAntaTestTuples) -> AntaCatalog:
        """Create an AntaCatalog instance from a list data structure.

        See ListAntaTestTuples type alias for details.

        Parameters
        ----------
        data
            Python list used to instantiate the AntaCatalog instance.

        Returns
        -------
        AntaCatalog
            An AntaCatalog populated with the 'data' list content.
        """
        tests: list[AntaTestDefinition] = []
        try:
            tests.extend(AntaTestDefinition(test=test, inputs=inputs) for test, inputs in data)
        except ValidationError as e:
            anta_log_exception(e, "Test catalog is invalid!", logger)
            raise
        return AntaCatalog(tests)

    @classmethod
    def merge_catalogs(cls, catalogs: list[AntaCatalog]) -> AntaCatalog:
        """Merge multiple AntaCatalog instances.

        Parameters
        ----------
        catalogs
            A list of AntaCatalog instances to merge.

        Returns
        -------
        AntaCatalog
            A new AntaCatalog instance containing the tests of all the input catalogs.
        """
        combined_tests = list(chain(*(catalog.tests for catalog in catalogs)))
        return cls(tests=combined_tests)

    def merge(self, catalog: AntaCatalog) -> AntaCatalog:
        """Merge two AntaCatalog instances.

        Warning
        -------
        This method is deprecated and will be removed in ANTA v2.0. Use `AntaCatalog.merge_catalogs()` instead.

        Parameters
        ----------
        catalog
            AntaCatalog instance to merge to this instance.

        Returns
        -------
        AntaCatalog
            A new AntaCatalog instance containing the tests of the two instances.
        """
        # TODO: Use a decorator to deprecate this method instead. See https://github.com/aristanetworks/anta/issues/754
        warn(
            message="AntaCatalog.merge() is deprecated and will be removed in ANTA v2.0. Use AntaCatalog.merge_catalogs() instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return self.merge_catalogs([self, catalog])

    def dump(self) -> AntaCatalogFile:
        """Return an AntaCatalogFile instance from this AntaCatalog instance.

        Returns
        -------
        AntaCatalogFile
            An AntaCatalogFile instance containing tests of this AntaCatalog instance.
        """
        root: dict[ImportString[Any], list[AntaTestDefinition]] = {}
        for test in self.tests:
            # Cannot use AntaTest.module property as the class is not instantiated
            root.setdefault(test.test.__module__, []).append(test)
        return AntaCatalogFile(root=root)

    def build_indexes(self, filtered_tests: set[str] | None = None) -> None:
        """Indexes tests by their tags for quick access during filtering operations.

        If a `filtered_tests` set is provided, only the tests in this set will be indexed.

        This method populates the tag_to_tests attribute, which is a dictionary mapping tags to sets of tests.

        Once the indexes are built, the `indexes_built` attribute is set to True.
        """
        for test in self.tests:
            # Skip tests that are not in the specified filtered_tests set
            if filtered_tests and test.test.name not in filtered_tests:
                continue

            # Indexing by tag
            if test.inputs.filters and (test_tags := test.inputs.filters.tags):
                for tag in test_tags:
                    self.tag_to_tests[tag].add(test)
            else:
                self.tag_to_tests[None].add(test)

        self.indexes_built = True

    def clear_indexes(self) -> None:
        """Clear this AntaCatalog instance indexes."""
        self._init_indexes()

    def get_tests_by_tags(self, tags: set[str], *, strict: bool = False) -> set[AntaTestDefinition]:
        """Return all tests that match a given set of tags, according to the specified strictness.

        Parameters
        ----------
        tags
            The tags to filter tests by. If empty, return all tests without tags.
        strict
            If True, returns only tests that contain all specified tags (intersection).
            If False, returns tests that contain any of the specified tags (union).

        Returns
        -------
        set[AntaTestDefinition]
            A set of tests that match the given tags.

        Raises
        ------
        ValueError
            If the indexes have not been built prior to method call.
        """
        if not self.indexes_built:
            msg = "Indexes have not been built yet. Call build_indexes() first."
            raise ValueError(msg)
        if not tags:
            return self.tag_to_tests[None]

        filtered_sets = [self.tag_to_tests[tag] for tag in tags if tag in self.tag_to_tests]
        if not filtered_sets:
            return set()

        if strict:
            return set.intersection(*filtered_sets)
        return set.union(*filtered_sets)
