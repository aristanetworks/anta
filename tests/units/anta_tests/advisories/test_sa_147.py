# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, F811
# pylint: disable=missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 147."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ComponentSoftwareVersion,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureValue,
    MitigationState,
    MitigationValue,
)
from anta._advisory.facts.software import OpenSshClientVersionFact, OpenSshServerVersionFact
from anta._advisory.facts.ssh import SshServerFact, StrictHostKeyCheckingFact, _parse_ssh_listener_state, _parse_strict_host_key_checking
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, MitigatedResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_147 import (
    ADVISORY,
    EOS_AFFECTED_VERSION_MATRIX,
    VerifySA147,
    _assess_client_issue,
    _assess_server_issue,
    _is_openssh_before_10_4,
)
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.device import DeviceVersion
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult


def version_output(
    *,
    eos: str = "4.35.5M",
    client: object = "9.9p1",
    server: object = "9.9p1",
) -> dict[str, Any]:
    """Return compact structured ``show version detail`` output."""
    packages: dict[str, object] = {}
    if client is not None:
        packages["openssh-clients"] = {"version": client}
    if server is not None:
        packages["openssh-server"] = {"version": server}
    return {"version": eos, "details": {"packages": packages}}


def sa147_eos_data(version: dict[str, Any], ssh_config: str) -> list[dict[str, Any] | str]:
    """Return production command data in required-fact declaration order."""
    return [version, version, ssh_config, ssh_config]


SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)


