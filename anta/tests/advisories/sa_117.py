# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 117."""

from __future__ import annotations

from collections.abc import Mapping
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

if TYPE_CHECKING:
    from anta._advisory.status import AdvisoryAssessment
    from anta.device import DeviceVersion
    from anta.models import AntaCommand, AntaTemplate

RISKY_TRACE_SELECTORS = (
    "service/9",
    "interceptor/9",
    "transport_socketcli/9",
)

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=30, patch_gte=1, patch_lt=10),
    VersionRule(major=4, minor=31, patch_lt=7),
    VersionRule(major=4, minor=32, patch_lt=5),
    VersionRule(major=4, minor=33, patch_lt=1),
    VersionRule(major=4, minor=33, patch_eq=1, exclude_suffixes=("FX-wbb",)),
)

FIXED_RELEASES = (
    FixedRelease("4.30.10M", "4.30"),
    FixedRelease("4.31.7M", "4.31"),
    FixedRelease("4.32.5M", "4.32"),
    FixedRelease("4.33.2F", "4.33"),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0117",
    title="Security Advisory 0117",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2025-0936",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description=("gNOI TransferToRemote credential exposure through OpenConfig accounting or tracing."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117"),
    description=(
        "On affected platforms running Arista EOS with a gNMI transport enabled, running the "
        "gNOI File TransferToRemote RPC with credentials for a remote server may cause these "
        "remote-server credentials to be logged or accounted on the local EOS device or "
        "possibly on other remote accounting servers (i.e. TACACS, RADIUS, etc)."
    ),
)


def _gnmi_transport_values(gnmi_output: Mapping[str, object]) -> tuple[object, ...] | None:
    """Return transport values from nested or flattened EOS gNMI output.

    EOS 4.33 eAPI revision 1 exposes a single transport at the top level, while
    newer schemas expose named transports below ``transports``.
    """
    if "transports" not in gnmi_output:
        enabled = gnmi_output.get("enabled")
        if not isinstance(enabled, bool):
            return None
        return (gnmi_output,) if enabled else ()

    transports = gnmi_output.get("transports")
    if not isinstance(transports, Mapping):
        return None
    return tuple(transports.values())


def _evaluate_gnmi_transport_enabled(gnmi_output: Mapping[str, object]) -> bool | None:
    """Return whether at least one gNMI transport is enabled."""
    transports = _gnmi_transport_values(gnmi_output)
    if transports is None:
        return None

    unknown = False
    for transport in transports:
        if not isinstance(transport, Mapping):
            unknown = True
            continue
        enabled = transport.get("enabled")
        if enabled is True:
            return True
        if enabled is not False:
            unknown = True

    return None if unknown else False


def _evaluate_gnmi_accounting_enabled(gnmi_output: Mapping[str, object]) -> bool | None:
    """Return whether an enabled gNMI transport has accounting enabled."""
    transports = _gnmi_transport_values(gnmi_output)
    if transports is None:
        return None

    unknown = False
    for transport in transports:
        if not isinstance(transport, Mapping):
            unknown = True
            continue
        enabled = transport.get("enabled")
        if enabled is False:
            continue
        if enabled is not True:
            unknown = True
            continue

        accounting = transport.get("accounting")
        if accounting is True:
            return True
        if accounting is not False:
            unknown = True

    return None if unknown else False


def _evaluate_risky_trace_configuration(trace_config_output: str) -> bool:
    """Return whether the narrow trace configuration contains a risky selector."""
    prefix = "trace OpenConfig setting "
    for line in trace_config_output.splitlines():
        command = line.lstrip()
        if not command.startswith(prefix):
            continue
        selectors = {selector.strip() for selector in command.removeprefix(prefix).split(",")}
        if any(selector in selectors for selector in RISKY_TRACE_SELECTORS):
            return True
    return False


