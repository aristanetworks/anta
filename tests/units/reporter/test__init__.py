# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test deprecated exports from anta.reporter."""

from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import patch

import pytest

import anta.reporter as reporter_module
from anta.reporter.jinja_reporter import ReportJinja
from anta.reporter.table_reporter import ReportTable


def test_canonical_imports_do_not_warn() -> None:
    """Canonical reporter imports do not emit deprecation warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        from anta.reporter.jinja_reporter import ReportJinja as CanonicalReportJinja
        from anta.reporter.table_reporter import ReportTable as CanonicalReportTable

    assert CanonicalReportJinja is ReportJinja
    assert CanonicalReportTable is ReportTable


@pytest.mark.parametrize(
    ("name", "canonical_class", "replacement_module"),
    [
        pytest.param("ReportJinja", ReportJinja, "anta.reporter.jinja_reporter", id="jinja"),
        pytest.param("ReportTable", ReportTable, "anta.reporter.table_reporter", id="table"),
    ],
)
def test_deprecated_root_export(name: str, canonical_class: type[Any], replacement_module: str) -> None:
    """Root reporter exports warn and return the canonical class object."""
    warning = rf"`{name}` has been moved\. Import it from `{replacement_module}`\. Direct import from `anta\.reporter` will be removed in ANTA v2\.0\.0\."
    with pytest.warns(DeprecationWarning, match=warning):
        assert getattr(reporter_module, name) is canonical_class


def test_deprecated_root_import() -> None:
    """The legacy from-import remains available with a warning."""
    with pytest.warns(DeprecationWarning, match=r"`ReportTable` has been moved\. Import it from `anta\.reporter\.table_reporter`"):
        from anta.reporter import ReportTable as LegacyReportTable

    assert LegacyReportTable is ReportTable


def test_deprecated_root_patch() -> None:
    """The legacy root path remains usable by patching tools."""
    with (
        pytest.warns(DeprecationWarning, match=r"`ReportTable` has been moved\. Import it from `anta\.reporter\.table_reporter`"),
        patch("anta.reporter.ReportTable.generate_expanded") as mocked_generate_expanded,
    ):
        assert mocked_generate_expanded is ReportTable.generate_expanded


def test_deprecated_root_export_warning_as_error() -> None:
    """Warning-as-error users receive the deprecation as an exception."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with pytest.raises(DeprecationWarning, match=r"`ReportJinja` has been moved\. Import it from `anta\.reporter\.jinja_reporter`"):
            _ = reporter_module.ReportJinja


def test_deprecated_root_exports_are_discoverable() -> None:
    """Deprecated exports remain available through discovery and wildcard imports."""
    assert {"ReportJinja", "ReportTable"}.issubset(dir(reporter_module))

    namespace: dict[str, Any] = {}
    with pytest.warns(DeprecationWarning, match=r"`(?:ReportJinja|ReportTable)` has been moved\. Import it from `anta\.reporter\.(?:jinja|table)_reporter`"):
        # pylint: disable-next=exec-used
        exec("from anta.reporter import *", namespace)  # noqa: S102

    assert namespace["ReportJinja"] is ReportJinja
    assert namespace["ReportTable"] is ReportTable


def test_unknown_attribute() -> None:
    """Unknown reporter attributes continue to raise AttributeError."""
    with pytest.raises(AttributeError, match=r"module 'anta.reporter' has no attribute 'UnknownReporter'"):
        _ = reporter_module.UnknownReporter
