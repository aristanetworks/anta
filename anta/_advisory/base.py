# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Base class for ANTA security advisory tests."""

from __future__ import annotations

import sys
from typing import ClassVar

from anta._advisory.models import AdvisoryMetadata
from anta._advisory.results import _AdvisoryTestResult
from anta.models import AntaCommand, AntaTemplate, AntaTest, _description_from_docstring

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class AntaAdvisoryTest(AntaTest):
    """Base class for ANTA security advisory tests."""

    # `_create_result` guarantees this narrower runtime type. Pyright cannot infer
    # an instance attribute's type from an overridden factory method.
    result: _AdvisoryTestResult  # pyright: ignore[reportIncompatibleVariableOverride]
    categories: ClassVar[list[str]] = ["advisories"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []
    advisory: ClassVar[AdvisoryMetadata]

    @override
    def _create_result(self) -> _AdvisoryTestResult:
        """Create a result with this test's advisory metadata."""
        return _AdvisoryTestResult(
            name=self.device.name,
            test=self.name,
            categories=self.categories,
            description=self.description,
            advisory=self.advisory,
        )

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
            cls.description = _description_from_docstring(cls.__doc__, cls.name)

        if "advisory" not in cls.__dict__:
            msg = f"Class {cls.__module__}.{cls.__name__} is missing required class attribute: advisory"
            raise AttributeError(msg)
        if not isinstance(cls.advisory, AdvisoryMetadata):
            msg = f"Class {cls.__module__}.{cls.__name__} class attribute 'advisory' must be an AdvisoryMetadata instance"
            raise TypeError(msg)
        if not cls.commands:
            msg = f"Class {cls.__module__}.{cls.__name__} must define at least one command"
            raise AttributeError(msg)
