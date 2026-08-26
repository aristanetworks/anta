# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 0117."""

from __future__ import annotations

from typing import Any, ClassVar

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tests.advisories._version import VersionRule, require_affected_version

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


def _evaluate_gnmi_accounting_enabled(gnmi_output: dict[str, Any]) -> bool | None:
    """Return whether an enabled gNMI transport has accounting enabled."""
    transports = gnmi_output.get("transports")
    if not isinstance(transports, dict):
        return None

    unknown = False
    for transport in transports.values():
        if not isinstance(transport, dict):
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


def _evaluate_risky_trace_configuration(running_config_output: dict[str, Any]) -> bool | None:
    """Return whether the structured configuration contains a risky trace selector."""
    commands = running_config_output.get("cmds")
    if not isinstance(commands, dict):
        return None

    for command in commands:
        if not isinstance(command, str):
            return None
        if command.startswith("trace OpenConfig setting ") and any(selector in command for selector in RISKY_TRACE_SELECTORS):
            return True
    return False


ADVISORY = {
    "title": "Security Advisory 0117",
    "cves": ("CVE-2025-0936",),
    "url": "https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117",
    "description": (
        "On affected platforms running Arista EOS with a gNMI transport enabled, running the gNOI "
        "File TransferToRemote RPC with credentials for a remote server may cause these remote-server "
        "credentials to be logged or accounted on the local EOS device or possibly on other remote "
        "accounting servers (i.e. TACACS, RADIUS, etc)."
    ),
}


class VerifySA117(AntaTest):
    """Verify that the device is not exposed to Arista Security Advisory 0117 (CVE-2025-0936).

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version or device configuration is not affected by the advisory.
    * Failure: The test will fail if an affected EOS version has gNMI accounting enabled or a risky OpenConfig trace selector configured.
    * Error: The test will error if the EOS version or relevant configuration cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_117:
      - VerifySA117:
    ```
    """

    categories: ClassVar[list[str]] = ["Security Advisory"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show management api gnmi", revision=1),
        AntaCommand(command="show running-config sanitized", revision=1),
        AntaCommand(command="show version", revision=1),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Fail when the exposure signals and every applicable affected condition are present."""
        gnmi_output = self.instance_commands[0].json_output
        running_config_output = self.instance_commands[1].json_output
        version_output = self.instance_commands[2].json_output
        messages: list[str] = []

        if not require_affected_version(self.result, messages, version_output, AFFECTED_VERSION_MATRIX):
            return

        accounting_enabled = _evaluate_gnmi_accounting_enabled(gnmi_output)
        risky_trace_configured = _evaluate_risky_trace_configuration(running_config_output)
        if accounting_enabled is True:
            messages.append("OpenConfig gNMI has accounting requests enabled.")
        elif risky_trace_configured is True:
            messages.append("OpenConfig tracing includes one of the risky selectors from the advisory.")
        elif accounting_enabled is None or risky_trace_configured is None:
            messages.append("The gNMI accounting or OpenConfig trace configuration could not be determined from the available EOS command output.")
            self.result.is_error("\n".join(messages))
            return
        else:
            messages.append("The device configuration is not affected by this advisory.")
            self.result.is_success("\n".join(messages))
            return

        self.result.is_failure("\n".join(messages))
