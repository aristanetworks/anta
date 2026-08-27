# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Security advisory tests and their built-in ANTA catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from anta.catalog import AntaCatalog
from anta.tests.advisories.sa_117 import VerifySA117

if TYPE_CHECKING:
    from anta._advisory.base import AntaAdvisoryTest

# Keep this registry explicit: adding an advisory module also requires adding its
# test class here. The default ``anta psirt`` catalog is built from every entry.
_ADVISORY_TESTS: tuple[type[AntaAdvisoryTest], ...] = (cast("type[AntaAdvisoryTest]", VerifySA117),)


def get_catalog() -> AntaCatalog:
    """Return the catalog containing every advisory test installed with ANTA."""
    return AntaCatalog.from_list([(test, None) for test in _ADVISORY_TESTS])


__all__ = ["get_catalog"]
