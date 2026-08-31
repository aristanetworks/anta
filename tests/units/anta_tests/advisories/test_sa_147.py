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

from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryStatus
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_147 import (
    ADVISORY,
    VerifySA147,
    _assess_client_issue,
    _assess_server_issue,
    _evaluate_eos_applicability,
    _extract_package_version,
    _is_openssh_before_10_4,
    _ssh_accepts_connections,
    _strict_host_key_checking_enabled,
)
from tests.units.anta_tests import test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
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
    "The assessment is inconclusive and the device may be affected because openssh-clients "
    "'9.9p1' is affected, but operator-initiated SFTP use with an untrusted server cannot be "
    "determined"
)
INCONCLUSIVE_SCP = (
    "The assessment is inconclusive and the device may be affected because openssh-clients "
    "'9.9p1' is affected, but operator-initiated SCP remote-to-remote use with an untrusted "
    "server cannot be determined"
)
INCONCLUSIVE_SSH = (
    "The assessment is inconclusive and the device may be affected because openssh-clients "
    "'9.9p1' is affected, but operator-initiated SSH use with a malicious or compromised server "
    "cannot be determined"
)
SERVER_AFFECTED = "The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections"
CLIENT_PACKAGE_ERROR = "The openssh-clients package version could not be determined from 'show version detail'"
SSH_STATE_ERROR = "Whether SSH accepts connections could not be determined from the management SSH configuration"
STRICT_CHECKING_ERROR = "The strict host-key checking state could not be determined from the management SSH configuration"
EOS_NOT_AFFECTED = "The device is not affected because its EOS version is outside the published affected range"
EOS_VERSION_ERROR = "The EOS version applicability is unavailable from the refreshed device metadata"

