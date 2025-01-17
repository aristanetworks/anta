# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest import mock
from unittest.mock import patch

import pytest
import yaml

from anta.catalog import AntaCatalog
from anta.device import AntaDevice, AsyncEOSDevice
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from anta.models import AntaCommand
    from anta.runner import RunnerContext

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"
DEVICE_HW_MODEL = "pytest"
DEVICE_NAME = "pytest"
COMMAND_OUTPUT = "retrieved"


@pytest.fixture(name="anta_env")
def anta_env_fixture() -> dict[str, str]:
    """Return an ANTA environment for testing."""
    return {
        "ANTA_USERNAME": "anta",
        "ANTA_PASSWORD": "formica",
        "ANTA_INVENTORY": str(Path(__file__).parent.parent / "data" / "test_inventory_with_tags.yml"),
        "ANTA_CATALOG": str(Path(__file__).parent.parent / "data" / "test_catalog.yml"),
    }


@pytest.fixture
def device(request: pytest.FixtureRequest) -> Iterator[AntaDevice]:
    """Return an AntaDevice instance with mocked abstract method."""

    def _collect(command: AntaCommand, *args: Any, **kwargs: Any) -> None:  # noqa: ARG001, ANN401
        command.output = COMMAND_OUTPUT

    kwargs = {"name": DEVICE_NAME, "hw_model": DEVICE_HW_MODEL}

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    with patch.object(AntaDevice, "__abstractmethods__", set()), patch("anta.device.AntaDevice._collect", side_effect=_collect):
        # AntaDevice constructor does not have hw_model argument
        hw_model = kwargs.pop("hw_model")
        dev = AntaDevice(**kwargs)  # type: ignore[abstract, arg-type]
        dev.hw_model = hw_model
        yield dev


@pytest.fixture
def async_device(request: pytest.FixtureRequest) -> AsyncEOSDevice:
    """Return an AsyncEOSDevice instance."""
    kwargs = {
        "name": DEVICE_NAME,
        "host": "42.42.42.42",
        "username": "anta",
        "password": "anta",
    }

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    return AsyncEOSDevice(**kwargs)  # type: ignore[arg-type]


@pytest.fixture
def yaml_file(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    """Fixture to create a temporary YAML file and return the path.

    Fixture is indirectly parametrized with the YAML file content.
    """
    assert hasattr(request, "param")
    file = tmp_path / "test_file.yaml"
    assert isinstance(request.param, dict)
    content: dict[str, Any] = request.param
    file.write_text(yaml.dump(content, allow_unicode=True))
    return file


@pytest.fixture
def runner_context(request: pytest.FixtureRequest) -> RunnerContext:
    """Fixture providing a basic RunnerContext for testing."""
    # Import must be inside fixture to prevent circular dependency from breaking CLI tests:
    # anta.runner -> anta.cli.console -> anta.cli/* (not yet loaded) -> anta.cli.anta
    from anta.runner import RunnerContext

    if not hasattr(request, "param"):
        msg = "runner_context fixture requires requires parameters"
        raise ValueError(msg)

    params = request.param

    # Check required parameters
    required_params = {"inventory", "catalog"}
    missing_params = required_params - params.keys()
    if missing_params:
        msg = f"runner_context fixture missing required parameters: {missing_params}"
        raise ValueError(msg)

    return RunnerContext(
        manager=ResultManager(),
        inventory=AntaInventory.parse(
            filename=DATA_DIR / params["inventory"],
            username="arista",
            password="arista",
            httpx_limits=params.get("httpx_limits", None),
        ),
        catalog=AntaCatalog.parse(DATA_DIR / params["catalog"]),
        devices=params.get("devices", None),
        tests=params.get("tests", None),
        tags=params.get("tags", None),
        established_only=params.get("established_only", True),
        dry_run=params.get("dry_run", False),
        max_concurrency=params.get("max_concurrency", 10000),
        file_descriptor_limit=params.get("file_descriptor_limit", 16384),
    )


@pytest.fixture
def setenvvar(monkeypatch: pytest.MonkeyPatch) -> Generator[pytest.MonkeyPatch, None, None]:
    """Fixture to set environment variables for testing."""
    with mock.patch.dict(os.environ, clear=True):
        yield monkeypatch
