# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 147."""

# ruff: noqa: PLR2004 - Numeric literals below are EOS/package boundaries and CLI indentation levels.

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.optional_commands import (
    OptionalAntaCommand,
    OptionalCommandsMixin,
    is_unsupported_optional_command,
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
    from anta._advisory.status import AdvisoryAssessment
    from anta.device import DeviceVersion

OPENSSH_VERSION_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)(?:p(?P<patch>\d+))?(?:[^\d].*)?$")
SSH_SHUTDOWN_DIRECTIVES = {"shutdown", "no shutdown"}
SSH_ENABLED_DIRECTIVE = "no shutdown"

CVE_60002_FIXED_RELEASES = (
    FixedRelease("4.35.6M", "4.35"),
    FixedRelease("4.34.8M", "4.34"),
)
EOS_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_lte=1),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_lt=33),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0147",
    title="Security Advisory 0147",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-59995",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="CVE-2026-59995: SFTP client issue when connecting to an untrusted server.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-59996",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description=("CVE-2026-59996: SCP remote-to-remote client issue involving an untrusted server."),
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-60001",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="CVE-2026-60001: OpenSSH server issue affecting accepted SSH connections.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-60002",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description=("CVE-2026-60002: SSH client issue when connecting to a malicious or compromised server."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24515-security-advisory-0147"),
    description=(
        "Multiple vulnerabilities have been discovered in OpenSSH before version 10.4, which "
        "is shipped with multiple Arista products. One vulnerability (CVE-2026-60001) affects "
        "the server-side SSH daemon (sshd). The remaining three vulnerabilities "
        "(CVE-2026-60002, CVE-2026-59995, CVE-2026-59996) affect the client-side SSH, Secure "
        "File Transfer Protocol (SFTP), and Secure Copy Protocol (SCP) utilities, respectively."
    ),
)


def _extract_package_version(show_version_output: Mapping[str, object], package_name: str) -> str | None:
    """Extract one package version from structured ``show version detail`` output."""
    details = show_version_output.get("details")
    if not isinstance(details, Mapping):
        return None
    packages = details.get("packages")
    if not isinstance(packages, Mapping):
        return None
    package = packages.get(package_name)
    if not isinstance(package, Mapping):
        return None
    version = package.get("version")
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


def _is_openssh_before_10_4(version_string: str) -> bool | None:
    """Return whether an OpenSSH package version is older than upstream 10.4."""
    match = OPENSSH_VERSION_PATTERN.fullmatch(version_string.strip())
    if match is None:
        return None
    return (int(match.group("major")), int(match.group("minor"))) < (10, 4)


@dataclass
class _SshConfigState:
    """Track effective global and per-VRF SSH shutdown state."""

    global_enabled: bool = True
    global_state_seen: bool = False
    vrf_states: dict[str, bool] = field(default_factory=dict)
    vrf_state_seen: set[str] = field(default_factory=set)

    def set_global_state(self, directive: str) -> bool:
        """Apply one global shutdown directive, rejecting duplicates."""
        if self.global_state_seen:
            return False
        self.global_enabled = directive == SSH_ENABLED_DIRECTIVE
        self.global_state_seen = True
        return True

    def add_vrf(self, name: str) -> bool:
        """Add one VRF with its default enabled state, rejecting invalid names."""
        if not name or name in self.vrf_states:
            return False
        self.vrf_states[name] = True
        return True

    def set_vrf_state(self, name: str, directive: str) -> bool:
        """Apply one VRF shutdown directive, rejecting duplicates."""
        if name in self.vrf_state_seen:
            return False
        self.vrf_states[name] = directive == SSH_ENABLED_DIRECTIVE
        self.vrf_state_seen.add(name)
        return True

    def accepts_connections(self) -> bool:
        """Return the effective SSH listener state across global and VRF scopes."""
        return any(self.vrf_states.values()) or self.global_enabled


def _parse_global_ssh_line(line: str, state: _SshConfigState) -> tuple[str | None, bool]:
    """Parse one line at global management-SSH indentation."""
    if line in SSH_SHUTDOWN_DIRECTIVES:
        return None, state.set_global_state(line)
    if not line.startswith("vrf "):
        return None, True
    vrf_name = line.removeprefix("vrf ").strip()
    return vrf_name, state.add_vrf(vrf_name)


def _parse_vrf_ssh_line(line: str, vrf_name: str, state: _SshConfigState) -> bool:
    """Parse one line at management-SSH VRF indentation."""
    return line not in SSH_SHUTDOWN_DIRECTIVES or state.set_vrf_state(vrf_name, line)