def eos_version_fact(version: str | None) -> Fact[DeviceVersion]:
    """Build an EOS version fact for semantic assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return EosVersionFact.available(cast("DeviceVersion", parse_eos_version(version)), SOURCE)


def component_version_fact(
    definition: type[OpenSshClientVersionFact | OpenSshServerVersionFact],
    version: str | None,
) -> Fact[ComponentSoftwareVersion]:
    """Build an OpenSSH package-version fact for semantic assessment tests."""
    if version is None:
        return definition.unavailable(FactProblemKind.MISSING, SOURCE)
    return definition.available(ComponentSoftwareVersion(definition.component_name, version), SOURCE)


def ssh_server_fact(config: str, *, unsupported: bool = False) -> Fact[FeatureValue]:
    """Parse the SSH server fact from test configuration or an unsupported command."""
    command = SshServerFact.command.model_copy()
    command.output = None if unsupported else config
    command.errors = ["This command is not supported on this hardware platform"] if unsupported else []
    return SshServerFact.parse(command)


ProductionStatus: TypeAlias = Literal[
    AntaTestStatus.SUCCESS,
    AntaTestStatus.INCONCLUSIVE,
    AntaTestStatus.FAILURE,
    AntaTestStatus.ERROR,
]
IssueExpectation: TypeAlias = tuple[str, ProductionStatus, str]


def expected_result(
    status: ProductionStatus,
    issues: tuple[IssueExpectation, ...],
) -> UnitTestResult:
    """Build parent and per-vulnerability expectations for one production case."""
    parent_remediations: list[str] = []
    seen_remediations: set[tuple[object, str]] = set()
    for index, (_, _, remediation) in enumerate(issues):
        if not remediation:
            continue
        # SFTP and SCP share their remediation. Identical evidence-remediation strings
        # are also shared across issues. CVE-2026-60002 otherwise has different fixed
        # releases, even where the compact expectation uses the same substring.
        group: object = "evidence" if remediation.startswith("Collect or correct") else (0 if index < 2 else index)
        key = (group, remediation)
        if key not in seen_remediations:
            parent_remediations.append(remediation)
            seen_remediations.add(key)
    return {
        "result": status,
        "messages": [message for message, _, _ in issues],
        "remediations": parent_remediations,
        "atomic_results": [
            {
                "description": f"Verify {vulnerability.id}.",
                "result": issue_status,
                "messages": [message],
                "remediations": [remediation] if remediation else [],
            }
            for vulnerability, (message, issue_status, remediation) in zip(ADVISORY.vulnerabilities, issues, strict=True)
        ],
    }


INCONCLUSIVE_SFTP = (
    "The assessment is inconclusive and the device may be affected. Indications: openssh-clients "
    "'9.9p1' is affected. Unresolved: operator-initiated SFTP use with an untrusted server is operator action."
)
INCONCLUSIVE_SCP = (
    "The assessment is inconclusive and the device may be affected. Indications: openssh-clients "
    "'9.9p1' is affected. Unresolved: operator-initiated SCP remote-to-remote use with an untrusted server is operator action."
)
INCONCLUSIVE_SSH = (
    "The assessment is inconclusive and the device may be affected. Indications: openssh-clients "
    "'9.9p1' is affected. Unresolved: operator-initiated SSH use with a malicious or compromised server is operator action."
)
SERVER_AFFECTED = "The device is affected because EOS version '4.35.5M' is affected, openssh-server '9.9p1' is affected, and the SSH feature is enabled."
CLIENT_PACKAGE_ERROR = "The test could not determine the OpenSSH client version because the 'show version detail' output is incomplete."
SSH_STATE_ERROR = "The test could not determine the SSH server state because the 'show running-config section management ssh' output is invalid."
STRICT_CHECKING_ERROR = (
    "The test could not determine the SSH client strict host-key checking because the 'show running-config section management ssh' output is invalid."
)
EOS_NOT_AFFECTED = "The device is not affected because EOS version '4.35.6M' is outside the affected releases."
EOS_VERSION_ERROR = "The test could not determine the EOS version because it is missing from device metadata."

_DATA: AntaUnitTestData = {
    (VerifySA147, "failure-vulnerable-packages"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa147_eos_data(version_output(), ""),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (SERVER_AFFECTED, AntaTestStatus.FAILURE, "Upgrade to"),
                (INCONCLUSIVE_SSH, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
            ),
        ),
    },
    (VerifySA147, "success-fixed-upstream-packages"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa147_eos_data(version_output(client="10.4p1", server="10.4p1"), ""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (
                    "The device is not affected because openssh-clients '10.4p1' is fixed",
                    AntaTestStatus.SUCCESS,
                    "",
                ),
                (
                    "The device is not affected because openssh-clients '10.4p1' is fixed",
                    AntaTestStatus.SUCCESS,
                    "",
                ),
                (
                    "The device is not affected because openssh-server '10.4p1' is fixed",
                    AntaTestStatus.SUCCESS,
                    "",
                ),
                (
                    "The device is not affected because openssh-clients '10.4p1' is fixed",
                    AntaTestStatus.SUCCESS,
                    "",
                ),
            ),
        ),
    },
    (VerifySA147, "inconclusive-ssh-disabled-only-resolves-server-cve"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa147_eos_data(version_output(), "management ssh\n   shutdown"),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (
                    "The device is not affected because the SSH feature is disabled.",
                    AntaTestStatus.SUCCESS,
                    "",
                ),
                (INCONCLUSIVE_SSH, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
            ),
        ),
    },
    (VerifySA147, "failure-strict-host-key-checking-mitigates-one-cve"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa147_eos_data(version_output(), "management ssh\n   hostkey client strict-checking"),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (SERVER_AFFECTED, AntaTestStatus.FAILURE, "Upgrade to"),
                (
                    (
                        "The device is affected but mitigated because EOS version '4.35.5M' is affected and openssh-clients "
                        "'9.9p1' is affected and SSH client strict host-key checking is effective."
                    ),
                    AntaTestStatus.INCONCLUSIVE,
                    "Upgrade to",
                ),
            ),
        ),
    },
    (VerifySA147, "success-eos-outside-published-affected-range"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": sa147_eos_data(version_output(eos="4.35.6M"), ""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
            ),
        ),
    },
    (VerifySA147, "error-missing-eos-version"): {
        "version": None,
        "eos_data": sa147_eos_data(version_output(), ""),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, ""),
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, ""),
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, ""),
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, ""),
            ),
        ),
    },
    (VerifySA147, "error-missing-client-package-has-parent-precedence"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa147_eos_data(version_output(client=None, server="9.9p1"), ""),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (
                    CLIENT_PACKAGE_ERROR,
                    AntaTestStatus.ERROR,
                    "",
                ),
                (
                    CLIENT_PACKAGE_ERROR,
                    AntaTestStatus.ERROR,
                    "",
                ),
                (SERVER_AFFECTED, AntaTestStatus.FAILURE, "Upgrade to"),
                (
                    CLIENT_PACKAGE_ERROR,
                    AntaTestStatus.ERROR,
                    "",
                ),
            ),
        ),
    },
    (VerifySA147, "success-fixed-eos-ignores-unneeded-evidence"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": sa147_eos_data(version_output(eos="4.35.6M", client=None, server=None), "management ssh\n   shutdown"),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
                (EOS_NOT_AFFECTED, AntaTestStatus.SUCCESS, ""),
            ),
        ),
    },
    (VerifySA147, "error-malformed-ssh-state-is-issue-specific"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa147_eos_data(version_output(), "unexpected output"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (
                    SSH_STATE_ERROR,
                    AntaTestStatus.ERROR,
                    "",
                ),
                (
                    STRICT_CHECKING_ERROR,
                    AntaTestStatus.ERROR,
                    "",
                ),
            ),
        ),
    },
}


class TestSA147Evidence(unittest.TestCase):
    """Validate package and SSH configuration evidence helpers."""

    def test_openssh_boundaries(self) -> None:
        for version, expected in (
            ("9.9p1", True),
            ("10.3p99", True),
            ("10.4", False),
            ("10.4p1", False),
            ("11.0p1", False),
            ("OpenSSH_9.9", None),
            ("", None),
        ):
            with self.subTest(version=version):
                assert _is_openssh_before_10_4(version) is expected

    def test_extract_package_version(self) -> None:
        command = OpenSshClientVersionFact.command.model_copy()
        command.output = version_output()
        parsed = OpenSshClientVersionFact.parse(command)
        assert isinstance(parsed, AvailableFact)
        assert parsed.value == ComponentSoftwareVersion("openssh-clients", "9.9p1")
        assert parsed.source == FactSource(command.command, FactSourceKind.COMMAND)
        command.output = {}
        assert OpenSshClientVersionFact.parse(command) == OpenSshClientVersionFact.unavailable(
            FactProblemKind.MISSING, FactSource(command.command, FactSourceKind.COMMAND)
        )
        command.output = version_output(client=99)
        assert OpenSshClientVersionFact.parse(command) == OpenSshClientVersionFact.unavailable(
            FactProblemKind.MALFORMED, FactSource(command.command, FactSourceKind.COMMAND)
        )

    def test_ssh_default_and_explicit_states(self) -> None:
        for config, expected in (
            ("", True),
            ("management ssh\n   hostkey client strict-checking", True),
            ("management ssh\n   shutdown", False),
            ("management ssh\n   shutdown\n   vrf MGMT\n      no shutdown", True),
            ("management ssh\n   no shutdown\n   vrf MGMT\n      shutdown", True),
            ("management ssh\n   shutdown\n   vrf MGMT\n      shutdown", False),
            ("unexpected\n   shutdown", None),
            ("management ssh\nshutdown", None),
            ("management ssh\n      shutdown", None),
            ("management ssh\n   shutdown\n   no shutdown", None),
            ("management ssh\n   vrf MGMT\n      shutdown\n      no shutdown", None),
            ("management ssh\n   vrf MGMT\n   vrf MGMT", None),
        ):
            with self.subTest(config=config):
                assert _parse_ssh_listener_state(config) is expected

    def test_strict_host_key_checking(self) -> None:
        assert _parse_strict_host_key_checking("management ssh\n   hostkey client strict-checking")
        assert not _parse_strict_host_key_checking("management ssh")
        assert not _parse_strict_host_key_checking("management ssh\n   no hostkey client strict-checking")
        assert _parse_strict_host_key_checking("unexpected output") is None
        assert _parse_strict_host_key_checking("management ssh\n   hostkey client strict-checking\n   no hostkey client strict-checking") is None

    def test_published_eos_affected_ranges(self) -> None:
        for version, expected in (
            ("4.36.2F", True),
            ("4.36.3F", False),
            ("4.35.5M", True),
            ("4.35.6M", False),
            ("4.34.7.1M", True),
            ("4.34.7.2M", False),
            ("4.34.8M", False),
            ("4.33.10M", True),
            ("4.33.11M", False),
            ("4.32.99M", True),
            ("4.37.0F", False),
        ):
            with self.subTest(version=version):
                parsed_version = parse_eos_version(version)
                evaluation = evaluate_version(parsed_version, EOS_AFFECTED_VERSION_MATRIX)
                assert (evaluation.affected_status is AffectedStatus.AFFECTED) is expected


class TestSA147Assessment(unittest.TestCase):
    """Validate each vulnerability's semantic classification before projection."""

    def test_operator_dependent_client_issue_is_inconclusive(self) -> None:
        result = _assess_client_issue(
            vulnerability_id="CVE-test",
            eos_version=eos_version_fact("4.35.5M"),
            package_version=component_version_fact(OpenSshClientVersionFact, "9.9p1"),
            action="operator behavior",
        )

        assert isinstance(result, InconclusiveResult)
        assert result.unresolved[0].subject == "operator behavior"
        assert "unresolved condition" in result.remediation

    def test_client_issue_fixed_mitigated_and_error_states(self) -> None:
        fixed = _assess_client_issue(
            vulnerability_id="CVE-test",
            eos_version=eos_version_fact("4.35.5M"),
            package_version=component_version_fact(OpenSshClientVersionFact, "10.4p1"),
            action="operator behavior",
        )
        eos_fixed = _assess_client_issue(
            vulnerability_id="CVE-test",
            eos_version=eos_version_fact("4.35.6M"),
            package_version=component_version_fact(OpenSshClientVersionFact, None),
            action="operator behavior",
        )
        mitigated = _assess_client_issue(
            vulnerability_id="CVE-test",
            eos_version=eos_version_fact("4.35.5M"),
            package_version=component_version_fact(OpenSshClientVersionFact, "9.9p1"),
            action="operator behavior",
            mitigation=StrictHostKeyCheckingFact.available(MitigationValue("SSH client strict host-key checking", MitigationState.EFFECTIVE), SOURCE),
        )
        missing_mitigation = _assess_client_issue(
            vulnerability_id="CVE-test",
            eos_version=eos_version_fact("4.35.5M"),
            package_version=component_version_fact(OpenSshClientVersionFact, "9.9p1"),
            action="operator behavior",
            mitigation=StrictHostKeyCheckingFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        )
        missing_package = _assess_client_issue(
            vulnerability_id="CVE-test",
            eos_version=eos_version_fact("4.35.5M"),
            package_version=component_version_fact(OpenSshClientVersionFact, None),
            action="operator behavior",
        )

        assert isinstance(fixed, NotAffectedResult)
        assert isinstance(eos_fixed, NotAffectedResult)
        assert isinstance(mitigated, MitigatedResult)
        assert "Upgrade to" in mitigated.remediation
        assert "strict host-key checking" not in mitigated.remediation
        assert "http" not in mitigated.remediation
        assert isinstance(missing_mitigation, ErrorResult)
        assert isinstance(missing_package, ErrorResult)

    def test_server_issue_states_and_safe_short_circuits(self) -> None:
        def assess(package: str | None, config: str, *, unsupported: bool = False) -> VulnerabilityResult:
            return _assess_server_issue(
                vulnerability_id="CVE-test",
                eos_version=eos_version_fact("4.35.5M"),
                package_version=component_version_fact(OpenSshServerVersionFact, package),
                ssh_server=ssh_server_fact(config, unsupported=unsupported),
            )

        assert isinstance(assess(None, "management ssh\n   shutdown"), NotAffectedResult)
        assert isinstance(assess("10.4p1", "", unsupported=True), NotAffectedResult)
        assert isinstance(assess("9.9p1", ""), AffectedResult)
        assert isinstance(assess("9.9p1", "", unsupported=True), ErrorResult)
        assert isinstance(assess("9.9p1", "unexpected output"), ErrorResult)


