# ANTA Report

**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Test Results Summary](#test-results-summary)
    - [Summary Totals](#summary-totals)
    - [Summary Totals Device Under Test](#summary-totals-device-under-test)
    - [Summary Totals Per Category](#summary-totals-per-category)
    - [FailedTestResultsSummary](#failed-test-results-summary)
  - [Test Results](#test-results)

## Test Results Summary

### Summary Totals

| Total Tests | Total Tests Success | Total Tests Skipped | Total Tests Failure | Total Tests Error |
| ----------- | ------------------- | ------------------- | ------------------- | ------------------|
| 30 | 11 | 9 | 8 | 2 |

### Summary Totals Device Under Test

| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |
| ------------------| ----------- | ------------- | ------------- | ------------- | ----------- | -------------------| ------------------|
| s1-leaf1 | 30 | 11 | 9 | 8 | 2 | AVT, Field Notices, Flow Tracking, Hardware, LANZ, PTP, VXLAN | Cvx, Greent, Interfaces, Logging, VLAN |

### Summary Totals Per Category

| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |
| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |
| AVT | 2 | 0 | 2 | 0 | 0 |
| BGP | 1 | 1 | 0 | 0 | 0 |
| Cvx | 3 | 0 | 0 | 1 | 2 |
| Field Notices | 1 | 0 | 1 | 0 | 0 |
| Flow Tracking | 1 | 0 | 1 | 0 | 0 |
| Greent | 2 | 0 | 0 | 2 | 0 |
| Hardware | 1 | 0 | 1 | 0 | 0 |
| Interfaces | 8 | 6 | 0 | 2 | 0 |
| LANZ | 1 | 0 | 1 | 0 | 0 |
| Logging | 3 | 1 | 0 | 2 | 0 |
| MLAG | 2 | 2 | 0 | 0 | 0 |
| PTP | 1 | 0 | 1 | 0 | 0 |
| VLAN | 2 | 1 | 0 | 1 | 0 |
| VXLAN | 2 | 0 | 2 | 0 | 0 |

## Failed Test Results Summary

| Device Under Test | Categories | Test | Description | Custom Field  | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | --------------| -------| -------- |
| s1-leaf1 | Cvx | VerifyActiveCVXConnections | Verifies the number of active CVX Connections. | - | error | show cvx connections brief has failed: Unavailable command (controller not ready) (at token 2: 'connections') |
| s1-leaf1 | Cvx | VerifyMcsServerMounts | Verify if all MCS server mounts are in a MountComplete state. | - | error | show cvx mounts has failed: Unavailable command (controller not ready) (at token 2: 'mounts') |
| s1-leaf1 | Cvx | VerifyMcsClientMounts | Verify if all MCS client mounts are in mountStateMountComplete. | - | failure | MCS Client mount states are not present |
| s1-leaf1 | Greent | VerifyGreenT | Verifies if a GreenT policy other than the default is created. | - | failure | No GreenT policy is created |
| s1-leaf1 | Greent | VerifyGreenTCounters | Verifies if the GreenT counters are incremented. | - | failure | GreenT counters are not incremented |
| s1-leaf1 | Interfaces | VerifyIPProxyARP | Verifies if Proxy ARP is enabled. | - | failure | Interface: Ethernet1 - Not found<br>Interface: Ethernet2 - Proxy-ARP disabled |
| s1-leaf1 | Interfaces | VerifyInterfaceIPv4 | Verifies the interface IPv4 addresses. | - | failure | Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.1/31 Actual: 10.111.1.1/31<br>Interface: Ethernet2 - Secondary IP address is not configured |
| s1-leaf1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | - | failure | Device has reported syslog messages with a severity of ERRORS or higher |
| s1-leaf1 | Logging | VerifyLoggingHostname | Verifies if logs are generated with the device FQDN. | - | failure | Logs are not generated with the device FQDN |
| s1-leaf1 | VLAN | VerifyDynamicVlanSource | Verifies dynamic VLAN allocation for specified VLAN sources. | - | failure | Dynamic VLAN source(s) not found in configuration: mlagsync |

## Test Results

| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |
| s1-leaf1 | AVT | VerifyAVTPathHealth | Verifies the status of all AVT paths for all VRFs. | - | skipped | VerifyAVTPathHealth test is not supported on cEOSLab. |
| s1-leaf1 | AVT | VerifyAVTRole | Verifies the AVT role of a device. | - | skipped | VerifyAVTRole test is not supported on cEOSLab. |
| s1-leaf1 | BGP | VerifyBGPPeersHealthRibd | Verifies the health of all the BGP IPv4 peer(s). | - | success | - |
| s1-leaf1 | Cvx | VerifyActiveCVXConnections | Verifies the number of active CVX Connections. | - | error | show cvx connections brief has failed: Unavailable command (controller not ready) (at token 2: 'connections') |
| s1-leaf1 | Cvx | VerifyMcsClientMounts | Verify if all MCS client mounts are in mountStateMountComplete. | - | failure | MCS Client mount states are not present |
| s1-leaf1 | Cvx | VerifyMcsServerMounts | Verify if all MCS server mounts are in a MountComplete state. | - | error | show cvx mounts has failed: Unavailable command (controller not ready) (at token 2: 'mounts') |
| s1-leaf1 | Field Notices | VerifyFieldNotice44Resolution | Verifies that the device is using the correct Aboot version per FN0044. | - | skipped | VerifyFieldNotice44Resolution test is not supported on cEOSLab. |
| s1-leaf1 | Flow Tracking | VerifyHardwareFlowTrackerStatus | Verifies the hardware flow tracking state. | - | skipped | VerifyHardwareFlowTrackerStatus test is not supported on cEOSLab. |
| s1-leaf1 | Greent | VerifyGreenT | Verifies if a GreenT policy other than the default is created. | - | failure | No GreenT policy is created |
| s1-leaf1 | Greent | VerifyGreenTCounters | Verifies if the GreenT counters are incremented. | - | failure | GreenT counters are not incremented |
| s1-leaf1 | Hardware | VerifyAdverseDrops | Verifies there are no adverse drops on DCS-7280 and DCS-7500 family switches. | - | skipped | VerifyAdverseDrops test is not supported on cEOSLab. |
| s1-leaf1 | Interfaces | VerifyIPProxyARP | Verifies if Proxy ARP is enabled. | - | failure | Interface: Ethernet1 - Not found<br>Interface: Ethernet2 - Proxy-ARP disabled |
| s1-leaf1 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in all port channels. | - | success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | - | success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | - | success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | - | success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceIPv4 | Verifies the interface IPv4 addresses. | - | failure | Interface: Ethernet2 - IP address mismatch - Expected: 172.30.11.1/31 Actual: 10.111.1.1/31<br>Interface: Ethernet2 - Secondary IP address is not configured |
| s1-leaf1 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | - | success | - |
| s1-leaf1 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in all port channels. | - | success | - |
| s1-leaf1 | LANZ | VerifyLANZ | Verifies if LANZ is enabled. | - | skipped | VerifyLANZ test is not supported on cEOSLab. |
| s1-leaf1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | - | failure | Device has reported syslog messages with a severity of ERRORS or higher |
| s1-leaf1 | Logging | VerifyLoggingHostname | Verifies if logs are generated with the device FQDN. | - | failure | Logs are not generated with the device FQDN |
| s1-leaf1 | Logging | VerifyLoggingLogsGeneration | Verifies if logs are generated. | - | success | - |
| s1-leaf1 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | - | success | - |
| s1-leaf1 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | - | success | - |
| s1-leaf1 | PTP | VerifyPtpGMStatus | Verifies that the device is locked to a valid PTP Grandmaster. | - | skipped | VerifyPtpGMStatus test is not supported on cEOSLab. |
| s1-leaf1 | VLAN | VerifyDynamicVlanSource | Verifies dynamic VLAN allocation for specified VLAN sources. | - | failure | Dynamic VLAN source(s) not found in configuration: mlagsync |
| s1-leaf1 | VLAN | VerifyVlanInternalPolicy | Verifies the VLAN internal allocation policy and the range of VLANs. | - | success | - |
| s1-leaf1 | VXLAN | VerifyVxlan1ConnSettings | Verifies the interface vxlan1 source interface and UDP port. | - | skipped | Vxlan1 interface is not configured. |
| s1-leaf1 | VXLAN | VerifyVxlan1Interface | Verifies if the Vxlan1 interface is configured and 'up/up'. | - | skipped | Interface: Vxlan1 - Not configured |
