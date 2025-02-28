# ANTA Report

**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Test Results Summary](#test-results-summary)
    - [Summary Totals](#summary-totals)
    - [Summary Totals Device Under Test](#summary-totals-device-under-test)
    - [Summary Totals Per Category](#summary-totals-per-category)
  - [Test Results](#test-results)

## Test Results Summary

### Summary Totals

| Total Tests | Total Tests Success | Total Tests Skipped | Total Tests Failure | Total Tests Error |
| ----------- | ------------------- | ------------------- | ------------------- | ------------------|
| 30 | 4 | 9 | 15 | 2 |

### Summary Totals Device Under Test

| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |
| ------------------| ----------- | ------------- | ------------- | ------------- | ----------- | -------------------| ------------------|
| s1-spine1 | 30 | 4 | 9 | 15 | 2 | AVT, Field Notices, Hardware, ISIS, LANZ, OSPF, PTP, Path-Selection, Profiles | AAA, BFD, BGP, Connectivity, Cvx, Interfaces, Logging, MLAG, SNMP, STUN, Security, Services, Software, System, VLAN |

### Summary Totals Per Category

| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |
| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |
| AAA | 1 | 0 | 0 | 1 | 0 |
| AVT | 1 | 0 | 1 | 0 | 0 |
| BFD | 1 | 0 | 0 | 1 | 0 |
| BGP | 1 | 0 | 0 | 0 | 1 |
| Configuration | 1 | 1 | 0 | 0 | 0 |
| Connectivity | 1 | 0 | 0 | 1 | 0 |
| Cvx | 1 | 0 | 0 | 0 | 1 |
| Field Notices | 1 | 0 | 1 | 0 | 0 |
| Hardware | 1 | 0 | 1 | 0 | 0 |
| Interfaces | 1 | 0 | 0 | 1 | 0 |
| ISIS | 1 | 0 | 1 | 0 | 0 |
| LANZ | 1 | 0 | 1 | 0 | 0 |
| Logging | 1 | 0 | 0 | 1 | 0 |
| MLAG | 1 | 0 | 0 | 1 | 0 |
| OSPF | 1 | 0 | 1 | 0 | 0 |
| Path-Selection | 1 | 0 | 1 | 0 | 0 |
| Profiles | 1 | 0 | 1 | 0 | 0 |
| PTP | 1 | 0 | 1 | 0 | 0 |
| Routing | 1 | 1 | 0 | 0 | 0 |
| Security | 2 | 0 | 0 | 2 | 0 |
| Services | 1 | 0 | 0 | 1 | 0 |
| SNMP | 1 | 0 | 0 | 1 | 0 |
| Software | 1 | 0 | 0 | 1 | 0 |
| STP | 1 | 1 | 0 | 0 | 0 |
| STUN | 2 | 0 | 0 | 2 | 0 |
| System | 1 | 0 | 0 | 1 | 0 |
| VLAN | 1 | 0 | 0 | 1 | 0 |
| VXLAN | 1 | 1 | 0 | 0 | 0 |

## Test Results

| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |
| s1-spine1 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for commands, exec, system, dot1x |
| s1-spine1 | AVT | VerifyAVTPathHealth | Verifies the status of all AVT paths for all VRFs. | - | skipped | VerifyAVTPathHealth test is not supported on cEOSLab. |
| s1-spine1 | BFD | VerifyBFDPeersHealth | Verifies the health of IPv4 BFD peers across all VRFs. | - | failure | No IPv4 BFD peers are configured for any VRF. |
| s1-spine1 | BGP | VerifyBGPAdvCommunities | Verifies that advertised communities are standard, extended and large for BGP IPv4 peer(s). | - | error | show bgp neighbors vrf all has failed: The command is only supported in the multi-agent routing protocol model., The command is only supported in the multi-agent routing protocol model., The command is only supported in the multi-agent routing protocol model., The command is only supported in the multi-agent routing protocol model. |
| s1-spine1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | - | success | - |
| s1-spine1 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | - | failure | Port: Ethernet1 Neighbor: DC1-SPINE1 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: spine1-dc1.fun.aristanetworks.com/Ethernet3<br>Port: Ethernet2 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: spine2-dc1.fun.aristanetworks.com/Ethernet3 |
| s1-spine1 | Cvx | VerifyActiveCVXConnections | Verifies the number of active CVX Connections. | - | error | show cvx connections brief has failed: Unavailable command (controller not ready) (at token 2: 'connections') |
| s1-spine1 | Field Notices | VerifyFieldNotice44Resolution | Verifies that the device is using the correct Aboot version per FN0044. | - | skipped | VerifyFieldNotice44Resolution test is not supported on cEOSLab. |
| s1-spine1 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | - | skipped | VerifyTemperature test is not supported on cEOSLab. |
| s1-spine1 | Interfaces | VerifyIPProxyARP | Verifies if Proxy ARP is enabled. | - | failure | Interface: Ethernet1 - Proxy-ARP disabled<br>Interface: Ethernet2 - Proxy-ARP disabled |
| s1-spine1 | ISIS | VerifyISISNeighborState | Verifies the health of IS-IS neighbors. | - | skipped | IS-IS not configured |
| s1-spine1 | LANZ | VerifyLANZ | Verifies if LANZ is enabled. | - | skipped | VerifyLANZ test is not supported on cEOSLab. |
| s1-spine1 | Logging | VerifyLoggingHosts | Verifies logging hosts (syslog servers) for a specified VRF. | - | failure | Syslog servers 1.1.1.1, 2.2.2.2 are not configured in VRF default |
| s1-spine1 | MLAG | VerifyMlagDualPrimary | Verifies the MLAG dual-primary detection parameters. | - | failure | Dual-primary detection is disabled |
| s1-spine1 | OSPF | VerifyOSPFMaxLSA | Verifies all OSPF instances did not cross the maximum LSA threshold. | - | skipped | No OSPF instance found. |
| s1-spine1 | Path-Selection | VerifyPathsHealth | Verifies the path and telemetry state of all paths under router path-selection. | - | skipped | VerifyPathsHealth test is not supported on cEOSLab. |
| s1-spine1 | Profiles | VerifyTcamProfile | Verifies the device TCAM profile. | - | skipped | VerifyTcamProfile test is not supported on cEOSLab. |
| s1-spine1 | PTP | VerifyPtpGMStatus | Verifies that the device is locked to a valid PTP Grandmaster. | - | skipped | VerifyPtpGMStatus test is not supported on cEOSLab. |
| s1-spine1 | Routing | VerifyIPv4RouteNextHops | Verifies the next-hops of the IPv4 prefixes. | - | success | - |
| s1-spine1 | Security | VerifyBannerLogin | Verifies the login banner of a device. | - | failure | Expected '# Copyright (c) 2023-2024 Arista Networks, Inc.<br># Use of this source code is governed by the Apache License 2.0<br># that can be found in the LICENSE file.<br>' as the login banner, but found '' instead. |
| s1-spine1 | Security | VerifyBannerMotd | Verifies the motd banner of a device. | - | failure | Expected '# Copyright (c) 2023-2024 Arista Networks, Inc.<br># Use of this source code is governed by the Apache License 2.0<br># that can be found in the LICENSE file.<br>' as the motd banner, but found '' instead. |
| s1-spine1 | Services | VerifyHostname | Verifies the hostname of a device. | - | failure | Incorrect Hostname - Expected: s1-spine1 Actual: leaf1-dc1 |
| s1-spine1 | SNMP | VerifySnmpContact | Verifies the SNMP contact of a device. | - | failure | SNMP contact is not configured. |
| s1-spine1 | Software | VerifyEOSVersion | Verifies the EOS version of the device. | - | failure | EOS version mismatch - Actual: 4.31.0F-33804048.4310F (engineering build) not in Expected: 4.25.4M, 4.26.1F |
| s1-spine1 | STP | VerifySTPBlockedPorts | Verifies there is no STP blocked ports. | - | success | - |
| s1-spine1 | STUN | VerifyStunClient | (Deprecated) Verifies the translation for a source address on a STUN client. | - | failure | Client 172.18.3.2 Port: 4500 - STUN client translation not found. |
| s1-spine1 | STUN | VerifyStunClientTranslation | Verifies the translation for a source address on a STUN client. | - | failure | Client 172.18.3.2 Port: 4500 - STUN client translation not found.<br>Client 100.64.3.2 Port: 4500 - STUN client translation not found. |
| s1-spine1 | System | VerifyNTPAssociations | Verifies the Network Time Protocol (NTP) associations. | - | failure | NTP Server: 1.1.1.1 Preferred: True Stratum: 1 - Not configured<br>NTP Server: 2.2.2.2 Preferred: False Stratum: 2 - Not configured<br>NTP Server: 3.3.3.3 Preferred: False Stratum: 2 - Not configured |
| s1-spine1 | VLAN | VerifyDynamicVlanSource | Verifies dynamic VLAN allocation for specified VLAN sources. | - | failure | Dynamic VLAN source(s) exist but have no VLANs allocated: mlagsync |
| s1-spine1 | VXLAN | VerifyVxlan1ConnSettings | Verifies the interface vxlan1 source interface and UDP port. | - | success | - |
