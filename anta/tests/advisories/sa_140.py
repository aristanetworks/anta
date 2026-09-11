# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 140."""

from __future__ import annotations

from datetime import date

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact, SecureBootFact
from anta._advisory.facts.models import (
    Fact,
    FeatureState,
    FeatureValue,
    UnavailableFact,
)
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
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
    software_version_plan,
)
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=35, patch_lte=1),
    VersionRule(major=4, minor=34, patch_lte=5),
    VersionRule(major=4, minor=33, patch_lte=7),
    VersionRule(major=4, minor=32, patch_lte=9),
    VersionRule(major=4, minor=31, patch_lte=10),
    VersionRule(major=4, minor=30, patch_lte=10),
)

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 32, 10, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 2, suffix="F")),
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
    version_fact: Fact[EOSVersion],
    secure_boot: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Return a structured conclusion from normalized SA140 facts."""
    release = assess_eos_scope(VULNERABILITY_ID, version_fact, AFFECTED_VERSION_MATRIX)
    if not isinstance(release, EosReleaseAssessment):
        return release

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
        context=(release,),
        conditions=(secure_boot,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA140(_AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0140.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version or Secure Boot state is not affected.
    * Failure: The test will fail if an affected EOS version has Secure Boot supported and enabled.
    * Error: The test will error if the EOS version or Secure Boot state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA140:
    ```
    """

    advisory = ADVISORY
    required_facts = (EosVersionFact, SecureBootFact)
    description = "Verify whether the device is impacted by Security Advisory 0140."
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