def _parse_ssh_line(raw_line: str, current_vrf: str | None, state: _SshConfigState) -> tuple[str | None, bool]:
    """Parse one meaningful management-SSH line and return the active VRF scope."""
    line = raw_line.strip()
    indentation = len(raw_line) - len(raw_line.lstrip())
    if indentation == 3:
        return _parse_global_ssh_line(line, state)
    if indentation == 6 and current_vrf is not None:
        return current_vrf, _parse_vrf_ssh_line(line, current_vrf, state)
    valid = line not in SSH_SHUTDOWN_DIRECTIVES and indentation >= 3
    return current_vrf, valid


def _ssh_accepts_connections(config_output: str) -> bool | None:
    """Infer whether SSH accepts connections from its narrow running-config section.

    SSH is enabled for all VRFs by default, so an empty section is enabled. An explicit
    global ``shutdown`` disables that default, while any VRF without an explicit
    ``shutdown`` remains enabled. Unknown syntax is ignored only when it cannot alter the
    shutdown state; contradictory or structurally malformed state remains unknown.
    """
    meaningful_lines = [line for line in config_output.splitlines() if line.strip() not in {"", "!"}]
    if not meaningful_lines:
        return True
    if meaningful_lines[0].strip() != "management ssh":
        return None

    state = _SshConfigState()
    current_vrf: str | None = None

    for raw_line in meaningful_lines[1:]:
        current_vrf, valid = _parse_ssh_line(raw_line, current_vrf, state)
        if not valid:
            return None

    return state.accepts_connections()


def _strict_host_key_checking_enabled(config_output: str) -> bool | None:
    """Return the effective strict host-key checking state from the SSH section."""
    meaningful_lines = [line for line in config_output.splitlines() if line.strip() not in {"", "!"}]
    if not meaningful_lines:
        return False
    if meaningful_lines[0].strip() != "management ssh":
        return None

    state: bool | None = None
    state_seen = False
    for raw_line in meaningful_lines[1:]:
        line = raw_line.strip()
        indentation = len(raw_line) - len(raw_line.lstrip())
        if indentation < 3:
            return None
        if line not in {
            "hostkey client strict-checking",
            "no hostkey client strict-checking",
        }:
            continue
        if indentation != 3 or state_seen:
            return None
        state = line == "hostkey client strict-checking"
        state_seen = True
    return state if state_seen else False


def _evaluate_eos_applicability(device_version: DeviceVersion | None) -> bool | None:
    """Return whether EOS is within the affected range shared by all four CVEs."""
    evaluation = evaluate_version(device_version, EOS_AFFECTED_VERSION_MATRIX)
    if evaluation.affected_status is AffectedStatus.UNKNOWN:
        return None
    return evaluation.affected_status is AffectedStatus.AFFECTED


def _eos_scope_assessment(*, eos_affected: bool | None) -> AdvisoryAssessment | None:
    """Return an early assessment when EOS applicability is unknown or not affected."""
    if eos_affected is None:
        return (
            AdvisoryStatus.ERROR,
            "The EOS version applicability is unavailable from the refreshed device metadata.",
            evidence_remediation("valid refreshed device EOS version metadata"),
        )
    if not eos_affected:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            "The device is not affected because its EOS version is outside the published affected range.",
            no_remediation(),
        )
    return None


def _assess_client_issue(  # noqa: PLR0911 - Keep the vulnerability decision tree explicit and auditable.
    *,
    package_version: str | None,
    action: str,
    fixed_releases: tuple[FixedRelease, ...] = (),
    eos_affected: bool | None = True,
    mitigated: bool = False,
    mitigation_evidence_unavailable: bool = False,
) -> AdvisoryAssessment:
    """Return one client vulnerability's status, result message, and remediation text."""
    if (scope_assessment := _eos_scope_assessment(eos_affected=eos_affected)) is not None:
        return scope_assessment
    if package_version is None:
        return (
            AdvisoryStatus.ERROR,
            "The openssh-clients package version could not be determined from 'show version detail'.",
            evidence_remediation("valid openssh-clients package evidence"),
        )
    affected = _is_openssh_before_10_4(package_version)
    if affected is None:
        return (
            AdvisoryStatus.ERROR,
            f"The openssh-clients package version '{package_version}' could not be interpreted.",
            evidence_remediation("a valid openssh-clients package version"),
        )
    if not affected:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            f"The device is not affected because openssh-clients '{package_version}' is fixed.",
            no_remediation(),
        )
    if mitigated:
        return (
            AdvisoryStatus.MITIGATED,
            f"The device is affected but mitigated because openssh-clients '{package_version}' uses strict host-key checking.",
            upgrade_remediation(fixed_releases),
        )
    if mitigation_evidence_unavailable:
        return (
            AdvisoryStatus.ERROR,
            "The strict host-key checking state could not be determined from the management SSH configuration.",
            evidence_remediation("valid management SSH configuration evidence"),
        )
    return (
        AdvisoryStatus.INCONCLUSIVE,
        f"The assessment is inconclusive and the device may be affected because openssh-clients '{package_version}' is affected, but {action} cannot be determined.",
        upgrade_remediation(fixed_releases, inconclusive=True),
    )


