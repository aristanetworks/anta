# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
import yaml

from anta.device import AntaDevice, AsyncEOSDevice

if TYPE_CHECKING:
    from collections.abc import Iterator

    from anta.models import AntaCommand

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
