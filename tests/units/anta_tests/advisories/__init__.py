# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit-test helpers for anta.tests.advisories modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from anta.device import AntaDevice

if TYPE_CHECKING:
    from typing import Literal, TypeAlias

    from anta._advisory.remediation import RemediationPlan
    from anta.models import AntaCommand
    from anta.result_manager.models import AntaTestStatus
    from tests.units.anta_tests import AtomicResult, UnitTestResult

    AdvisoryResultStatus: TypeAlias = Literal[
        AntaTestStatus.SUCCESS,
        AntaTestStatus.FAILURE,
        AntaTestStatus.ERROR,
    ]
    AdvisoryFindingKind: TypeAlias = Literal["not affected", "mitigated", "inconclusive", "affected", "error"]


def build_expected_advisory_result(
    vulnerability_id: str,
    status: AdvisoryResultStatus,
    message: str,
    remediation: RemediationPlan | None,
    finding_kind: AdvisoryFindingKind | None = None,
) -> UnitTestResult:
    """Build matching parent and single-vulnerability atomic expectations."""
    if finding_kind is None:
        finding_kind = cast("AdvisoryFindingKind", {"success": "not affected", "failure": "affected", "error": "error"}[status.value])
    atomic_result: AtomicResult = {
        "description": f"Verify {vulnerability_id}.",
        "result": status,
        "messages": [message],
        "finding_kind": finding_kind,
    }
    if remediation is not None:
        atomic_result["remediation"] = remediation
    return {
        "result": status,
        "messages": [message],
        "remediations": [remediation] if remediation is not None else [],
        "atomic_results": [atomic_result],
    }


class OfflineAntaDevice(AntaDevice):
    """Minimal ANTA device for tests that simulate collection outcomes."""

    @property
    def _keys(self) -> tuple[Any, ...]:
        """Return the immutable key tuple used by ANTA."""
        return (self.name,)

    async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
        """Reject unexpected command collection."""
        msg = f"Unit-test device cannot collect '{command.command}'."
        raise RuntimeError(msg)

    async def refresh(self) -> None:
        """Mark the unit-test device as available."""
        self.is_online = True
        self.established = True