def _assess_server_issue(  # noqa: PLR0911 - Keep the vulnerability decision tree explicit and auditable.
    package_version: str | None,
    ssh_config_output: str,
    *,
    ssh_command_unsupported: bool,
    eos_affected: bool | None = True,
) -> AdvisoryAssessment:
    """Return the server vulnerability's status, result message, and remediation text."""
    if (scope_assessment := _eos_scope_assessment(eos_affected=eos_affected)) is not None:
        return scope_assessment
    ssh_enabled = None if ssh_command_unsupported else _ssh_accepts_connections(ssh_config_output)
    if ssh_enabled is False:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            "The device is not affected because SSH management access is disabled entirely.",
            no_remediation(),
        )
    if package_version is None:
        return (
            AdvisoryStatus.ERROR,
            "The openssh-server package version could not be determined from 'show version detail'.",
            evidence_remediation("valid openssh-server package evidence"),
        )
    affected = _is_openssh_before_10_4(package_version)
    if affected is None:
        return (
            AdvisoryStatus.ERROR,
            f"The openssh-server package version '{package_version}' could not be interpreted.",
            evidence_remediation("a valid openssh-server package version"),
        )
    if not affected:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            f"The device is not affected because openssh-server '{package_version}' is fixed.",
            no_remediation(),
        )
    if ssh_command_unsupported:
        return (
            AdvisoryStatus.ERROR,
            "SSH management state is unavailable because 'show running-config section management ssh' is unsupported.",
            evidence_remediation("SSH management enabled-state evidence"),
        )
    if ssh_enabled is None:
        return (
            AdvisoryStatus.ERROR,
            "Whether SSH accepts connections could not be determined from the management SSH configuration.",
            evidence_remediation("valid management SSH configuration evidence"),
        )
    return (
        AdvisoryStatus.AFFECTED,
        f"The device is affected because openssh-server '{package_version}' is affected and SSH accepts connections.",
        upgrade_remediation(()),
    )


@preview_test_class
class VerifySA147(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify the four independent OpenSSH issues in Security Advisory 147.

    Expected Results
    ----------------
    * Success: The test will pass if every vulnerability is not affected.
    * Failure: The test will fail if any vulnerability is affected.
    * Inconclusive: The test is inconclusive if evidence only establishes a mitigation or possible exposure.
    * Error: The test will error if evidence required for a vulnerability is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_147:
      - VerifySA147:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show version detail", revision=1),
        OptionalAntaCommand(command="show running-config section management ssh", ofmt="text"),
    ]
    description = "Verify whether the device is impacted by SA 0147."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project each OpenSSH vulnerability independently."""
        version_output = self.instance_commands[0].json_output
        ssh_command = self.instance_commands[1]
        ssh_command_unsupported = is_unsupported_optional_command(ssh_command)
        ssh_config_output = "" if ssh_command_unsupported else ssh_command.text_output
        ssh_state = None if ssh_command_unsupported else _ssh_accepts_connections(ssh_config_output)
        strict_host_key_checking = None if ssh_command_unsupported else _strict_host_key_checking_enabled(ssh_config_output)
        client_version = _extract_package_version(version_output, "openssh-clients")
        server_version = _extract_package_version(version_output, "openssh-server")
        eos_affected = _evaluate_eos_applicability(self.device.version)
        assessments = (
            _assess_client_issue(
                package_version=client_version,
                action="operator-initiated SFTP use with an untrusted server",
                eos_affected=eos_affected,
            ),
            _assess_client_issue(
                package_version=client_version,
                action="operator-initiated SCP remote-to-remote use with an untrusted server",
                eos_affected=eos_affected,
            ),
            _assess_server_issue(
                server_version,
                ssh_config_output,
                ssh_command_unsupported=ssh_command_unsupported,
                eos_affected=eos_affected,
            ),
            _assess_client_issue(
                package_version=client_version,
                action="operator-initiated SSH use with a malicious or compromised server",
                fixed_releases=CVE_60002_FIXED_RELEASES,
                eos_affected=eos_affected,
                mitigated=strict_host_key_checking is True,
                mitigation_evidence_unavailable=(ssh_command_unsupported or ssh_state is None or strict_host_key_checking is None),
            ),
        )
        for vulnerability, (status, message, remediation) in zip(ADVISORY.vulnerabilities, assessments, strict=True):
            atomic_result = self.result.add(
                vulnerability.description,
                vulnerability_ids=(vulnerability.id,),
            )
            project_advisory_status(atomic_result, status, message, remediation)
