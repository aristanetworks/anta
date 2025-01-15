# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils for the ANTA benchmark tests."""

from __future__ import annotations

import asyncio
import copy
import importlib
import json
import pkgutil
from typing import TYPE_CHECKING, Any

import httpx

from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import ModuleType

    from anta.device import AntaDevice


async def collect(self: AntaTest) -> None:
    """Patched anta.models.AntaTest.collect() method.

    When generating the catalog, we inject a unit test case name in the custom_field input to be able to retrieve the eos_data for this specific test.
    We use this unit test case name in the eAPI request ID.
    """
    if self.inputs.result_overwrite is None or self.inputs.result_overwrite.custom_field is None:
        msg = f"The custom_field input is not present for test {self.name}"
        raise RuntimeError(msg)
    await self.device.collect_commands(self.instance_commands, collection_id=f"{self.name}:{self.inputs.result_overwrite.custom_field}")


async def collect_commands(self: AntaDevice, commands: list[AntaCommand], collection_id: str) -> None:
    """Patched anta.device.AntaDevice.collect_commands() method.

    For the same reason as above, we inject the command index of the test to the eAPI request ID.
    """
    await asyncio.gather(*(self.collect(command=command, collection_id=f"{collection_id}:{idx}") for idx, command in enumerate(commands)))


class AntaMockEnvironment:  # pylint: disable=too-few-public-methods
    """Generate an ANTA test catalog from the unit tests data. It can be accessed using the `catalog` attribute of this class instance.

    Also provide the attribute 'eos_data_catalog` with the output of all the commands used in the test catalog.

    Each module in `tests.units.anta_tests` has a `DATA` constant.
    The `DATA` structure is a list of dictionaries used to parametrize the test. The list elements have the following keys:
    - `name` (str): Test name as displayed by Pytest.
    - `test` (AntaTest): An AntaTest subclass imported in the test module - e.g. VerifyUptime.
    - `eos_data` (list[dict]): List of data mocking EOS returned data to be passed to the test.
    - `inputs` (dict): Dictionary to instantiate the `test` inputs as defined in the class from `test`.

    The keys of `eos_data_catalog` is the tuple (DATA['test'], DATA['name']). The values are `eos_data`.
    """

    def __init__(self) -> None:
        self._catalog, self.eos_data_catalog = self._generate_catalog()
        self.tests_count = len(self._catalog.tests)

    @property
    def catalog(self) -> AntaCatalog:
        """AntaMockEnvironment object will always return a new AntaCatalog object based on the initial parsing.

        This is because AntaCatalog objects store indexes when tests are run and we want a new object each time a test is run.
        """
        return copy.deepcopy(self._catalog)

    def _generate_catalog(self) -> tuple[AntaCatalog, dict[tuple[str, str], list[dict[str, Any]]]]:
        """Generate the `catalog` and `eos_data_catalog` attributes."""

        def import_test_modules() -> Generator[ModuleType, None, None]:
            """Yield all test modules from the given package."""
            package = importlib.import_module("tests.units.anta_tests")
            prefix = package.__name__ + "."
            for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix):
                if not is_pkg and module_name.split(".")[-1].startswith("test_"):
                    module = importlib.import_module(module_name)
                    if hasattr(module, "DATA"):
                        yield module

        test_definitions = []
        eos_data_catalog = {}
        for module in import_test_modules():
            for test_data in module.DATA:
                test = test_data["test"]
                result_overwrite = AntaTest.Input.ResultOverwrite(custom_field=test_data["name"])
                if test_data.get("inputs") is None:
                    inputs = test.Input(result_overwrite=result_overwrite)
                else:
                    inputs = test.Input(**test_data["inputs"], result_overwrite=result_overwrite)
                test_definition = AntaTestDefinition(
                    test=test,
                    inputs=inputs,
                )
                eos_data_catalog[(test.__name__, test_data["name"])] = test_data["eos_data"]
                test_definitions.append(test_definition)

        return (AntaCatalog(tests=test_definitions), eos_data_catalog)

    def eapi_response(self, request: httpx.Request) -> httpx.Response:
        """Mock eAPI response.

        If the eAPI request ID has the format `ANTA-{test name}:{unit test name}:{command index}-{command ID}`,
        the function will return the eos_data from the unit test case.

        Otherwise, it will mock 'show version' command or raise an Exception.
        """
        words_count = 3

        def parse_req_id(req_id: str) -> tuple[str, str, int] | None:
            """Parse the patched request ID from the eAPI request."""
            req_id = req_id.removeprefix("ANTA-").rpartition("-")[0]
            words = req_id.split(":", words_count)
            if len(words) == words_count:
                test_name, unit_test_name, command_index = words
                return test_name, unit_test_name, int(command_index)
            return None

        jsonrpc = json.loads(request.content)
        assert jsonrpc["method"] == "runCmds"
        commands = jsonrpc["params"]["cmds"]
        ofmt = jsonrpc["params"]["format"]
        req_id: str = jsonrpc["id"]
        result = None

        # Extract the test name, unit test name, and command index from the request ID
        if (words := parse_req_id(req_id)) is not None:
            test_name, unit_test_name, idx = words

            # This should never happen, but better be safe than sorry
            if (test_name, unit_test_name) not in self.eos_data_catalog:
                msg = f"Error while generating a mock response for unit test {unit_test_name} of test {test_name}: eos_data not found"
                raise RuntimeError(msg)

            eos_data = self.eos_data_catalog[(test_name, unit_test_name)]

            # This could happen if the unit test data is not correctly defined
            if idx >= len(eos_data):
                msg = f"Error while generating a mock response for unit test {unit_test_name} of test {test_name}: missing test case in eos_data"
                raise RuntimeError(msg)
            result = {"output": eos_data[idx]} if ofmt == "text" else eos_data[idx]
        elif {"cmd": "show version"} in commands and ofmt == "json":
            # Mock 'show version' request performed during inventory refresh.
            result = {
                "modelName": "pytest",
            }

        if result is not None:
            return httpx.Response(
                status_code=200,
                json={
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": [result],
                },
            )
        msg = f"The following eAPI Request has not been mocked: {jsonrpc}"
        raise NotImplementedError(msg)
