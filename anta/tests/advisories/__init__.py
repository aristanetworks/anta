# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Security advisory tests and their built-in ANTA catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from anta.catalog import AntaCatalog
from anta.tests.advisories.sa_117 import SA117
from anta.tests.advisories.sa_140 import SA140
from anta.tests.advisories.sa_142 import SA142
from anta.tests.advisories.sa_146 import SA146
from anta.tests.advisories.sa_147 import SA147

if TYPE_CHECKING:
    from anta._advisory.base import _AntaAdvisoryTest

# Keep this registry explicit: adding an advisory module also requires adding its
# test class here. The default ``anta psirt`` catalog is built from every entry.
_ADVISORY_TESTS: tuple[type[_AntaAdvisoryTest], ...] = tuple(cast("type[_AntaAdvisoryTest]", test) for test in (SA117, SA140, SA142, SA146, SA147))


def get_catalog() -> AntaCatalog:
    """Return the catalog containing every advisory test installed with ANTA."""
    return AntaCatalog.from_list([(test, None) for test in _ADVISORY_TESTS])


__all__ = ["get_catalog"]
