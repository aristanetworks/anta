# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Security advisory tests and their built-in ANTA catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from anta.catalog import AntaCatalog
from anta.tests.advisories.sa_117 import VerifySA117
from anta.tests.advisories.sa_140 import VerifySA140
from anta.tests.advisories.sa_142 import VerifySA142
from anta.tests.advisories.sa_146 import VerifySA146
from anta.tests.advisories.sa_147 import VerifySA147

if TYPE_CHECKING:
    from anta._advisory.base import _AntaAdvisoryTest

# Keep this registry explicit: adding an advisory module also requires adding its
# test class here. The default ``anta psirt`` catalog is built from every entry.
_ADVISORY_TESTS: tuple[type[_AntaAdvisoryTest], ...] = tuple(
    cast("type[_AntaAdvisoryTest]", test) for test in (VerifySA117, VerifySA140, VerifySA142, VerifySA146, VerifySA147)
)


def get_catalog() -> AntaCatalog:
    """Return the catalog containing every advisory test installed with ANTA."""
    return AntaCatalog.from_list([(test, None) for test in _ADVISORY_TESTS])


__all__ = ["get_catalog"]
