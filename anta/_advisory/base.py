# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Base class for ANTA security advisory tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from anta._advisory.models import AdvisoryMetadata
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import _TestResultMetadata

if TYPE_CHECKING:
    from anta.device import AntaDevice


class AntaAdvisoryTest(AntaTest):
    """Base class for ANTA security advisory tests."""

    categories: ClassVar[list[str]] = ["advisories"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []
    advisory: ClassVar[AdvisoryMetadata]

    def __init__(
        self,
        device: AntaDevice,
        inputs: dict[str, Any] | AntaTest.Input | None = None,
        eos_data: list[dict[str, Any] | str] | None = None,
    ) -> None:
        """Initialize an advisory test and attach its metadata to the result."""
        super().__init__(device=device, inputs=inputs, eos_data=eos_data)
        self.result._metadata = _TestResultMetadata(security_advisory=self.advisory)  # noqa: SLF001

    def __init_subclass__(cls) -> None:
        """Set subclass identity and validate required advisory attributes."""
        has_own_name = "name" in cls.__dict__
        has_own_description = "description" in cls.__dict__
        super().__init_subclass__()

        # AntaTest uses inherited attributes when resolving these values. Reset
        # them so each advisory subclass reflects its own class declaration.
        if not has_own_name:
            cls.name = cls.__name__
        if not has_own_description:
            if not cls.__doc__ or cls.__doc__.strip() == "":
                msg = f"Cannot set the description for class {cls.name}, either set it in the class definition or add a docstring to the class."
                raise AttributeError(msg)
            cls.description = cls.__doc__.split(sep="\n", maxsplit=1)[0]

        if "advisory" not in cls.__dict__:
            msg = f"Class {cls.__module__}.{cls.__name__} is missing required class attribute: advisory"
            raise AttributeError(msg)
        if not isinstance(cls.advisory, AdvisoryMetadata):
            msg = f"Class {cls.__module__}.{cls.__name__} class attribute 'advisory' must be an AdvisoryMetadata instance"
            raise TypeError(msg)
        if not cls.commands:
            msg = f"Class {cls.__module__}.{cls.__name__} must define at least one command"
            raise AttributeError(msg)