class TestVerifySA147(unittest.IsolatedAsyncioTestCase):
    """Validate independent vulnerability projection and parent aggregation."""

    async def run_test(
        self,
        *,
        ssh_config: str = "",
        version: dict[str, Any] | None = None,
    ) -> VerifySA147:
        """Run the ANTA test with synthetic EOS output in declaration order."""
        device = OfflineAntaDevice("unit-test")
        detail_output = version if version is not None else version_output()
        eos_version = detail_output.get("version")
        device.version = parse_eos_version(eos_version) if isinstance(eos_version, str) else None
        await device.refresh()
        eos_data = sa147_eos_data(detail_output, ssh_config)
        test = cast("Any", VerifySA147)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_error_atomic_results_preserve_vulnerability_associations(self) -> None:
        test = await self.run_test(version=version_output(client=None, server="9.9p1"))

        assert [_get_atomic_vulnerability_ids(result) for result in test.result.atomic_results] == [
            ("CVE-2026-59995",),
            ("CVE-2026-59996",),
            ("CVE-2026-60001",),
            ("CVE-2026-60002",),
        ]

    async def test_unsupported_optional_ssh_command_is_classified_per_issue(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.5M")
        await device.refresh()
        eos_data = sa147_eos_data(version_output(), "")
        test = cast("Any", VerifySA147)(device=device, eos_data=eos_data)
        for command in test.instance_commands[2:]:
            command.output = None
            command.errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert [result.result for result in test.result.atomic_results] == [
            AntaTestStatus.INCONCLUSIVE,
            AntaTestStatus.INCONCLUSIVE,
            AntaTestStatus.ERROR,
            AntaTestStatus.ERROR,
        ]
        assert test.result.result is AntaTestStatus.ERROR