# pylint: disable-next=too-many-return-statements
def _assess_sa117(  # noqa: PLR0911 - Keep the advisory decision tree explicit and auditable.
    device_version: DeviceVersion | None,
    gnmi_output: Mapping[str, object] | None,
    trace_configured: bool | None,  # noqa: FBT001 - Tri-state evidence is part of the assessment contract.
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

    if gnmi_output is None:
        return (
            AdvisoryStatus.ERROR,
            "The gNMI transport state could not be determined from 'show management api gnmi'.",
            evidence_remediation("valid 'show management api gnmi' output"),
        )

    transport_enabled = _evaluate_gnmi_transport_enabled(gnmi_output)
    if transport_enabled is None:
        return (
            AdvisoryStatus.ERROR,
            "The gNMI transport enabled state is missing or malformed.",
            evidence_remediation("valid gNMI transport enabled-state evidence"),
        )
    if not transport_enabled:
        return (
            AdvisoryStatus.NOT_AFFECTED,
            "The device is not affected because no gNMI transport is enabled.",
            no_remediation(),
        )

    accounting_enabled = _evaluate_gnmi_accounting_enabled(gnmi_output)
    if accounting_enabled is True:
        # TODO(sa117): Resolve the gNOI File and effective gNSI Authz controls.  # NOSONAR
        # Narrow EOS evidence is required before classifying this as AFFECTED or MITIGATED.
        return (
            AdvisoryStatus.INCONCLUSIVE,
            (
                "The assessment is inconclusive and the device may be affected because EOS version "
                f"'{version_evaluation.version}' has an enabled gNMI transport with accounting "
                "enabled, but the gNOI File and effective gNSI Authz controls cannot be determined."
            ),
            upgrade_remediation(FIXED_RELEASES, inconclusive=True),
        )
    if trace_configured is True:
        # TODO(sa117): Resolve the gNOI File and effective gNSI Authz controls.  # NOSONAR
        # Narrow EOS evidence is required before classifying this as AFFECTED or MITIGATED.
        return (
            AdvisoryStatus.INCONCLUSIVE,
            (
                "The assessment is inconclusive and the device may be affected because EOS version "
                f"'{version_evaluation.version}' has an enabled gNMI transport and OpenConfig "
                "tracing includes a selector identified by the advisory, but the gNOI File and "
                "effective gNSI Authz controls cannot be determined."
            ),
            upgrade_remediation(FIXED_RELEASES, inconclusive=True),
        )
    if accounting_enabled is None:
        return (
            AdvisoryStatus.ERROR,
            "The accounting state of an enabled gNMI transport is missing or malformed.",
            evidence_remediation("valid gNMI transport accounting evidence"),
        )
    if trace_configured is None:
        return (
            AdvisoryStatus.ERROR,
            "The OpenConfig trace configuration could not be determined from 'show running-config section trace'.",
            evidence_remediation("valid 'show running-config section trace' output"),
        )

    return (
        AdvisoryStatus.NOT_AFFECTED,
        "The device is not affected because enabled gNMI transports do not use accounting and no advisory-identified OpenConfig trace selector is configured.",
        no_remediation(),
    )


@preview_test_class
class VerifySA117(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Assess SA117 credential exposure through OpenConfig accounting or tracing.

    Notes
    -----
    Exposure signals remain inconclusive because disabling the gNOI File service and an
    effective gNSI Authz policy that blocks TransferToRemote cannot currently be evaluated
    with trusted narrow EOS evidence.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version or configuration is not affected.
    * Inconclusive: The test is inconclusive if exposure signals exist but required control evidence is unavailable.
    * Error: The test will error if required EOS version or configuration evidence is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_117:
      - VerifySA117:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        OptionalAntaCommand(command="show management api gnmi", revision=1),
        OptionalAntaCommand(command="show running-config section trace", ofmt="text"),
    ]
    description = "Verify whether the device is impacted by SA 0117."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project the advisory vulnerability."""
        gnmi_command = self.instance_commands[0]
        trace_command = self.instance_commands[1]

        gnmi_output = None if is_unsupported_optional_command(gnmi_command) else gnmi_command.json_output
        trace_configured = None if is_unsupported_optional_command(trace_command) else _evaluate_risky_trace_configuration(trace_command.text_output)

        status, message, remediation = _assess_sa117(
            self.device.version,
            gnmi_output,
            trace_configured,
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            vulnerability.description,
            vulnerability_ids=(vulnerability.id,),
        )
        project_advisory_status(atomic_result, status, message, remediation)
