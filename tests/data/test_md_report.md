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
| 30 | 7 | 2 | 19 | 2 |

### Summary Totals Device Under Test

| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |
| ------------------| ----------- | ------------- | ------------- | ------------- | ----------- | -------------------| ------------------|
| DC1-LEAF1A | 15 | 5 | 0 | 9 | 1 | - | AAA, BFD, BGP, Connectivity, SNMP, STP, Services, Software, System |
| DC1-SPINE1 | 15 | 2 | 2 | 10 | 1 | MLAG, VXLAN | AAA, BFD, BGP, Connectivity, Routing, SNMP, STP, Services, Software, System |

### Summary Totals Per Category

| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |
| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |
| AAA | 2 | 0 | 0 | 2 | 0 |
| BFD | 2 | 0 | 0 | 2 | 0 |
| BGP | 2 | 0 | 0 | 2 | 0 |
| Connectivity | 4 | 0 | 0 | 2 | 2 |
| Interfaces | 2 | 2 | 0 | 0 | 0 |
| MLAG | 2 | 1 | 1 | 0 | 0 |
| Routing | 2 | 1 | 0 | 1 | 0 |
| SNMP | 2 | 0 | 0 | 2 | 0 |
| STP | 2 | 0 | 0 | 2 | 0 |
| Security | 2 | 2 | 0 | 0 | 0 |
| Services | 2 | 0 | 0 | 2 | 0 |
| Software | 2 | 0 | 0 | 2 | 0 |
| System | 2 | 0 | 0 | 2 | 0 |
| VXLAN | 2 | 1 | 1 | 0 | 0 |

## Test Results

| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |
| DC1-LEAF1A | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-LEAF1A | BFD | VerifyBFDSpecificPeers | Verifies the IPv4 BFD peer's sessions and remote disc in the specified VRF. | - | failure | Following BFD peers are not configured, status is not up or remote disc is zero: {'192.0.255.8': {'default': 'Not Configured'}, '192.0.255.7': {'default': 'Not Configured'}} |
| DC1-LEAF1A | BGP | VerifyBGPPeerCount | Verifies the count of BGP peers. | - | failure | Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'PROD': 'Expected: 2, Actual: 1'}}, {'afi': 'ipv4', 'safi': 'multicast', 'vrfs': {'DEV': 'Expected: 3, Actual: 0'}}] |
| DC1-LEAF1A | Connectivity | VerifyLLDPNeighbors | Verifies that the provided LLDP neighbors are connected properly. | - | failure | Wrong LLDP neighbor(s) on port(s):    Ethernet1       DC1-SPINE1_Ethernet1    Ethernet2       DC1-SPINE2_Ethernet1 Port(s) not configured:    Ethernet7 |
| DC1-LEAF1A | Connectivity | VerifyReachability | Test the network reachability to one or many destination IP(s). | - | error | ping vrf MGMT 1.1.1.1 source Management1 repeat 2 has failed: No source interface Management1 |
| DC1-LEAF1A | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | - | success | - |
| DC1-LEAF1A | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | - | success | - |
| DC1-LEAF1A | Routing | VerifyRoutingTableEntry | Verifies that the provided routes are present in the routing table of a specified VRF. | - | success | - |
| DC1-LEAF1A | SNMP | VerifySnmpStatus | Verifies if the SNMP agent is enabled. | - | failure | SNMP agent disabled in vrf default |
| DC1-LEAF1A | STP | VerifySTPMode | Verifies the configured STP mode for a provided list of VLAN(s). | - | failure | Wrong STP mode configured for the following VLAN(s): [10, 20] |
| DC1-LEAF1A | Security | VerifyTelnetStatus | Verifies if Telnet is disabled in the default VRF. | - | success | - |
| DC1-LEAF1A | Services | VerifyHostname | Verifies the hostname of a device. | - | failure | Expected 's1-spine1' as the hostname, but found 'DC1-LEAF1A' instead. |
| DC1-LEAF1A | Software | VerifyEOSVersion | Verifies the EOS version of the device. | - | failure | device is running version "4.31.1F-34554157.4311F (engineering build)" not in expected versions: ['4.25.4M', '4.26.1F'] |
| DC1-LEAF1A | System | VerifyNTP | Verifies if NTP is synchronised. | - | failure | The device is not synchronized with the configured NTP server(s): 'NTP is disabled.' |
| DC1-LEAF1A | VXLAN | VerifyVxlan1Interface | Verifies the Vxlan1 interface status. | - | success | - |
| DC1-SPINE1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-SPINE1 | BFD | VerifyBFDSpecificPeers | Verifies the IPv4 BFD peer's sessions and remote disc in the specified VRF. | - | failure | Following BFD peers are not configured, status is not up or remote disc is zero: {'192.0.255.8': {'default': 'Not Configured'}, '192.0.255.7': {'default': 'Not Configured'}} |
| DC1-SPINE1 | BGP | VerifyBGPPeerCount | Verifies the count of BGP peers. | - | failure | Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'PROD': 'Not Configured', 'default': 'Expected: 3, Actual: 4'}}, {'afi': 'ipv4', 'safi': 'multicast', 'vrfs': {'DEV': 'Not Configured'}}, {'afi': 'evpn', 'vrfs': {'default': 'Expected: 2, Actual: 4'}}] |
| DC1-SPINE1 | Connectivity | VerifyLLDPNeighbors | Verifies that the provided LLDP neighbors are connected properly. | - | failure | Wrong LLDP neighbor(s) on port(s):    Ethernet1       DC1-LEAF1A_Ethernet1    Ethernet2       DC1-LEAF1B_Ethernet1 Port(s) not configured:    Ethernet7 |
| DC1-SPINE1 | Connectivity | VerifyReachability | Test the network reachability to one or many destination IP(s). | - | error | ping vrf MGMT 1.1.1.1 source Management1 repeat 2 has failed: No source interface Management1 |
| DC1-SPINE1 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | - | success | - |
| DC1-SPINE1 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | - | skipped | MLAG is disabled |
| DC1-SPINE1 | Routing | VerifyRoutingTableEntry | Verifies that the provided routes are present in the routing table of a specified VRF. | - | failure | The following route(s) are missing from the routing table of VRF default: ['10.1.0.2'] |
| DC1-SPINE1 | SNMP | VerifySnmpStatus | Verifies if the SNMP agent is enabled. | - | failure | SNMP agent disabled in vrf default |
| DC1-SPINE1 | STP | VerifySTPMode | Verifies the configured STP mode for a provided list of VLAN(s). | - | failure | STP mode 'rapidPvst' not configured for the following VLAN(s): [10, 20] |
| DC1-SPINE1 | Security | VerifyTelnetStatus | Verifies if Telnet is disabled in the default VRF. | - | success | - |
| DC1-SPINE1 | Services | VerifyHostname | Verifies the hostname of a device. | - | failure | Expected 's1-spine1' as the hostname, but found 'DC1-SPINE1' instead. |
| DC1-SPINE1 | Software | VerifyEOSVersion | Verifies the EOS version of the device. | - | failure | device is running version "4.31.1F-34554157.4311F (engineering build)" not in expected versions: ['4.25.4M', '4.26.1F'] |
| DC1-SPINE1 | System | VerifyNTP | Verifies if NTP is synchronised. | - | failure | The device is not synchronized with the configured NTP server(s): 'NTP is disabled.' |
| DC1-SPINE1 | VXLAN | VerifyVxlan1Interface | Verifies the Vxlan1 interface status. | - | skipped | Vxlan1 interface is not configured |
