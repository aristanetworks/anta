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

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from anta._runner import AntaRunner
    from anta.models import AntaCommand

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
def anta_runner(request: pytest.FixtureRequest) -> AntaRunner:
    """AntaRunner fixture.

    Must be parametrized with a dictionary containing the following keys:
    - inventory: Inventory file name from the data directory
    - catalog: Catalog file name from the data directory

    Optional keys:
    - manager: ResultManager instance
    - max_concurrency: Maximum concurrency limit
    - nofile: File descriptor limit
    """
    # Import must be inside fixture to prevent circular dependency from breaking CLI tests:
    # anta.runner -> anta.cli.console -> anta.cli/* (not yet loaded) -> anta.cli.anta
    from anta._runner import AntaRunner
    from anta.settings import AntaRunnerSettings

    if not hasattr(request, "param"):
        msg = "anta_runner fixture requires a parameter dictionary"
        raise ValueError(msg)

    params = request.param

    # Check required parameters
    required_params = {"inventory", "catalog"}
    missing_params = required_params - params.keys()
    if missing_params:
        msg = f"runner_context fixture missing required parameters: {missing_params}"
        raise ValueError(msg)

    # Build AntaRunner fields
    runner_fields = {
        "inventory": AntaInventory.parse(
            filename=DATA_DIR / params["inventory"],
            username="arista",
            password="arista",
        ),
        "catalog": AntaCatalog.parse(DATA_DIR / params["catalog"]),
        "manager": params.get("manager", None),
    }

    # Build AntaRunnerSettings fields
    settings_fields = {}
    if "max_concurrency" in params:
        settings_fields["max_concurrency"] = params["max_concurrency"]
    if "nofile" in params:
        settings_fields["nofile"] = params["nofile"]

    runner = AntaRunner(**runner_fields)
    runner._settings = AntaRunnerSettings(**settings_fields)
    return runner


@pytest.fixture
def setenvvar(monkeypatch: pytest.MonkeyPatch) -> Generator[pytest.MonkeyPatch, None, None]:
    """Fixture to set environment variables for testing."""
    with mock.patch.dict(os.environ, clear=True):
        yield monkeypatch
