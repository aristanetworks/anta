# ANTA Report

**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Test Results Summary](#test-results-summary)
    - [Summary Totals](#summary-totals)
    - [Summary Totals Device Under Test](#summary-totals-device-under-test)
    - [Summary Totals Per Category](#summary-totals-per-category)
  - [Failed Test Results Summary](#failed-test-results-summary)

## Test Results Summary

### Summary Totals

| Total Tests | Total Tests Success | Total Tests Skipped | Total Tests Failure | Total Tests Error |
| ----------- | ------------------- | ------------------- | ------------------- | ------------------|
| 89 | 31 | 8 | 48 | 2 |

### Summary Totals Device Under Test

| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |
| ------------------| ----------- | ------------- | ------------- | ------------- | ----------- | -------------------| ------------------|
| DC1-SPINE1 | 44 | 13 | 6 | 24 | 1 | MLAG, OSPF, VXLAN | AAA, BFD, BGP, Connectivity, Interfaces, Multicast, Routing, SNMP, STP, Software, System, VLAN |
| DC1-LEAF1A | 45 | 18 | 2 | 24 | 1 | OSPF | AAA, BFD, BGP, Connectivity, Interfaces, Multicast, Routing, SNMP, STP, Software, System, VLAN |

### Summary Totals Per Category

| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |
| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |
| AAA | 2 | 0 | 0 | 2 | 0 |
| BFD | 6 | 2 | 0 | 4 | 0 |
| BGP | 22 | 0 | 0 | 22 | 0 |
| Connectivity | 3 | 0 | 0 | 1 | 2 |
| Interfaces | 10 | 6 | 0 | 4 | 0 |
| MLAG | 4 | 2 | 2 | 0 | 0 |
| Multicast | 4 | 2 | 0 | 2 | 0 |
| OSPF | 4 | 0 | 4 | 0 | 0 |
| Routing | 6 | 3 | 0 | 3 | 0 |
| SNMP | 2 | 0 | 0 | 2 | 0 |
| STP | 2 | 0 | 0 | 2 | 0 |
| Security | 4 | 4 | 0 | 0 | 0 |
| Software | 2 | 0 | 0 | 2 | 0 |
| System | 12 | 10 | 0 | 2 | 0 |
| VLAN | 2 | 0 | 0 | 2 | 0 |
| VXLAN | 4 | 2 | 2 | 0 | 0 |

## Failed Test Results Summary

| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |
| DC1-LEAF1A | BFD | VerifyBFDPeersIntervals | Verifies the timers of the IPv4 BFD peers in the specified VRF. | - | failure | Following BFD peers are not configured or timers are not correct: {'192.0.255.8': {'default': 'Not Configured'}, '192.0.255.7': {'default': 'Not Configured'}} |
| DC1-LEAF1A | BFD | VerifyBFDSpecificPeers | Verifies the IPv4 BFD peer's sessions and remote disc in the specified VRF. | - | failure | Following BFD peers are not configured, status is not up or remote disc is zero: {'192.0.255.8': {'default': 'Not Configured'}, '192.0.255.7': {'default': 'Not Configured'}} |
| DC1-LEAF1A | BGP | VerifyBGPAdvCommunities | Verifies the advertised communities of a BGP peer. | - | failure | Following BGP peers are not configured or advertised communities are not standard, extended, and large: {'bgp_peers': {'172.30.11.17': {'default': {'status': 'Not configured'}}, '172.30.11.21': {'default': {'status': 'Not configured'}}}} |
| DC1-LEAF1A | BGP | VerifyBGPExchangedRoutes | Verifies the advertised and received routes of BGP peers. | - | failure | Following BGP peers are not found or routes are not exchanged properly: {'bgp_peers': {'172.30.255.5': {'default': 'Not configured'}, '172.30.255.1': {'default': 'Not configured'}}} |
| DC1-LEAF1A | BGP | VerifyBGPPeerASNCap | Verifies the four octet asn capabilities of a BGP peer. | - | failure | Following BGP peer four octet asn capabilities are not found or not ok: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}}} |
| DC1-LEAF1A | BGP | VerifyBGPPeerCount | Verifies the count of BGP peers. | - | failure | Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'PROD': 'Expected: 2, Actual: 1'}}, {'afi': 'ipv4', 'safi': 'multicast', 'vrfs': {'DEV': 'Expected: 3, Actual: 0'}}] |
| DC1-LEAF1A | BGP | VerifyBGPPeerMD5Auth | Verifies the MD5 authentication and state of a BGP peer. | - | failure | Following BGP peers are not configured, not established or MD5 authentication is not enabled: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}, '172.30.11.5': {'default': {'status': 'Not configured'}}}} |
| DC1-LEAF1A | BGP | VerifyBGPPeerMPCaps | Verifies the multiprotocol capabilities of a BGP peer. | - | failure | Following BGP peer multiprotocol capabilities are not found or not ok: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}}} |
| DC1-LEAF1A | BGP | VerifyBGPPeerRouteRefreshCap | Verifies the route refresh capabilities of a BGP peer. | - | failure | Following BGP peer route refresh capabilities are not found or not ok: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}}} |
| DC1-LEAF1A | BGP | VerifyBGPPeersHealth | Verifies the health of BGP peers | - | failure | Failures: [{'afi': 'ipv6', 'safi': 'unicast', 'vrfs': {'DEV': 'No Peers'}}] |
| DC1-LEAF1A | BGP | VerifyBGPSpecificPeers | Verifies the health of specific BGP peer(s). | - | failure | Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'default': {'10.1.255.4': {'peerNotFound': True}}}}] |
| DC1-LEAF1A | BGP | VerifyBGPTimers | Verifies the timers of a BGP peer. | - | failure | Following BGP peers are not configured or hold and keep-alive timers are not correct: {'172.30.11.1': {'default': 'Not configured'}, '172.30.11.5': {'default': 'Not configured'}} |
| DC1-LEAF1A | Software | VerifyEOSVersion | Verifies the EOS version of the device. | - | failure | device is running version "4.31.1F-34554157.4311F (engineering build)" not in expected versions: ['4.25.4M', '4.26.1F'] |
| DC1-LEAF1A | BGP | VerifyEVPNType2Route | Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI. | - | failure | The following VXLAN endpoint do not have any EVPN Type-2 route: [('192.168.20.102', 10020), ('aa:c1:ab:5d:b4:1e', 10010)] |
| DC1-LEAF1A | Multicast | VerifyIGMPSnoopingVlans | Verifies the IGMP snooping status for the provided VLANs. | - | failure | IGMP state for vlan 10 is enabled, Supplied vlan 12 is not present on the device. |
| DC1-LEAF1A | Interfaces | VerifyInterfaceDiscards | Verifies there are no interface discard counters. | - | failure | The following interfaces have non 0 discard counter(s): [{'Management0': {'inDiscards': 180393, 'outDiscards': 0}}] |
| DC1-LEAF1A | Interfaces | VerifyInterfacesStatus | Verifies the status of the provided interfaces. | - | failure | The following interface(s) are not configured: ['Port-Channel100', 'Ethernet49/1'] |
| DC1-LEAF1A | Connectivity | VerifyLLDPNeighbors | Verifies that the provided LLDP neighbors are connected properly. | - | failure | Wrong LLDP neighbor(s) on port(s):    Ethernet1       DC1-SPINE1_Ethernet1    Ethernet2       DC1-SPINE2_Ethernet1 Port(s) not configured:    Ethernet7 |
| DC1-LEAF1A | System | VerifyNTP | Verifies if NTP is synchronised. | - | failure | The device is not synchronized with the configured NTP server(s): 'NTP is disabled.' |
| DC1-LEAF1A | Connectivity | VerifyReachability | Test the network reachability to one or many destination IP(s). | - | error | ping vrf MGMT 1.1.1.1 source Management1 repeat 2 has failed: No source interface Management1 |
| DC1-LEAF1A | Routing | VerifyRoutingTableSize | Verifies the size of the IP routing table of the default VRF. | - | failure | routing-table has 32 routes and not between min (2) and maximum (20) |
| DC1-LEAF1A | STP | VerifySTPMode | Verifies the configured STP mode for a provided list of VLAN(s). | - | failure | Wrong STP mode configured for the following VLAN(s): [10, 20] |
| DC1-LEAF1A | SNMP | VerifySnmpStatus | Verifies if the SNMP agent is enabled. | - | failure | SNMP agent disabled in vrf default |
| DC1-LEAF1A | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-LEAF1A | VLAN | VerifyVlanInternalPolicy | Verifies the VLAN internal allocation policy and the range of VLANs. | - | failure | The VLAN internal allocation policy is not configured properly: Expected '4094' as the endVlanId, but found '1199' instead. |
| DC1-SPINE1 | BFD | VerifyBFDPeersIntervals | Verifies the timers of the IPv4 BFD peers in the specified VRF. | - | failure | Following BFD peers are not configured or timers are not correct: {'192.0.255.8': {'default': 'Not Configured'}, '192.0.255.7': {'default': 'Not Configured'}} |
| DC1-SPINE1 | BFD | VerifyBFDSpecificPeers | Verifies the IPv4 BFD peer's sessions and remote disc in the specified VRF. | - | failure | Following BFD peers are not configured, status is not up or remote disc is zero: {'192.0.255.8': {'default': 'Not Configured'}, '192.0.255.7': {'default': 'Not Configured'}} |
| DC1-SPINE1 | BGP | VerifyBGPAdvCommunities | Verifies the advertised communities of a BGP peer. | - | failure | Following BGP peers are not configured or advertised communities are not standard, extended, and large: {'bgp_peers': {'172.30.11.17': {'default': {'status': 'Not configured'}}, '172.30.11.21': {'default': {'status': 'Not configured'}}}} |
| DC1-SPINE1 | BGP | VerifyBGPExchangedRoutes | Verifies the advertised and received routes of BGP peers. | - | failure | Following BGP peers are not found or routes are not exchanged properly: {'bgp_peers': {'172.30.255.5': {'default': 'Not configured'}, '172.30.255.1': {'default': 'Not configured'}}} |
| DC1-SPINE1 | BGP | VerifyBGPPeerASNCap | Verifies the four octet asn capabilities of a BGP peer. | - | failure | Following BGP peer four octet asn capabilities are not found or not ok: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}}} |
| DC1-SPINE1 | BGP | VerifyBGPPeerCount | Verifies the count of BGP peers. | - | failure | Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'PROD': 'Not Configured', 'default': 'Expected: 3, Actual: 4'}}, {'afi': 'ipv4', 'safi': 'multicast', 'vrfs': {'DEV': 'Not Configured'}}, {'afi': 'evpn', 'vrfs': {'default': 'Expected: 2, Actual: 4'}}] |
| DC1-SPINE1 | BGP | VerifyBGPPeerMD5Auth | Verifies the MD5 authentication and state of a BGP peer. | - | failure | Following BGP peers are not configured, not established or MD5 authentication is not enabled: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}, '172.30.11.5': {'default': {'status': 'Not configured'}}}} |
| DC1-SPINE1 | BGP | VerifyBGPPeerMPCaps | Verifies the multiprotocol capabilities of a BGP peer. | - | failure | Following BGP peer multiprotocol capabilities are not found or not ok: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}}} |
| DC1-SPINE1 | BGP | VerifyBGPPeerRouteRefreshCap | Verifies the route refresh capabilities of a BGP peer. | - | failure | Following BGP peer route refresh capabilities are not found or not ok: {'bgp_peers': {'172.30.11.1': {'default': {'status': 'Not configured'}}}} |
| DC1-SPINE1 | BGP | VerifyBGPPeersHealth | Verifies the health of BGP peers | - | failure | Failures: [{'afi': 'ipv6', 'safi': 'unicast', 'vrfs': {'DEV': 'Not Configured'}}] |
| DC1-SPINE1 | BGP | VerifyBGPSpecificPeers | Verifies the health of specific BGP peer(s). | - | failure | Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'default': {'10.1.254.1': {'peerNotFound': True}, '10.1.255.0': {'peerNotFound': True}, '10.1.255.2': {'peerNotFound': True}, '10.1.255.4': {'peerNotFound': True}}}}, {'afi': 'evpn', 'vrfs': {'default': {'10.1.0.1': {'peerNotFound': True}, '10.1.0.2': {'peerNotFound': True}}}}] |
| DC1-SPINE1 | BGP | VerifyBGPTimers | Verifies the timers of a BGP peer. | - | failure | Following BGP peers are not configured or hold and keep-alive timers are not correct: {'172.30.11.1': {'default': 'Not configured'}, '172.30.11.5': {'default': 'Not configured'}} |
| DC1-SPINE1 | Software | VerifyEOSVersion | Verifies the EOS version of the device. | - | failure | device is running version "4.31.1F-34554157.4311F (engineering build)" not in expected versions: ['4.25.4M', '4.26.1F'] |
| DC1-SPINE1 | BGP | VerifyEVPNType2Route | Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI. | - | failure | The following VXLAN endpoint do not have any EVPN Type-2 route: [('192.168.20.102', 10020), ('aa:c1:ab:5d:b4:1e', 10010)] |
| DC1-SPINE1 | Multicast | VerifyIGMPSnoopingVlans | Verifies the IGMP snooping status for the provided VLANs. | - | failure | Supplied vlan 10 is not present on the device., Supplied vlan 12 is not present on the device. |
| DC1-SPINE1 | Interfaces | VerifyInterfaceDiscards | Verifies there are no interface discard counters. | - | failure | The following interfaces have non 0 discard counter(s): [{'Management0': {'inDiscards': 180406, 'outDiscards': 0}}] |
| DC1-SPINE1 | Interfaces | VerifyInterfacesStatus | Verifies the status of the provided interfaces. | - | failure | The following interface(s) are not configured: ['Port-Channel100', 'Ethernet49/1'] |
| DC1-SPINE1 | System | VerifyNTP | Verifies if NTP is synchronised. | - | failure | The device is not synchronized with the configured NTP server(s): 'NTP is disabled.' |
| DC1-SPINE1 | Connectivity | VerifyReachability | Test the network reachability to one or many destination IP(s). | - | error | ping vrf MGMT 1.1.1.1 source Management1 repeat 2 has failed: No source interface Management1 |
| DC1-SPINE1 | Routing | VerifyRoutingTableEntry | Verifies that the provided routes are present in the routing table of a specified VRF. | - | failure | The following route(s) are missing from the routing table of VRF default: ['10.1.0.2'] |
| DC1-SPINE1 | Routing | VerifyRoutingTableSize | Verifies the size of the IP routing table of the default VRF. | - | failure | routing-table has 31 routes and not between min (2) and maximum (20) |
| DC1-SPINE1 | STP | VerifySTPMode | Verifies the configured STP mode for a provided list of VLAN(s). | - | failure | STP mode 'rapidPvst' not configured for the following VLAN(s): [10, 20] |
| DC1-SPINE1 | SNMP | VerifySnmpStatus | Verifies if the SNMP agent is enabled. | - | failure | SNMP agent disabled in vrf default |
| DC1-SPINE1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-SPINE1 | VLAN | VerifyVlanInternalPolicy | Verifies the VLAN internal allocation policy and the range of VLANs. | - | failure | The VLAN internal allocation policy is not configured properly: Expected '4094' as the endVlanId, but found '1199' instead. |
