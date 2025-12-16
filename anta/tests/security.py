# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various security tests."""

from __future__ import annotations

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from datetime import datetime, timezone
from typing import ClassVar

from anta.custom_types import PositiveInteger
from anta.input_models.security import ACL, APISSLCertificate, IPSecPeer, IPSecPeers
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tools import get_item, get_value


class VerifySSHStatus(AntaTest):
    """Verifies if the SSHD agent is disabled in the default VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the SSHD agent is disabled in the default VRF.
    * Failure: The test will fail if the SSHD agent is NOT disabled in the default VRF.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifySSHStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management ssh", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySSHStatus."""
        command_output = self.instance_commands[0].text_output

        try:
            line = next(line for line in command_output.split("\n") if line.startswith("SSHD status"))
        except StopIteration:
            self.result.is_failure("Could not find SSH status in returned output")
            return
        status = line.split()[-1]

        if status == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure(line)


class VerifySSHIPv4Acl(AntaTest):
    """Verifies if the SSHD agent has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the SSHD agent has the provided number of IPv4 ACL(s) in the specified VRF.
    * Failure: The test will fail if the SSHD agent has not the right number of IPv4 ACL(s) in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifySSHIPv4Acl:
          number: 3
          vrf: default
    ```
    """

    description = "Verifies if the SSHD agent has IPv4 ACL(s) configured."
    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management ssh ip access-list summary", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySSHIPv4Acl test."""

        number: PositiveInteger
        """The number of expected IPv4 ACL(s)."""
        vrf: str = "default"
        """The name of the VRF in which to check for the SSHD agent. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySSHIPv4Acl."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - SSH IPv4 ACL(s) count mismatch - Expected: {self.inputs.number} Actual: {ipv4_acl_number}")
            return

        not_configured_acl = [acl["name"] for acl in ipv4_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if not_configured_acl:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Following SSH IPv4 ACL(s) not configured or active: {', '.join(not_configured_acl)}")


class VerifySSHIPv6Acl(AntaTest):
    """Verifies if the SSHD agent has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the SSHD agent has the provided number of IPv6 ACL(s) in the specified VRF.
    * Failure: The test will fail if the SSHD agent has not the right number of IPv6 ACL(s) in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifySSHIPv6Acl:
          number: 3
          vrf: default
    ```
    """

    description = "Verifies if the SSHD agent has IPv6 ACL(s) configured."
    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management ssh ipv6 access-list summary", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySSHIPv6Acl test."""

        number: PositiveInteger
        """The number of expected IPv6 ACL(s)."""
        vrf: str = "default"
        """The name of the VRF in which to check for the SSHD agent. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySSHIPv6Acl."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - SSH IPv6 ACL(s) count mismatch - Expected: {self.inputs.number} Actual: {ipv6_acl_number}")
            return

        not_configured_acl = [acl["name"] for acl in ipv6_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if not_configured_acl:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Following SSH IPv6 ACL(s) not configured or active: {', '.join(not_configured_acl)}")


class VerifyTelnetStatus(AntaTest):
    """Verifies if Telnet is disabled in the default VRF.

    Expected Results
    ----------------
    * Success: The test will pass if Telnet is disabled in the default VRF.
    * Failure: The test will fail if Telnet is NOT disabled in the default VRF.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyTelnetStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management telnet", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTelnetStatus."""
        command_output = self.instance_commands[0].json_output
        if command_output["serverState"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("Telnet status for Default VRF is enabled")


class VerifyAPIHttpStatus(AntaTest):
    """Verifies if eAPI HTTP server is disabled globally.

    Expected Results
    ----------------
    * Success: The test will pass if eAPI HTTP server is disabled globally.
    * Failure: The test will fail if eAPI HTTP server is NOT disabled globally.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyAPIHttpStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management api http-commands", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAPIHttpStatus."""
        command_output = self.instance_commands[0].json_output
        if command_output["enabled"] and not command_output["httpServer"]["running"]:
            self.result.is_success()
        else:
            self.result.is_failure("eAPI HTTP server is enabled globally")


class VerifyAPIHttpsSSL(AntaTest):
    """Verifies if the eAPI has a valid SSL profile.

    Expected Results
    ----------------
    * Success: The test will pass if the eAPI HTTPS server SSL profile is configured and valid.
    * Failure: The test will fail if the eAPI HTTPS server SSL profile is NOT configured, misconfigured or invalid.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyAPIHttpsSSL:
          profile: default
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management api http-commands", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyAPIHttpsSSL test."""

        profile: str
        """SSL profile to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAPIHttpsSSL."""
        command_output = self.instance_commands[0].json_output
        try:
            if command_output["sslProfile"]["name"] == self.inputs.profile and command_output["sslProfile"]["state"] == "valid":
                self.result.is_success()
            else:
                self.result.is_failure(f"eAPI HTTPS server SSL profile {self.inputs.profile} is misconfigured or invalid")

        except KeyError:
            self.result.is_failure(f"eAPI HTTPS server SSL profile {self.inputs.profile} is not configured")


class VerifyAPIIPv4Acl(AntaTest):
    """Verifies if eAPI has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if eAPI has the provided number of IPv4 ACL(s) in the specified VRF.
    * Failure: The test will fail if eAPI has not the right number of IPv4 ACL(s) in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyAPIIPv4Acl:
          number: 3
          vrf: default
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management api http-commands ip access-list summary", revision=1)]

    class Input(AntaTest.Input):
        """Input parameters for the VerifyAPIIPv4Acl test."""

        number: PositiveInteger
        """The number of expected IPv4 ACL(s)."""
        vrf: str = "default"
        """The name of the VRF in which to check for eAPI. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAPIIPv4Acl."""
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - eAPI IPv4 ACL(s) count mismatch - Expected: {self.inputs.number} Actual: {ipv4_acl_number}")
            return

        not_configured_acl = [acl["name"] for acl in ipv4_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if not_configured_acl:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Following eAPI IPv4 ACL(s) not configured or active: {', '.join(not_configured_acl)}")
        else:
            self.result.is_success()


class VerifyAPIIPv6Acl(AntaTest):
    """Verifies if eAPI has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if eAPI has the provided number of IPv6 ACL(s) in the specified VRF.
    * Failure: The test will fail if eAPI has not the right number of IPv6 ACL(s) in the specified VRF.
    * Skipped: The test will be skipped if the number of IPv6 ACL(s) or VRF parameter is not provided.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyAPIIPv6Acl:
          number: 3
          vrf: default
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management api http-commands ipv6 access-list summary", revision=1)]

    class Input(AntaTest.Input):
        """Input parameters for the VerifyAPIIPv6Acl test."""

        number: PositiveInteger
        """The number of expected IPv6 ACL(s)."""
        vrf: str = "default"
        """The name of the VRF in which to check for eAPI. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAPIIPv6Acl."""
        command_output = self.instance_commands[0].json_output
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - eAPI IPv6 ACL(s) count mismatch - Expected: {self.inputs.number} Actual: {ipv6_acl_number}")
            return

        not_configured_acl = [acl["name"] for acl in ipv6_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if not_configured_acl:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Following eAPI IPv6 ACL(s) not configured or active: {', '.join(not_configured_acl)}")
        else:
            self.result.is_success()


class VerifyAPISSLCertificate(AntaTest):
    """Verifies the eAPI SSL certificate expiry, common subject name, encryption algorithm and key size.

    This test performs the following checks for each certificate:

      1. Validates that the certificate is not expired and meets the configured expiry threshold.
      2. Validates that the certificate Common Name matches the expected one.
      3. Ensures the certificate uses the specified encryption algorithm.
      4. Verifies the certificate key matches the expected key size.

    Expected Results
    ----------------
    * Success: If all of the following occur:
        - The certificate's expiry date exceeds the configured threshold.
        - The certificate's Common Name matches the input configuration.
        - The encryption algorithm used by the certificate is as expected.
        - The key size of the certificate matches the input configuration.
    * Failure: If any of the following occur:
        - The certificate is expired or set to expire within the defined threshold.
        - The certificate's common name does not match the expected input.
        - The encryption algorithm is incorrect.
        - The key size does not match the expected input.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyAPISSLCertificate:
          certificates:
            - certificate_name: ARISTA_SIGNING_CA.crt
              expiry_threshold: 30
              common_name: AristaIT-ICA ECDSA Issuing Cert Authority
              encryption_algorithm: ECDSA
              key_size: 256
            - certificate_name: ARISTA_ROOT_CA.crt
              expiry_threshold: 30
              common_name: Arista Networks Internal IT Root Cert Authority
              encryption_algorithm: RSA
              key_size: 4096
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show management security ssl certificate", revision=1),
        AntaCommand(command="show clock", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input parameters for the VerifyAPISSLCertificate test."""

        certificates: list[APISSLCertificate]
        """List of API SSL certificates."""
        APISSLCertificate: ClassVar[type[APISSLCertificate]] = APISSLCertificate

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAPISSLCertificate."""
        # Mark the result as success by default
        self.result.is_success()

        # Extract certificate and clock output
        certificate_output = self.instance_commands[0].json_output
        clock_output = self.instance_commands[1].json_output
        current_timestamp = clock_output["utcTime"]

        # Iterate over each API SSL certificate
        for certificate in self.inputs.certificates:
            # Collecting certificate expiry time and current EOS time.
            # These times are used to calculate the number of days until the certificate expires.
            if not (certificate_data := get_value(certificate_output, f"certificates..{certificate.certificate_name}", separator="..")):
                self.result.is_failure(f"{certificate} - Not found")
                continue

            expiry_time = certificate_data["notAfter"]
            day_difference = (datetime.fromtimestamp(expiry_time, tz=timezone.utc) - datetime.fromtimestamp(current_timestamp, tz=timezone.utc)).days

            # Verify certificate expiry
            if 0 < day_difference < certificate.expiry_threshold:
                self.result.is_failure(
                    f"{certificate} - set to expire within the threshold - Threshold: {certificate.expiry_threshold} days Actual: {day_difference} days"
                )
            elif day_difference < 0:
                self.result.is_failure(f"{certificate} - certificate expired")

            # Verify certificate common subject name, encryption algorithm and key size
            common_name = get_value(certificate_data, "subject.commonName", default="Not found")
            encryp_algo = get_value(certificate_data, "publicKey.encryptionAlgorithm", default="Not found")
            key_size = get_value(certificate_data, "publicKey.size", default="Not found")

            if common_name != certificate.common_name:
                self.result.is_failure(f"{certificate} - incorrect common name - Expected: {certificate.common_name} Actual: {common_name}")

            if encryp_algo != certificate.encryption_algorithm:
                self.result.is_failure(f"{certificate} - incorrect encryption algorithm - Expected: {certificate.encryption_algorithm} Actual: {encryp_algo}")

            if key_size != certificate.key_size:
                self.result.is_failure(f"{certificate} - incorrect public key - Expected: {certificate.key_size} Actual: {key_size}")


class VerifyBannerLogin(AntaTest):
    """Verifies the login banner of a device.

    PyYAML does not preserve leading spaces so the recommendation is to use the following syntax:
    `|2+` to indicate where the banner starts and to preserve any new line at the end.

    Expected Results
    ----------------
    * Success: The test will pass if the login banner matches the provided input.
    * Failure: The test will fail if the login banner does not match the provided input.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyBannerLogin:
          login_banner: |2+
            # Copyright (c) 2023-2024 Arista Networks, Inc.
            # Use of this source code is governed by the Apache License 2.0
            # that can be found in the LICENSE file.

    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show banner login", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBannerLogin test."""

        login_banner: str
        """Expected login banner of the device."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBannerLogin."""
        self.result.is_success()
        if not (login_banner := self.instance_commands[0].json_output["loginBanner"]):
            self.result.is_failure("Login banner is not configured")
            return

        if login_banner != self.inputs.login_banner:
            self.result.is_failure(f"Incorrect login banner configured - Expected: '{self.inputs.login_banner}' Actual: '{login_banner}'")


class VerifyBannerMotd(AntaTest):
    """Verifies the motd banner of a device.

    PyYAML does not preserve leading spaces so the recommendation is to use the following syntax:
    `|2+` to indicate where the banner starts and to preserve any new line at the end.


    Expected Results
    ----------------
    * Success: The test will pass if the motd banner matches the provided input.
    * Failure: The test will fail if the motd banner does not match the provided input.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyBannerMotd:
          motd_banner: |2+
            # Copyright (c) 2023-2024 Arista Networks, Inc.
            # Use of this source code is governed by the Apache License 2.0
            # that can be found in the LICENSE file.
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show banner motd", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBannerMotd test."""

        motd_banner: str
        """Expected motd banner of the device."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBannerMotd."""
        self.result.is_success()
        if not (motd_banner := self.instance_commands[0].json_output["motd"]):
            self.result.is_failure("MOTD banner is not configured")
            return

        if motd_banner != self.inputs.motd_banner:
            self.result.is_failure(f"Incorrect MOTD banner configured - Expected: '{self.inputs.motd_banner}' Actual: '{motd_banner}'")


class VerifyIPv4ACL(AntaTest):
    """Verifies the configuration of IPv4 ACLs.

    This test performs the following checks for each IPv4 ACL:

      1. Validates that the IPv4 ACL is properly configured.
      2. Validates that the sequence entries in the ACL are correctly ordered.

    Expected Results
    ----------------
    * Success: If all of the following occur:
        - Any IPv4 ACL entry is not configured.
        - The sequency entries are correctly configured.
    * Failure: If any of the following occur:
        - The IPv4 ACL is not configured.
        - The any IPv4 ACL entry is not configured.
        - The action for any entry does not match the expected input.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyIPv4ACL:
          ipv4_access_lists:
            - name: default-control-plane-acl
              entries:
                - sequence: 10
                  action: permit icmp any any
                - sequence: 20
                  action: permit ip any any tracked
                - sequence: 30
                  action: permit udp any any eq bfd ttl eq 255
            - name: LabTest
              entries:
                - sequence: 10
                  action: permit icmp any any
                - sequence: 20
                  action: permit tcp any any range 5900 5910
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip access-lists", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIPv4ACL test."""

        ipv4_access_lists: list[ACL]
        """List of IPv4 ACLs to verify."""
        IPv4ACL: ClassVar[type[ACL]] = ACL
        """To maintain backward compatibility."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIPv4ACL."""
        self.result.is_success()

        if not (command_output := self.instance_commands[0].json_output["aclList"]):
            self.result.is_failure("No Access Control List (ACL) configured")
            return

        for access_list in self.inputs.ipv4_access_lists:
            if not (access_list_output := get_item(command_output, "name", access_list.name)):
                self.result.is_failure(f"{access_list} - Not configured")
                continue

            for entry in access_list.entries:
                if not (actual_entry := get_item(access_list_output["sequence"], "sequenceNumber", entry.sequence)):
                    self.result.is_failure(f"{access_list} {entry} - Not configured")
                    continue

                if (act_action := actual_entry["text"]) != entry.action:
                    self.result.is_failure(f"{access_list} {entry} - action mismatch - Expected: {entry.action} Actual: {act_action}")


class VerifyIPSecConnHealth(AntaTest):
    """Verifies all IPv4 security connections.

    Expected Results
    ----------------
    * Success: The test will pass if all the IPv4 security connections are established in all vrf.
    * Failure: The test will fail if IPv4 security is not configured or any of IPv4 security connections are not established in any vrf.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyIPSecConnHealth:
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip security connection vrf all")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIPSecConnHealth."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output["connections"]

        # Check if IP security connection is configured
        if not command_output:
            self.result.is_failure("No IPv4 security connection configured")
            return

        # Iterate over all ipsec connections
        for conn_data in command_output.values():
            state = next(iter(conn_data["pathDict"].values()))
            if state != "Established":
                source = conn_data.get("saddr")
                destination = conn_data.get("daddr")
                vrf = conn_data.get("tunnelNs")
                self.result.is_failure(f"Source: {source} Destination: {destination} VRF: {vrf} - IPv4 security connection not established")


class VerifySpecificIPSecConn(AntaTest):
    """Verifies the IPv4 security connections.

    This test performs the following checks for each peer:

      1. Validates that the VRF is configured.
      2. Checks for the presence of IPv4 security connections for the specified peer.
      3. For each relevant peer:
        - If source and destination addresses are provided, verifies the security connection for the specific path exists and is `Established`.
        - If no addresses are provided, verifies that all security connections associated with the peer are `Established`.

    Expected Results
    ----------------
    * Success: If all checks pass for all specified IPv4 security connections.
    * Failure: If any of the following occur:
        - No IPv4 security connections are found for the peer
        - The security connection is not established for the specified path or any of the peer connections is not established when no path is specified.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifySpecificIPSecConn:
          ip_security_connections:
            - peer: 10.255.0.1
            - peer: 10.255.0.2
              vrf: default
              connections:
                - source_address: 100.64.3.2
                  destination_address: 100.64.2.2
                - source_address: 172.18.3.2
                  destination_address: 172.18.2.2
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show ip security connection vrf {vrf} path peer {peer}", revision=2)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifySpecificIPSecConn test."""

        ip_security_connections: list[IPSecPeer]
        """List of IP4v security peers."""
        IPSecPeers: ClassVar[type[IPSecPeers]] = IPSecPeers
        """To maintain backward compatibility."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each input IP Sec connection."""
        return [template.render(peer=conn.peer, vrf=conn.vrf) for conn in self.inputs.ip_security_connections]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySpecificIPSecConn."""
        self.result.is_success()

        for command_output, input_peer in zip(self.instance_commands, self.inputs.ip_security_connections, strict=False):
            conn_output = command_output.json_output["connections"]
            conn_input = input_peer.connections
            vrf = input_peer.vrf

            # Check if IPv4 security connection is configured
            if not conn_output:
                # Atomic result
                self.result.add(description=str(input_peer), status=AntaTestStatus.FAILURE, messages=["Not configured"])
                continue

            # If connection details are not provided then check all connections of a peer
            if conn_input is None:
                for conn_data in conn_output.values():
                    state = next(iter(conn_data["pathDict"].values()))
                    # Atomic result
                    source = conn_data.get("saddr")
                    destination = conn_data.get("daddr")
                    result = self.result.add(description=f"{input_peer} Source: {source} Destination: {destination}", status=AntaTestStatus.SUCCESS)
                    if state != "Established":
                        result.is_failure(f"Connection down - Expected: Established Actual: {state}")
                continue

            # Create a dictionary of existing connections for faster lookup
            existing_connections = {
                (conn_data.get("saddr"), conn_data.get("daddr"), conn_data.get("tunnelNs")): next(iter(conn_data["pathDict"].values()))
                for conn_data in conn_output.values()
            }
            for connection in conn_input:
                source_input = str(connection.source_address)
                destination_input = str(connection.destination_address)
                # Atomic result
                result = self.result.add(description=f"{input_peer} {connection}", status=AntaTestStatus.SUCCESS)
                if (source_input, destination_input, vrf) in existing_connections:
                    existing_state = existing_connections[(source_input, destination_input, vrf)]
                    if existing_state != "Established":
                        failure = f"Expected: Established Actual: {existing_state}"
                        result.is_failure(f"Connection down - {failure}")
                else:
                    result.is_failure("Connection not found")


class VerifyHardwareEntropy(AntaTest):
    """Verifies hardware entropy generation is enabled on device.

    Expected Results
    ----------------
    * Success: The test will pass if hardware entropy generation is enabled.
    * Failure: The test will fail if hardware entropy generation is not enabled.

    Examples
    --------
    ```yaml
    anta.tests.security:
      - VerifyHardwareEntropy:
    ```
    """

    categories: ClassVar[list[str]] = ["security"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management security")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyHardwareEntropy."""
        command_output = self.instance_commands[0].json_output

        # Check if hardware entropy generation is enabled.
        if not command_output.get("hardwareEntropyEnabled"):
            self.result.is_failure("Hardware entropy generation is disabled")
        else:
            self.result.is_success()
