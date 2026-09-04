# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 140."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact, SecureBootFact
from anta._advisory.facts.models import (
    Fact,
    FactProblemKind,
    FeatureState,
    FeatureValue,
    UnavailableFact,
)
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.remediation import (
    FixedRelease,
    upgrade_remediation,
)
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta.device import DeviceVersion

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=35, patch_lte=1),
    VersionRule(major=4, minor=34, patch_lte=5),
    VersionRule(major=4, minor=33, patch_lte=7),
    VersionRule(major=4, minor=32, patch_lte=9),
    VersionRule(major=4, minor=31, patch_lte=10),
    VersionRule(major=4, minor=30, patch_lte=10),
)

FIXED_RELEASES = (
    FixedRelease("4.32.10M", "4.32"),
    FixedRelease("4.33.8M", "4.33"),
    FixedRelease("4.34.6M", "4.34"),
    FixedRelease("4.35.2F", "4.35"),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0140",
    title="Security Advisory 0140",
    last_updated=date(2026, 6, 3),
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-10040",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Secure Boot Software Image verification bypass.",
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24074-security-advisory-0140"),
    description=(
        "A user with local eos-admin privileges on affected Arista EOS (Extensible "
        "Operating System) platforms where secure boot is enabled can bypass Secure Boot "
        "Software Image (SWI) verification through the use of a specially crafted file."
    ),
)

VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa140(
    version_fact: Fact[DeviceVersion],
    secure_boot: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Return a structured conclusion from normalized SA140 facts."""
    if isinstance(version_fact, UnavailableFact):
        return ErrorResult(
            vulnerability_id=VULNERABILITY_ID,
            problems=(version_fact,),
        )
    version_evaluation = evaluate_version(version_fact.value, AFFECTED_VERSION_MATRIX)
    if version_evaluation.affected_status is AffectedStatus.UNKNOWN:
        problem = EosVersionFact.unavailable(FactProblemKind.INVALID, version_fact.source)
        return ErrorResult(
            vulnerability_id=VULNERABILITY_ID,
            problems=(problem,),
        )

    if version_evaluation.affected_status is AffectedStatus.NOT_AFFECTED:
        return NotAffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            decisive=(EosReleaseAssessment(version_fact, VersionRelation.OUTSIDE_SCOPE),),
        )

    if isinstance(secure_boot, UnavailableFact):
        return ErrorResult(
            vulnerability_id=VULNERABILITY_ID,
            problems=(secure_boot,),
        )

    if secure_boot.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            decisive=(secure_boot,),
        )

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(EosReleaseAssessment(version_fact, VersionRelation.AFFECTED),),
        conditions=(secure_boot,),
        remediation=upgrade_remediation(FIXED_RELEASES),
    )


@preview_test_class
class VerifySA140(_AntaAdvisoryTest):
    """Verify that the advisory 140 Secure Boot exposure is absent.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version or Secure Boot state is not affected.
    * Failure: The test will fail if an affected EOS version has Secure Boot supported and enabled.
    * Error: The test will error if the EOS version or Secure Boot state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_140:
      - VerifySA140:
    ```
    """

    advisory = ADVISORY
    required_facts = (EosVersionFact, SecureBootFact)
    description = "Verify whether the device is impacted by SA 0140."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Normalize command and inventory inputs, assess facts, and project the finding."""
        finding = _assess_sa140(
            self.fact(EosVersionFact),
            self.fact(SecureBootFact),
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_vulnerability_result(atomic_result, finding)
