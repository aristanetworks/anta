# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 140."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.remediation import (
    FixedRelease,
    evidence_remediation,
    no_remediation,
    upgrade_remediation,
)
from anta._advisory.status import AdvisoryStatus, project_advisory_status
from anta.decorators import preview_test_class
from anta.models import AntaCommand, AntaTemplate

if TYPE_CHECKING:
    from collections.abc import Mapping

    from anta._advisory.status import AdvisoryAssessment
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
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-10040",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="CVE-2026-10040: Secure Boot Software Image verification bypass.",
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24074-security-advisory-0140"),
    description=(
        "A user with local eos-admin privileges on affected Arista EOS (Extensible "
        "Operating System) platforms where secure boot is enabled can bypass Secure Boot "
        "Software Image (SWI) verification through the use of a specially crafted file."
    ),
)


def _is_secure_boot_supported_and_enabled(
    boot_output: Mapping[str, object],
) -> bool | None:
    """Return whether Secure Boot is both supported and enabled.

    The structured ``show boot`` fields prove the advisory's platform and configuration
    prerequisites together. Either false prerequisite is sufficient to establish a safe
    result; missing, contradictory, or malformed evidence remains unknown.
    """
    if not boot_output:
        return False

    supported = boot_output.get("securebootSupported")
    enabled = boot_output.get("securebootEnabled")

    if supported is False and enabled is True:
        return None
    if supported is False or enabled is False:
        return False
    if supported is True and enabled is True:
        return True
    return None


def _assess_sa140(
    device_version: DeviceVersion | None,
    boot_output: Mapping[str, object],
) -> AdvisoryAssessment:
    """Return the semantic vulnerability status, result message, and remediation text."""
    version_evaluation = evaluate_version(device_version, AFFECTED_VERSION_MATRIX)
    if version_evaluation.affected_status is AffectedStatus.UNKNOWN:
        return (
            AdvisoryStatus.ERROR,
            "The EOS version is unavailable from the refreshed device metadata.",
            evidence_remediation("valid refreshed device EOS version metadata"),
        )
    if version_evaluation.affected_status is AffectedStatus.NOT_AFFECTED:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            f"The device is not affected because EOS version '{version_evaluation.version}' is outside the affected releases.",
            no_remediation(),
        )

    secure_boot_exposed = _is_secure_boot_supported_and_enabled(boot_output)
    if secure_boot_exposed is None:
        return (
            AdvisoryStatus.ERROR,
            "Secure Boot support and enabled state could not be determined from 'show boot'.",
            evidence_remediation("valid 'show boot' output"),
        )
    if not secure_boot_exposed:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            "The device is not affected because Secure Boot is unsupported or disabled.",
            no_remediation(),
        )
    return (
        AdvisoryStatus.AFFECTED,
        f"The device is affected because EOS version '{version_evaluation.version}' is affected and Secure Boot is supported and enabled.",
        upgrade_remediation(FIXED_RELEASES),
    )


@preview_test_class
class VerifySA140(_AntaAdvisoryTest):
    """Verify that the advisory 140 Secure Boot exposure is absent.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version or Secure Boot state is not affected.
    * Failure: The test will fail if an affected EOS version has Secure Boot supported and enabled.
    * Error: The test will error if required EOS version or Secure Boot evidence is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_140:
      - VerifySA140:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show boot", revision=1),
    ]
    description = "Verify whether the device is impacted by SA 0140."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project the advisory vulnerability."""
        boot_command = self.instance_commands[0]
        status, message, remediation = _assess_sa140(
            self.device.version,
            boot_command.json_output,
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            vulnerability.description,
            vulnerability_ids=(vulnerability.id,),
        )
        project_advisory_status(atomic_result, status, message, remediation)
