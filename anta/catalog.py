# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Catalog related functions
"""
from __future__ import annotations

import importlib
import logging
from typing import Any, Optional, cast

from yaml import safe_load

from anta.device import AsyncEOSDevice
from anta.models import AntaTest
from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


class AntaCatalog:
    """
    Class representing an ANTA Catalog

    Attributes:
        name: Catalog name
        filename Optional[str]: The path from which the catalog was loaded
        tests: list[tuple[AntaTest, AntaTest.Input]]: A list of Tuple containing an AntaTest and the associated input
    """

    def __init__(self, name: str, filename: Optional[str] = None) -> None:
        """
        Constructor of AntaCatalog

        Args:
            name: Device name
            filname: Optional name - if provided tests are loaded
        """
        self.name: str = name
        self.filename: Optional[str] = filename
        self.tests: list[tuple[AntaTest, AntaTest.Input]] = []

    def parse_catalog_file(self: AntaCatalog) -> None:
        """
        Parse a file
        """
        if self.filename is None:
            return
        try:
            with open(self.filename, "r", encoding="UTF-8") as file:
                data = safe_load(file)
                self.parse_catalog(data)
        # pylint: disable-next=broad-exception-caught
        except Exception:
            logger.critical(f"Something went wrong while parsing {self.filename}")
            raise

    def parse_catalog(self: AntaCatalog, test_catalog: dict[str, Any], package: str | None = None) -> None:
        """
        Function to parse the catalog and return a list of tests with their inputs

        A valid test catalog must follow the following structure:
            <Python module>:
                - <AntaTest subclass>:
                    <AntaTest.Input compliant dictionary>

        Example:
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

        Also supports nesting for Python module definition:
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

        Args:
            test_catalog: Python dictionary representing the test catalog YAML file

        """
        # pylint: disable=broad-exception-raised
        if not test_catalog:
            return

        for key, value in test_catalog.items():
            # Required to manage iteration within a tests module
            if package is not None:
                key = ".".join([package, key])
            try:
                module = importlib.import_module(f"{key}")
            except ModuleNotFoundError:
                logger.critical(f"No test module named '{key}'")
                raise

            if isinstance(value, list):
                # This is a list of tests
                for test in value:
                    for test_name, inputs in test.items():
                        # A test must be a subclass of AntaTest as defined in the Python module
                        try:
                            test = getattr(module, test_name)
                        except AttributeError:
                            logger.critical(f"Wrong test name '{test_name}' in '{module.__name__}'")
                            raise
                        if not issubclass(test, AntaTest):
                            logger.critical(f"'{test.__module__}.{test.__name__}' is not an AntaTest subclass")
                            raise Exception()
                        # Test inputs can be either None or a dictionary
                        if inputs is None or isinstance(inputs, dict):
                            self.tests.append((cast(AntaTest, test), cast(AntaTest.Input, inputs)))
                        else:
                            logger.critical(f"'{test.__module__}.{test.__name__}' inputs must be a dictionary")
                            raise Exception()
            if isinstance(value, dict):
                # This is an inner Python module
                self.parse_catalog(value, package=module.__name__)

    def check(self: AntaCatalog) -> ResultManager:
        """
        TODO - for now a test requires a device but this may be revisited in the future
        """
        # Mock device
        mock_device = AsyncEOSDevice(name="mock", host="127.0.0.1", username="mock", password="mock")

        manager = ResultManager()
        # Instantiate each test to verify the Inputs are correct
        for test_class, test_inputs in self.tests:
            # TODO - this is the same code with typing as in runner.py but somehow mypy complains that test_class
            # ot type AntaTest is not callable
            test_instance = test_class(device=mock_device, inputs=test_inputs)  # type: ignore[operator]
            manager.add_test_result(test_instance.result)
        return manager