_DATA: AntaUnitTestData = {
    (VerifySA147, "failure-vulnerable-packages"): {
        "version": "4.35.5M",
        "eos_data": [version_output(), ""],
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
        "version": "4.35.5M",
        "eos_data": [version_output(client="10.4p1", server="10.4p1"), ""],
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
        "version": "4.35.5M",
        "eos_data": [version_output(), "management ssh\n   shutdown"],
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (
                    "The device is not affected because SSH management access is disabled entirely",
                    AntaTestStatus.SUCCESS,
                    "",
                ),
                (INCONCLUSIVE_SSH, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
            ),
        ),
    },
    (VerifySA147, "failure-strict-host-key-checking-mitigates-one-cve"): {
        "version": "4.35.5M",
        "eos_data": [
            version_output(),
            "management ssh\n   hostkey client strict-checking",
        ],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (SERVER_AFFECTED, AntaTestStatus.FAILURE, "Upgrade to"),
                (
                    "The device is affected but mitigated because openssh-clients '9.9p1' uses strict host-key checking",
                    AntaTestStatus.INCONCLUSIVE,
                    "Upgrade to",
                ),
            ),
        ),
    },
    (VerifySA147, "success-eos-outside-published-affected-range"): {
        "version": "4.35.6M",
        "eos_data": [version_output(eos="4.35.6M"), ""],
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
        "eos_data": [version_output(), ""],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, "Collect or correct valid refreshed device EOS version metadata"),
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, "Collect or correct valid refreshed device EOS version metadata"),
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, "Collect or correct valid refreshed device EOS version metadata"),
                (EOS_VERSION_ERROR, AntaTestStatus.ERROR, "Collect or correct valid refreshed device EOS version metadata"),
            ),
        ),
    },
    (VerifySA147, "error-missing-client-package-has-parent-precedence"): {
        "version": "4.35.5M",
        "eos_data": [version_output(client=None, server="9.9p1"), ""],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (
                    CLIENT_PACKAGE_ERROR,
                    AntaTestStatus.ERROR,
                    "Collect or correct valid openssh-clients package evidence",
                ),
                (
                    CLIENT_PACKAGE_ERROR,
                    AntaTestStatus.ERROR,
                    "Collect or correct valid openssh-clients package evidence",
                ),
                (SERVER_AFFECTED, AntaTestStatus.FAILURE, "Upgrade to"),
                (
                    CLIENT_PACKAGE_ERROR,
                    AntaTestStatus.ERROR,
                    "Collect or correct valid openssh-clients package evidence",
                ),
            ),
        ),
    },
    (VerifySA147, "success-fixed-eos-ignores-unneeded-evidence"): {
        "version": "4.35.6M",
        "eos_data": [
            version_output(eos="4.35.6M", client=None, server=None),
            "management ssh\n   shutdown",
        ],
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
        "version": "4.35.5M",
        "eos_data": [version_output(), "unexpected output"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (INCONCLUSIVE_SFTP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (INCONCLUSIVE_SCP, AntaTestStatus.INCONCLUSIVE, "unresolved condition"),
                (
                    SSH_STATE_ERROR,
                    AntaTestStatus.ERROR,
                    "Collect or correct valid management SSH configuration evidence",
                ),
                (
                    STRICT_CHECKING_ERROR,
                    AntaTestStatus.ERROR,
                    "Collect or correct valid management SSH configuration evidence",
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
        output = version_output()
        assert _extract_package_version(output, "openssh-clients") == "9.9p1"
        assert _extract_package_version({}, "openssh-clients") is None
        assert _extract_package_version(version_output(client=99), "openssh-clients") is None

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
                assert _ssh_accepts_connections(config) is expected

    def test_strict_host_key_checking(self) -> None:
        assert _strict_host_key_checking_enabled("management ssh\n   hostkey client strict-checking")
        assert not _strict_host_key_checking_enabled("management ssh")
        assert not _strict_host_key_checking_enabled("management ssh\n   no hostkey client strict-checking")
        assert _strict_host_key_checking_enabled("unexpected output") is None
        assert _strict_host_key_checking_enabled("management ssh\n   hostkey client strict-checking\n   no hostkey client strict-checking") is None

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
                assert _evaluate_eos_applicability(parsed_version) is expected
        assert _evaluate_eos_applicability(None) is None


class TestSA147Assessment(unittest.TestCase):
    """Validate each vulnerability's semantic classification before projection."""

    def test_operator_dependent_client_issue_is_inconclusive(self) -> None:
        status, message, remediation = _assess_client_issue(
            package_version="9.9p1",
            action="operator behavior",
        )

        assert status is AdvisoryStatus.INCONCLUSIVE
        assert "inconclusive" in message
        assert "may be affected" in message
        assert "unresolved condition" in remediation

    def test_client_issue_fixed_mitigated_and_error_states(self) -> None:
        fixed, _, _ = _assess_client_issue(
            package_version="10.4p1",
            action="operator behavior",
        )
        eos_fixed, _, _ = _assess_client_issue(
            package_version=None,
            action="operator behavior",
            eos_affected=False,
        )
        mitigated, mitigated_message, mitigated_remediation = _assess_client_issue(
            package_version="9.9p1",
            action="operator behavior",
            mitigated=True,
        )
        missing_mitigation, _, _ = _assess_client_issue(
            package_version="9.9p1",
            action="operator behavior",
            mitigation_evidence_unavailable=True,
        )
        missing_package, _, _ = _assess_client_issue(
            package_version=None,
            action="operator behavior",
        )

        assert fixed is AdvisoryStatus.NOT_AFFECTED
        assert eos_fixed is AdvisoryStatus.NOT_AFFECTED
        assert mitigated is AdvisoryStatus.MITIGATED
        assert "mitigated" in mitigated_message
        assert "Upgrade to" in mitigated_remediation
        assert "strict host-key checking" not in mitigated_remediation
        assert "http" not in mitigated_remediation
        assert missing_mitigation is AdvisoryStatus.ERROR
        assert missing_package is AdvisoryStatus.ERROR

    def test_server_issue_states_and_safe_short_circuits(self) -> None:
        disabled, _, _ = _assess_server_issue(None, "management ssh\n   shutdown", ssh_command_unsupported=False)
        fixed, _, _ = _assess_server_issue("10.4p1", "", ssh_command_unsupported=True)
        affected, affected_message, _ = _assess_server_issue("9.9p1", "", ssh_command_unsupported=False)
        missing_config, _, _ = _assess_server_issue("9.9p1", "", ssh_command_unsupported=True)
        malformed, _, _ = _assess_server_issue("9.9p1", "unexpected output", ssh_command_unsupported=False)

        assert disabled is AdvisoryStatus.NOT_AFFECTED
        assert fixed is AdvisoryStatus.NOT_AFFECTED
        assert affected is AdvisoryStatus.AFFECTED
        assert "affected" in affected_message
        assert missing_config is AdvisoryStatus.ERROR
        assert malformed is AdvisoryStatus.ERROR


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
        eos_data = [detail_output, ssh_config]
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
        eos_data = [version_output(), ""]
        test = cast("Any", VerifySA147)(device=device, eos_data=eos_data)
        test.instance_commands[1].output = None
        test.instance_commands[1].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert [result.result for result in test.result.atomic_results] == [
            AntaTestStatus.INCONCLUSIVE,
            AntaTestStatus.INCONCLUSIVE,
            AntaTestStatus.ERROR,
            AntaTestStatus.ERROR,
        ]
        assert test.result.result is AntaTestStatus.ERROR
