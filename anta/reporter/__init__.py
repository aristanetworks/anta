# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Report management for ANTA."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Final, TypeAlias

from anta.reporter.jinja_reporter import ReportJinja as _ReportJinja
from anta.reporter.table_reporter import ReportTable as _ReportTable

if TYPE_CHECKING:
    from anta.reporter.jinja_reporter import ReportJinja
    from anta.reporter.table_reporter import ReportTable

__all__ = ["ReportJinja", "ReportTable"]

_ReporterType: TypeAlias = type[_ReportJinja] | type[_ReportTable]

# TODO(ANTA 2.0): Remove the deprecated root reporter exports and their compatibility helpers.
_DEPRECATED_REPORTERS: Final[dict[str, tuple[_ReporterType, str]]] = {
    "ReportJinja": (_ReportJinja, "anta.reporter.jinja_reporter"),
    "ReportTable": (_ReportTable, "anta.reporter.table_reporter"),
}


def __getattr__(name: str) -> _ReporterType:
    """Return a deprecated root reporter export with a migration warning."""
    try:
        reporter, replacement_module = _DEPRECATED_REPORTERS[name]
    except KeyError:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg) from None

    warnings.warn(
        f"`{name}` has been moved. Import it from `{replacement_module}`. Direct import from `anta.reporter` will be removed in ANTA v2.0.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return reporter


def __dir__() -> list[str]:
    """Include deprecated root reporter exports in module discovery."""
    return sorted(set(globals()) | set(__all__))
