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
| ----------- | ------------------- | ------------------- | ------------------- | ----------------- |
| 181 | 43 | 34 | 103 | 1 |

### Summary Totals Device Under Test

| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |
| ----------------- | ----------- | ------------- | ------------- | ------------- | ----------- | ------------------ | ----------------- |
| s1-spine1 | 181 | 43 | 34 | 103 | 1 | AVT, Field Notices, Flow Tracking, Hardware, ISIS, Interfaces, LANZ, OSPF, PTP, Path-Selection, Profiles, Segment-Routing | AAA, BFD, BGP, Configuration, Connectivity, Cvx, Greent, Interfaces, Logging, MLAG, Multicast, Routing, SNMP, STP, STUN, Security, Services, Software, VLAN, VXLAN |

### Summary Totals Per Category

| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |
| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |
| AAA | 7 | 0 | 0 | 7 | 0 |
| AVT | 3 | 0 | 3 | 0 | 0 |
| BFD | 4 | 1 | 0 | 3 | 0 |
| BGP | 25 | 3 | 0 | 21 | 1 |
| Configuration | 3 | 1 | 0 | 2 | 0 |
| Connectivity | 2 | 1 | 0 | 1 | 0 |
| Cvx | 5 | 0 | 0 | 5 | 0 |
| Field Notices | 2 | 0 | 2 | 0 | 0 |
| Flow Tracking | 1 | 0 | 1 | 0 | 0 |
| Greent | 2 | 0 | 0 | 2 | 0 |
| Hardware | 7 | 0 | 7 | 0 | 0 |
| Interfaces | 16 | 7 | 1 | 8 | 0 |
| ISIS | 7 | 0 | 7 | 0 | 0 |
| LANZ | 1 | 0 | 1 | 0 | 0 |
| Logging | 10 | 3 | 0 | 7 | 0 |
| MLAG | 6 | 4 | 0 | 2 | 0 |
| Multicast | 2 | 1 | 0 | 1 | 0 |
| OSPF | 3 | 0 | 3 | 0 | 0 |
| Path-Selection | 2 | 0 | 2 | 0 | 0 |
| Profiles | 2 | 0 | 2 | 0 | 0 |
| PTP | 5 | 0 | 5 | 0 | 0 |
| Routing | 6 | 2 | 0 | 4 | 0 |
| Security | 15 | 3 | 0 | 12 | 0 |
| Segment-Routing | 3 | 0 | 3 | 0 | 0 |
| Services | 4 | 1 | 0 | 3 | 0 |
| SNMP | 12 | 0 | 0 | 12 | 0 |
| Software | 3 | 1 | 0 | 2 | 0 |
| STP | 7 | 4 | 0 | 3 | 0 |
| STUN | 3 | 0 | 0 | 3 | 0 |
| System | 8 | 8 | 0 | 0 | 0 |
| VLAN | 3 | 0 | 0 | 3 | 0 |
| VXLAN | 5 | 3 | 0 | 2 | 0 |

## Test Results

| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |
| s1-spine1 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for commands, exec, system, dot1x |
| s1-spine1 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for commands, exec, system, dot1x |
| s1-spine1 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| s1-spine1 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods local, none, logging are not matching for commands, exec |
| s1-spine1 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| s1-spine1 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| s1-spine1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | VRF: MGMT Source Interface: Management0 - Not configured |
| s1-spine1 | AVT | VerifyAVTPathHealth | Verifies the status of all AVT paths for all VRFs. | - | skipped | VerifyAVTPathHealth test is not supported on cEOSLab |
| s1-spine1 | AVT | VerifyAVTRole | Verifies the AVT role of a device. | - | skipped | VerifyAVTRole test is not supported on cEOSLab |
| s1-spine1 | AVT | VerifyAVTSpecificPath | Verifies the Adaptive Virtual Topology (AVT) path. | - | skipped | VerifyAVTSpecificPath test is not supported on cEOSLab |
| s1-spine1 | BFD | VerifyBFDPeersHealth | Verifies the health of IPv4 BFD peers across all VRFs. | - | success | - |
| s1-spine1 | BFD | VerifyBFDPeersIntervals | Verifies the timers of IPv4 BFD peer sessions. | - | failure | Peer: 192.0.255.8 VRF: default - Not found<br>Peer: 192.0.255.7 VRF: default - Not found |
| s1-spine1 | BFD | VerifyBFDPeersRegProtocols | Verifies the registered routing protocol of IPv4 BFD peer sessions. | - | failure | Peer: 192.0.255.7 VRF: default - Not found |
| s1-spine1 | BFD | VerifyBFDSpecificPeers | Verifies the state of IPv4 BFD peer sessions. | - | failure | Peer: 192.0.255.8 VRF: default - Not found<br>Peer: 192.0.255.7 VRF: default - Not found |
| s1-spine1 | BGP | VerifyBGPAdvCommunities | Verifies the advertised communities of BGP peers. | - | failure | Peer: 172.30.11.17 VRF: default - Not found<br>Peer: 172.30.11.21 VRF: MGMT - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found |
| s1-spine1 | BGP | VerifyBGPExchangedRoutes | Verifies the advertised and received routes of BGP IPv4 peer(s). | - | failure | Peer: 172.30.255.5 VRF: default Advertised route: 192.0.254.5/32 - Not found<br>Peer: 172.30.255.5 VRF: default Received route: 192.0.255.4/32 - Not found<br>Peer: 172.30.255.1 VRF: default Advertised route: 192.0.255.1/32 - Not found<br>Peer: 172.30.255.1 VRF: default Advertised route: 192.0.254.5/32 - Not found |
| s1-spine1 | BGP | VerifyBGPNlriAcceptance | Verifies that all received NLRI are accepted for all AFI/SAFI configured for BGP peers. | - | failure | Peer: 10.100.0.128 VRF: default - Not found<br>Peer: 2001:db8:1::2 VRF: default - Not found<br>Peer: fe80::2%Et1 VRF: default - Not found<br>Peer: fe80::2%Et1 VRF: default - Not found |
| s1-spine1 | BGP | VerifyBGPPeerASNCap | Verifies the four octet ASN capability of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerCount | Verifies the count of BGP peers for given address families. | - | failure | AFI: ipv4 SAFI: unicast VRF: PROD - VRF not configured<br>AFI: ipv4 SAFI: multicast VRF: DEV - VRF not configured |
| s1-spine1 | BGP | VerifyBGPPeerDropStats | Verifies BGP NLRI drop statistics of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerGroup | Verifies BGP peer group of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerMD5Auth | Verifies the MD5 authentication and state of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: 172.30.11.5 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: default - Session does not have MD5 authentication enabled |
| s1-spine1 | BGP | VerifyBGPPeerMPCaps | Verifies the multiprotocol capabilities of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: default - ipv4MplsLabels not found<br>Interface: Ethernet1 VRF: default - ipv4MplsVpn not found |
| s1-spine1 | BGP | VerifyBGPPeerRouteLimit | Verifies maximum routes and warning limit for BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerRouteRefreshCap | Verifies the route refresh capabilities of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | - | failure | Peer: 10.1.0.1 VRF: default - Not found<br>Peer: 10.1.0.2 VRF: default - Not found<br>Peer: 10.1.255.2 VRF: DEV - Not found<br>Peer: 10.1.255.4 VRF: DEV - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Vlan3499 VRF: PROD - Not found |
| s1-spine1 | BGP | VerifyBGPPeerSessionRibd | Verifies the session state of BGP peers. | - | failure | Peer: 10.1.0.1 VRF: default - Not found<br>Peer: 10.1.255.4 VRF: DEV - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerTtlMultiHops | Verifies BGP TTL and max-ttl-hops count for BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: 172.30.11.2 VRF: test - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeerUpdateErrors | Verifies BGP update error counters of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBGPPeersHealth | Verifies the health of BGP peers for given address families. | - | failure | AFI: ipv6 SAFI: unicast VRF: DEV - VRF not configured |
| s1-spine1 | BGP | VerifyBGPPeersHealthRibd | Verifies the health of all the BGP peers. | - | success | - |
| s1-spine1 | BGP | VerifyBGPRedistribution | Verifies BGP redistribution. | - | error | show bgp instance vrf all has failed: Invalid requested version for ModelMetaClass: no such revision 4, most current is 3 |
| s1-spine1 | BGP | VerifyBGPRouteECMP | Verifies BGP IPv4 route ECMP paths. | - | success | - |
| s1-spine1 | BGP | VerifyBGPRoutePaths | Verifies BGP IPv4 route paths. | - | success | - |
| s1-spine1 | BGP | VerifyBGPSpecificPeers | Verifies the health of specific BGP peer(s) for given address families. | - | failure | AFI: evpn Peer: 10.1.0.1 - Not configured<br>AFI: evpn Peer: 10.1.0.2 - Not configured<br>AFI: ipv4 SAFI: unicast VRF: default Peer: 10.1.254.1 - Not configured<br>AFI: ipv4 SAFI: unicast VRF: default Peer: 10.1.255.0 - Not configured<br>AFI: ipv4 SAFI: unicast VRF: default Peer: 10.1.255.2 - Not configured<br>AFI: ipv4 SAFI: unicast VRF: default Peer: 10.1.255.4 - Not configured |
| s1-spine1 | BGP | VerifyBGPTimers | Verifies the timers of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: 172.30.11.5 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyBgpRouteMaps | Verifies BGP inbound and outbound route-maps of BGP peers. | - | failure | Peer: 172.30.11.1 VRF: default - Not found<br>Peer: fd00:dc:1::1 VRF: default - Not found<br>Interface: Ethernet1 VRF: MGMT - Not found |
| s1-spine1 | BGP | VerifyEVPNType2Route | Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI. | - | failure | Address: 192.168.20.102 VNI: 10020 - No EVPN Type-2 route<br>Address: aa:c1:ab:5d:b4:1e VNI: 10010 - No EVPN Type-2 route |
| s1-spine1 | BGP | VerifyEVPNType5Routes | Verifies EVPN Type-5 routes for given IP prefixes and VNIs. | - | failure | Prefix: 192.168.10.0/24 VNI: 10 - No EVPN Type-5 routes found<br>Prefix: 192.168.20.0/24 VNI: 20 - No EVPN Type-5 routes found<br>Prefix: 192.168.30.0/24 VNI: 30 - No EVPN Type-5 routes found<br>Prefix: 192.168.40.0/24 VNI: 40 - No EVPN Type-5 routes found |
| s1-spine1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | - | failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -18,6 +18,7 @@<br> hostname leaf1-dc1<br> ip name-server vrf MGMT 10.14.0.1<br> dns domain fun.aristanetworks.com<br>+ip host vitthal 192.168.66.220<br> !<br> platform tfa<br>    personality arfa<br> |
| s1-spine1 | Configuration | VerifyRunningConfigLines | Search the Running-Config for the given RegEx patterns. | - | failure | Following patterns were not found: '^enable password.*$', 'bla bla' |
| s1-spine1 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | - | success | - |
| s1-spine1 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | - | failure | Port: Ethernet1 Neighbor: DC1-SPINE1 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: spine1-dc1.fun.aristanetworks.com/Ethernet3<br>Port: Ethernet2 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: spine2-dc1.fun.aristanetworks.com/Ethernet3 |
| s1-spine1 | Connectivity | VerifyReachability | Test network reachability to one or many destination IP(s). | - | success | - |
| s1-spine1 | Cvx | VerifyActiveCVXConnections | Verifies the number of active CVX Connections. | - | failure | 'show cvx connections brief' failed on s1-spine1: Unavailable command (controller not ready) (at token 2: 'connections') |
| s1-spine1 | Cvx | VerifyCVXClusterStatus | Verifies the CVX Server Cluster status. | - | failure | CVX Server status is not enabled<br>CVX Server is not a cluster |
| s1-spine1 | Cvx | VerifyManagementCVX | Verifies the management CVX global status. | - | failure | Management CVX status is not valid: Expected: enabled Actual: disabled |
| s1-spine1 | Cvx | VerifyMcsClientMounts | Verify if all MCS client mounts are in mountStateMountComplete. | - | failure | MCS Client mount states are not present |
| s1-spine1 | Cvx | VerifyMcsServerMounts | Verify if all MCS server mounts are in a MountComplete state. | - | failure | 'show cvx mounts' failed on s1-spine1: Unavailable command (controller not ready) (at token 2: 'mounts') |
| s1-spine1 | Field Notices | VerifyFieldNotice44Resolution | Verifies that the device is using the correct Aboot version per FN0044. | - | skipped | VerifyFieldNotice44Resolution test is not supported on cEOSLab |
| s1-spine1 | Field Notices | VerifyFieldNotice72Resolution | Verifies if the device is exposed to FN0072, and if the issue has been mitigated. | - | skipped | VerifyFieldNotice72Resolution test is not supported on cEOSLab |
| s1-spine1 | Flow Tracking | VerifyHardwareFlowTrackerStatus | Verifies the hardware flow tracking state. | - | skipped | VerifyHardwareFlowTrackerStatus test is not supported on cEOSLab |
| s1-spine1 | Greent | VerifyGreenT | Verifies if a GreenT policy other than the default is created. | - | failure | No GreenT policy is created |
| s1-spine1 | Greent | VerifyGreenTCounters | Verifies if the GreenT counters are incremented. | - | failure | GreenT counters are not incremented |
| s1-spine1 | Hardware | VerifyAdverseDrops | Verifies there are no adverse drops on DCS-7280 and DCS-7500 family switches. | - | skipped | VerifyAdverseDrops test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | - | skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyEnvironmentPower | Verifies the power supplies status. | - | skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | - | skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | - | skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | - | skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | - | skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-spine1 | Interfaces | VerifyIPProxyARP | Verifies if Proxy ARP is enabled. | - | failure | Interface: Ethernet1 - Proxy-ARP disabled<br>Interface: Ethernet2 - Proxy-ARP disabled |
| s1-spine1 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in all port channels. | - | success | - |
| s1-spine1 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | - | success | - |
| s1-spine1 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | - | success | - |
| s1-spine1 | Interfaces | VerifyInterfaceIPv4 | Verifies the interface IPv4 addresses. | - | failure | Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.1/31 Actual: 10.100.0.11/31<br>Interface: Ethernet2 - Secondary IP address is not configured |
| s1-spine1 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | - | success | - |
| s1-spine1 | Interfaces | VerifyInterfacesSpeed | Verifies the speed, lanes, auto-negotiation status, and mode as full duplex for interfaces. | - | failure | Interface: Ethernet2 - Bandwidth mismatch - Expected: 10.0Gbps Actual: 1Gbps<br>Interface: Ethernet3 - Bandwidth mismatch - Expected: 100.0Gbps Actual: 1Gbps<br>Interface: Ethernet3 - Auto-negotiation mismatch - Expected: success Actual: unknown<br>Interface: Ethernet3 - Data lanes count mismatch - Expected: 1 Actual: 0<br>Interface: Ethernet2 - Bandwidth mismatch - Expected: 2.5Gbps Actual: 1Gbps |
| s1-spine1 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | interface | failure | Port-Channel100 - Not configured<br>Ethernet49/1 - Not configured |
| s1-spine1 | Interfaces | VerifyIpVirtualRouterMac | Verifies the IP virtual router MAC address. | - | success | - |
| s1-spine1 | Interfaces | VerifyL2MTU | Verifies the global L2 MTU of all L2 interfaces. | - | failure | Interface: Ethernet3 - Incorrect MTU configured - Expected: 1500 Actual: 9214<br>Interface: Port-Channel5 - Incorrect MTU configured - Expected: 1500 Actual: 9214 |
| s1-spine1 | Interfaces | VerifyL3MTU | Verifies the global L3 MTU of all L3 interfaces. | - | failure | Interface: Ethernet2 - Incorrect MTU - Expected: 1500 Actual: 9214<br>Interface: Ethernet1 - Incorrect MTU - Expected: 2500 Actual: 9214<br>Interface: Loopback0 - Incorrect MTU - Expected: 1500 Actual: 65535<br>Interface: Loopback1 - Incorrect MTU - Expected: 1500 Actual: 65535<br>Interface: Vlan1006 - Incorrect MTU - Expected: 1500 Actual: 9164<br>Interface: Vlan1199 - Incorrect MTU - Expected: 1500 Actual: 9164<br>Interface: Vlan4093 - Incorrect MTU - Expected: 1500 Actual: 9214<br>Interface: Vlan4094 - Incorrect MTU - Expected: 1500 Actual: 9214<br>Interface: Vlan3019 - Incorrect MTU - Expected: 1500 Actual: 9214<br>Interface: Vlan3009 - Incorrect MTU - Expected: 1500 Actual: 9214 |
| s1-spine1 | Interfaces | VerifyLACPInterfacesStatus | Verifies the Link Aggregation Control Protocol (LACP) status of the interface. | - | failure | Interface: Ethernet1 Port-Channel: Port-Channel100 - Not configured |
| s1-spine1 | Interfaces | VerifyLoopbackCount | Verifies the number of loopback interfaces and their status. | - | failure | Loopback interface(s) count mismatch: Expected 3 Actual: 2 |
| s1-spine1 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in all port channels. | - | success | - |
| s1-spine1 | Interfaces | VerifySVI | Verifies the status of all SVIs. | - | success | - |
| s1-spine1 | Interfaces | VerifyStormControlDrops | Verifies there are no interface storm-control drop counters. | - | skipped | VerifyStormControlDrops test is not supported on cEOSLab |
| s1-spine1 | ISIS | VerifyISISGracefulRestart | Verifies the IS-IS graceful restart feature. | - | skipped | IS-IS not configured |
| s1-spine1 | ISIS | VerifyISISInterfaceMode | Verifies IS-IS interfaces are running in the correct mode. | - | skipped | IS-IS not configured |
| s1-spine1 | ISIS | VerifyISISNeighborCount | Verifies the number of IS-IS neighbors per interface and level. | - | skipped | IS-IS not configured |
| s1-spine1 | ISIS | VerifyISISNeighborState | Verifies the health of IS-IS neighbors. | - | skipped | IS-IS not configured |
| s1-spine1 | ISIS, Segment-Routing | VerifyISISSegmentRoutingAdjacencySegments | Verifies IS-IS segment routing adjacency segments. | - | skipped | IS-IS not configured |
| s1-spine1 | ISIS, Segment-Routing | VerifyISISSegmentRoutingDataplane | Verifies IS-IS segment routing data-plane configuration. | - | skipped | IS-IS not configured |
| s1-spine1 | ISIS, Segment-Routing | VerifyISISSegmentRoutingTunnels | Verify ISIS-SR tunnels computed by device. | - | skipped | IS-IS-SR not configured |
| s1-spine1 | LANZ | VerifyLANZ | Verifies if LANZ is enabled. | - | skipped | VerifyLANZ test is not supported on cEOSLab |
| s1-spine1 | Logging | VerifyLoggingAccounting | Verifies if AAA accounting logs are generated. | - | success | - |
| s1-spine1 | Logging | VerifyLoggingEntries | Verifies that the expected log string is present in the last specified log messages. | - | failure | Pattern: `.*ACCOUNTING-5-EXEC: cvpadmin ssh.*` - Not found in last 30 alerts log entries<br>Pattern: `.*SPANTREE-6-INTERFACE_ADD:.*` - Not found in last 10 critical log entries |
| s1-spine1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | - | failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Apr 29 08:01:27 leaf1-dc1 Bgp: %BGP-3-NOTIFICATION: sent to neighbor 10.100.4.5 (VRF data AS 65102) 6/7 (Cease/connection collision resolution) 0 bytes <br> Apr 29 08:01:27 leaf1-dc1 Bgp: %BGP-3-NOTIFICATION: sent to neighbor 10.100.4.5 (VRF guest AS 65102) 6/7 (Cease/connection collision resolution) 0 bytes <br> Apr 29 08:01:29 leaf1-dc1 Bgp: %BGP-3-NOTIFICATION: received from neighbor 10.100.4.5 (VRF guest AS 65102) 6/7 (Cease/connection collision resolution) 0 bytes <br> <br> |
| s1-spine1 | Logging | VerifyLoggingHostname | Verifies if logs are generated with the device FQDN. | - | failure | Logs are not generated with the device FQDN |
| s1-spine1 | Logging | VerifyLoggingHosts | Verifies logging hosts (syslog servers) for a specified VRF. | - | failure | Syslog servers 1.1.1.1, 2.2.2.2 are not configured in VRF default |
| s1-spine1 | Logging | VerifyLoggingLogsGeneration | Verifies if logs are generated. | - | success | - |
| s1-spine1 | Logging | VerifyLoggingPersistent | Verifies if logging persistent is enabled and logs are saved in flash. | - | failure | Persistent logging is disabled |
| s1-spine1 | Logging | VerifyLoggingSourceIntf | Verifies logging source-interface for a specified VRF. | - | failure | Source-interface: Management0 VRF: default - Not configured |
| s1-spine1 | Logging | VerifyLoggingTimestamp | Verifies if logs are generated with the appropriate timestamp. | - | failure | Logs are not generated with the appropriate timestamp format |
| s1-spine1 | Logging | VerifySyslogLogging | Verifies if syslog logging is enabled. | - | success | - |
| s1-spine1 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | - | success | - |
| s1-spine1 | MLAG | VerifyMlagDualPrimary | Verifies the MLAG dual-primary detection parameters. | - | failure | Dual-primary detection is disabled |
| s1-spine1 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | - | success | - |
| s1-spine1 | MLAG | VerifyMlagPrimaryPriority | Verifies the configuration of the MLAG primary priority. | - | failure | MLAG primary priority mismatch - Expected: 3276 Actual: 32767 |
| s1-spine1 | MLAG | VerifyMlagReloadDelay | Verifies the reload-delay parameters of the MLAG configuration. | - | success | - |
| s1-spine1 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | - | success | - |
| s1-spine1 | Multicast | VerifyIGMPSnoopingGlobal | Verifies the IGMP snooping global status. | - | success | - |
| s1-spine1 | Multicast | VerifyIGMPSnoopingVlans | Verifies the IGMP snooping status for the provided VLANs. | - | failure | VLAN10 - Incorrect IGMP state - Expected: disabled Actual: enabled<br>Supplied vlan 12 is not present on the device |
| s1-spine1 | OSPF | VerifyOSPFMaxLSA | Verifies all OSPF instances did not cross the maximum LSA threshold. | - | skipped | OSPF not configured |
| s1-spine1 | OSPF | VerifyOSPFNeighborCount | Verifies the number of OSPF neighbors in FULL state is the one we expect. | - | skipped | OSPF not configured |
| s1-spine1 | OSPF | VerifyOSPFNeighborState | Verifies all OSPF neighbors are in FULL state. | - | skipped | OSPF not configured |
| s1-spine1 | Path-Selection | VerifyPathsHealth | Verifies the path and telemetry state of all paths under router path-selection. | - | skipped | VerifyPathsHealth test is not supported on cEOSLab |
| s1-spine1 | Path-Selection | VerifySpecificPath | Verifies the DPS path and telemetry state of an IPv4 peer. | - | skipped | VerifySpecificPath test is not supported on cEOSLab |
| s1-spine1 | Profiles | VerifyTcamProfile | Verifies the device TCAM profile. | - | skipped | VerifyTcamProfile test is not supported on cEOSLab |
| s1-spine1 | Profiles | VerifyUnifiedForwardingTableMode | Verifies the device is using the expected UFT mode. | - | skipped | VerifyUnifiedForwardingTableMode test is not supported on cEOSLab |
| s1-spine1 | PTP | VerifyPtpGMStatus | Verifies that the device is locked to a valid PTP Grandmaster. | - | skipped | VerifyPtpGMStatus test is not supported on cEOSLab |
| s1-spine1 | PTP | VerifyPtpLockStatus | Verifies that the device was locked to the upstream PTP GM in the last minute. | - | skipped | VerifyPtpLockStatus test is not supported on cEOSLab |
| s1-spine1 | PTP | VerifyPtpModeStatus | Verifies that the device is configured as a PTP Boundary Clock. | - | skipped | VerifyPtpModeStatus test is not supported on cEOSLab |
| s1-spine1 | PTP | VerifyPtpOffset | Verifies that the PTP timing offset is within +/- 1000ns from the master clock. | - | skipped | VerifyPtpOffset test is not supported on cEOSLab |
| s1-spine1 | PTP | VerifyPtpPortModeStatus | Verifies the PTP interfaces state. | - | skipped | VerifyPtpPortModeStatus test is not supported on cEOSLab |
| s1-spine1 | Routing | VerifyIPv4RouteNextHops | Verifies the next-hops of the IPv4 prefixes. | - | success | - |
| s1-spine1 | Routing | VerifyIPv4RouteType | Verifies the route-type of the IPv4 prefixes. | - | failure | Prefix: 10.100.0.12/31 VRF: default - Route not found<br>Prefix: 10.100.1.5/32 VRF: default - Incorrect route type - Expected: iBGP Actual: connected |
| s1-spine1 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | - | success | - |
| s1-spine1 | Routing | VerifyRoutingStatus | Verifies the routing status for IPv4/IPv6 unicast, multicast, and IPv6 interfaces (RFC5549). | - | failure | IPv6 unicast routing enabled status mismatch - Expected: True Actual: False |
| s1-spine1 | Routing | VerifyRoutingTableEntry | Verifies that the provided routes are present in the routing table of a specified VRF. | - | failure | The following route(s) are missing from the routing table of VRF default: 10.1.0.1, 10.1.0.2 |
| s1-spine1 | Routing | VerifyRoutingTableSize | Verifies the size of the IP routing table of the default VRF. | - | failure | Routing table routes are outside the routes range - Expected: 2 <= to >= 20 Actual: 35 |
| s1-spine1 | Security | VerifyAPIHttpStatus | Verifies if eAPI HTTP server is disabled globally. | - | success | - |
| s1-spine1 | Security | VerifyAPIHttpsSSL | Verifies if the eAPI has a valid SSL profile. | - | failure | eAPI HTTPS server SSL profile default is not configured |
| s1-spine1 | Security | VerifyAPIIPv4Acl | Verifies if eAPI has the right number IPv4 ACL(s) configured for a specified VRF. | - | failure | VRF: default - eAPI IPv4 ACL(s) count mismatch - Expected: 3 Actual: 0 |
| s1-spine1 | Security | VerifyAPIIPv6Acl | Verifies if eAPI has the right number IPv6 ACL(s) configured for a specified VRF. | - | failure | VRF: default - eAPI IPv6 ACL(s) count mismatch - Expected: 3 Actual: 0 |
| s1-spine1 | Security | VerifyAPISSLCertificate | Verifies the eAPI SSL certificate expiry, common subject name, encryption algorithm and key size. | - | success | - |
| s1-spine1 | Security | VerifyBannerLogin | Verifies the login banner of a device. | - | failure | Login banner is not configured |
| s1-spine1 | Security | VerifyBannerMotd | Verifies the motd banner of a device. | - | failure | MOTD banner is not configured |
| s1-spine1 | Security | VerifyHardwareEntropy | Verifies hardware entropy generation is enabled on device. | - | failure | Hardware entropy generation is disabled |
| s1-spine1 | Security | VerifyIPSecConnHealth | Verifies all IPv4 security connections. | - | failure | No IPv4 security connection configured |
| s1-spine1 | Security | VerifyIPv4ACL | Verifies the configuration of IPv4 ACLs. | - | failure | ACL name: LabTest - Not configured |
| s1-spine1 | Security | VerifySSHIPv4Acl | Verifies if the SSHD agent has IPv4 ACL(s) configured. | - | failure | VRF: default - SSH IPv4 ACL(s) count mismatch - Expected: 3 Actual: 0 |
| s1-spine1 | Security | VerifySSHIPv6Acl | Verifies if the SSHD agent has IPv6 ACL(s) configured. | - | failure | VRF: default - SSH IPv6 ACL(s) count mismatch - Expected: 3 Actual: 0 |
| s1-spine1 | Security | VerifySSHStatus | Verifies if the SSHD agent is disabled in the default VRF. | - | failure | SSHD status for Default VRF is enabled |
| s1-spine1 | Security | VerifySpecificIPSecConn | Verifies the IPv4 security connections. | - | failure | Peer: 10.255.0.1 VRF: default - Not configured<br>Peer: 10.255.0.2 VRF: default - Not configured |
| s1-spine1 | Security | VerifyTelnetStatus | Verifies if Telnet is disabled in the default VRF. | - | success | - |
| s1-spine1 | Services | VerifyDNSLookup | Verifies the DNS name to IP address resolution. | - | success | - |
| s1-spine1 | Services | VerifyDNSServers | Verifies if the DNS (Domain Name Service) servers are correctly configured. | - | failure | Server 10.14.0.1 VRF: default Priority: 1 - Not configured<br>Server 10.14.0.11 VRF: MGMT Priority: 0 - Not configured |
| s1-spine1 | Services | VerifyErrdisableRecovery | Verifies the error disable recovery functionality. | - | failure | Reason: acl Status: Enabled Interval: 30 - Incorrect configuration - Status: Disabled Interval: 300<br>Reason: bpduguard Status: Enabled Interval: 30 - Incorrect configuration - Status: Disabled Interval: 300 |
| s1-spine1 | Services | VerifyHostname | Verifies the hostname of a device. | - | failure | Incorrect Hostname - Expected: s1-spine1 Actual: leaf1-dc1 |
| s1-spine1 | SNMP | VerifySnmpContact | Verifies the SNMP contact of a device. | - | failure | SNMP contact is not configured |
| s1-spine1 | SNMP | VerifySnmpErrorCounters | Verifies the SNMP error counters. | - | failure | SNMP counters not found |
| s1-spine1 | SNMP | VerifySnmpGroup | Verifies the SNMP group configurations for specified version(s). | - | failure | Group: Group1 Version: v1 - Not configured<br>Group: Group2 Version: v3 - Not configured |
| s1-spine1 | SNMP | VerifySnmpHostLogging | Verifies SNMP logging configurations. | - | failure | SNMP logging is disabled |
| s1-spine1 | SNMP | VerifySnmpIPv4Acl | Verifies if the SNMP agent has IPv4 ACL(s) configured. | - | failure | VRF: default - Incorrect SNMP IPv4 ACL(s) - Expected: 3 Actual: 0 |
| s1-spine1 | SNMP | VerifySnmpIPv6Acl | Verifies if the SNMP agent has IPv6 ACL(s) configured. | - | failure | VRF: default - Incorrect SNMP IPv6 ACL(s) - Expected: 3 Actual: 0 |
| s1-spine1 | SNMP | VerifySnmpLocation | Verifies the SNMP location of a device. | - | failure | SNMP location is not configured |
| s1-spine1 | SNMP | VerifySnmpNotificationHost | Verifies the SNMP notification host(s) (SNMP manager) configurations. | - | failure | No SNMP host is configured |
| s1-spine1 | SNMP | VerifySnmpPDUCounters | Verifies the SNMP PDU counters. | - | failure | SNMP counters not found |
| s1-spine1 | SNMP | VerifySnmpSourceInterface | Verifies SNMP source interfaces. | - | failure | SNMP source interface(s) not configured |
| s1-spine1 | SNMP | VerifySnmpStatus | Verifies if the SNMP agent is enabled. | - | failure | VRF: default - SNMP agent disabled |
| s1-spine1 | SNMP | VerifySnmpUser | Verifies the SNMP user configurations. | - | failure | User: test Group: test_group Version: v3 - Not found |
| s1-spine1 | Software | VerifyEOSExtensions | Verifies that all EOS extensions installed on the device are enabled for boot persistence. | - | success | - |
| s1-spine1 | Software | VerifyEOSVersion | Verifies the EOS version of the device. | - | failure | EOS version mismatch - Actual: 4.31.0F-33804048.4310F (engineering build) not in Expected: 4.25.4M, 4.26.1F |
| s1-spine1 | Software | VerifyTerminAttrVersion | Verifies the TerminAttr version of the device. | - | failure | TerminAttr version mismatch - Actual: v1.29.0 not in Expected: v1.13.6, v1.8.0 |
| s1-spine1 | STP | VerifySTPBlockedPorts | Verifies there is no STP blocked ports. | - | success | - |
| s1-spine1 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | - | success | - |
| s1-spine1 | STP | VerifySTPDisabledVlans | Verifies the STP disabled VLAN(s). | - | failure | VLAN: 6 - Not configured |
| s1-spine1 | STP | VerifySTPForwardingPorts | Verifies that all interfaces are forwarding for a provided list of VLAN(s). | - | success | - |
| s1-spine1 | STP | VerifySTPMode | Verifies the configured STP mode for a provided list of VLAN(s). | - | failure | VLAN 10 - Incorrect STP mode - Expected: rapidPvst Actual: mstp<br>VLAN 20 - Incorrect STP mode - Expected: rapidPvst Actual: mstp |
| s1-spine1 | STP | VerifySTPRootPriority | Verifies the STP root priority for a provided list of VLAN or MST instance ID(s). | - | failure | Instance: MST10 - Not configured<br>Instance: MST20 - Not configured |
| s1-spine1 | STP | VerifyStpTopologyChanges | Verifies the number of changes across all interfaces in the Spanning Tree Protocol (STP) topology is below a threshold. | - | success | - |
| s1-spine1 | STUN | VerifyStunClient | (Deprecated) Verifies the translation for a source address on a STUN client. | - | failure | Client 172.18.3.2 Port: 4500 - STUN client translation not found |
| s1-spine1 | STUN | VerifyStunClientTranslation | Verifies the translation for a source address on a STUN client. | - | failure | Client 172.18.3.2 Port: 4500 - STUN client translation not found<br>Client 100.64.3.2 Port: 4500 - STUN client translation not found |
| s1-spine1 | STUN | VerifyStunServer | Verifies the STUN server status is enabled and running. | - | failure | STUN server status is disabled and not running |
| s1-spine1 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | - | success | - |
| s1-spine1 | System | VerifyCPUUtilization | Verifies whether the CPU utilization is below 75%. | - | success | - |
| s1-spine1 | System | VerifyCoredump | Verifies there are no core dump files. | - | success | - |
| s1-spine1 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | - | success | - |
| s1-spine1 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | - | success | - |
| s1-spine1 | System | VerifyNTP | Verifies if NTP is synchronised. | - | success | - |
| s1-spine1 | System | VerifyReloadCause | Verifies the last reload cause of the device. | reload-cause | success | - |
| s1-spine1 | System | VerifyUptime | Verifies the device uptime. | - | success | - |
| s1-spine1 | VLAN | VerifyDynamicVlanSource | Verifies dynamic VLAN allocation for specified VLAN sources. | - | failure | Dynamic VLAN source(s) exist but have no VLANs allocated: mlagsync |
| s1-spine1 | VLAN | VerifyVlanInternalPolicy | Verifies the VLAN internal allocation policy and the range of VLANs. | - | failure | VLAN internal allocation policy: ascending - Incorrect end VLAN id configured - Expected: 4094 Actual: 1199 |
| s1-spine1 | VLAN | VerifyVlanStatus | Verifies the administrative status of specified VLANs. | - | failure | VLAN: Vlan10 - Incorrect administrative status - Expected: suspended Actual: active |
| s1-spine1 | VXLAN | VerifyVxlan1ConnSettings | Verifies Vxlan1 source interface and UDP port. | - | success | - |
| s1-spine1 | VXLAN | VerifyVxlan1Interface | Verifies the Vxlan1 interface status. | - | success | - |
| s1-spine1 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | - | success | - |
| s1-spine1 | VXLAN | VerifyVxlanVniBinding | Verifies the VNI-VLAN, VNI-VRF bindings of the Vxlan1 interface. | - | failure | Interface: Vxlan1 VNI: 500 - Binding not found |
| s1-spine1 | VXLAN | VerifyVxlanVtep | Verifies Vxlan1 VTEP peers. | - | failure | The following VTEP peer(s) are missing from the Vxlan1 interface: 10.1.1.5, 10.1.1.6<br>Unexpected VTEP peer(s) on Vxlan1 interface: 10.100.2.3 |
