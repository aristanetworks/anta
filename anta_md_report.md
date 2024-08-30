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
| 84 | 0 | 0 | 84 | 0 |

### Summary Totals Device Under Test

| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |
| ------------------| ----------- | ------------- | ------------- | ------------- | ----------- | -------------------| ------------------|
| DC1-SPINE1 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC1-SPINE2 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC1-LEAF1A | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC1-LEAF1B | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC1-BL1 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC1-BL2 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC2-SPINE1 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC2-SPINE2 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC2-LEAF1A | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC2-LEAF1B | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC2-BL1 | 7 | 0 | 0 | 7 | 0 | - | AAA |
| DC2-BL2 | 7 | 0 | 0 | 7 | 0 | - | AAA |

### Summary Totals Per Category

| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |
| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |
| AAA | 84 | 0 | 0 | 84 | 0 |

## Test Results

| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |
| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |
| DC1-BL1 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-BL1 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-BL1 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC1-BL1 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC1-BL1 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC1-BL1 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC1-BL1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-BL2 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-BL2 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-BL2 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC1-BL2 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC1-BL2 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC1-BL2 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC1-BL2 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-LEAF1A | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-LEAF1A | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-LEAF1A | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC1-LEAF1A | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC1-LEAF1A | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC1-LEAF1A | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC1-LEAF1A | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-LEAF1B | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-LEAF1B | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-LEAF1B | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC1-LEAF1B | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC1-LEAF1B | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC1-LEAF1B | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC1-LEAF1B | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-SPINE1 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-SPINE1 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-SPINE1 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC1-SPINE1 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC1-SPINE1 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC1-SPINE1 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC1-SPINE1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC1-SPINE2 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-SPINE2 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC1-SPINE2 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC1-SPINE2 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC1-SPINE2 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC1-SPINE2 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC1-SPINE2 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC2-BL1 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-BL1 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-BL1 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC2-BL1 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC2-BL1 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC2-BL1 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC2-BL1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC2-BL2 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-BL2 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-BL2 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC2-BL2 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC2-BL2 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC2-BL2 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC2-BL2 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC2-LEAF1A | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-LEAF1A | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-LEAF1A | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC2-LEAF1A | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC2-LEAF1A | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC2-LEAF1A | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC2-LEAF1A | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC2-LEAF1B | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-LEAF1B | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-LEAF1B | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC2-LEAF1B | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC2-LEAF1B | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC2-LEAF1B | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC2-LEAF1B | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC2-SPINE1 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-SPINE1 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-SPINE1 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC2-SPINE1 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC2-SPINE1 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC2-SPINE1 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC2-SPINE1 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
| DC2-SPINE2 | AAA | VerifyAcctConsoleMethods | Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA console accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-SPINE2 | AAA | VerifyAcctDefaultMethods | Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x). | - | failure | AAA default accounting is not configured for ['commands', 'exec', 'system', 'dot1x'] |
| DC2-SPINE2 | AAA | VerifyAuthenMethods | Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x). | - | failure | AAA authentication methods are not configured for login console |
| DC2-SPINE2 | AAA | VerifyAuthzMethods | Verifies the AAA authorization method lists for different authorization types (commands, exec). | - | failure | AAA authorization methods ['local', 'none', 'logging'] are not matching for ['commands', 'exec'] |
| DC2-SPINE2 | AAA | VerifyTacacsServerGroups | Verifies if the provided TACACS server group(s) are configured. | - | failure | No TACACS server group(s) are configured |
| DC2-SPINE2 | AAA | VerifyTacacsServers | Verifies TACACS servers are configured for a specified VRF. | - | failure | No TACACS servers are configured |
| DC2-SPINE2 | AAA | VerifyTacacsSourceIntf | Verifies TACACS source-interface for a specified VRF. | - | failure | Source-interface Management0 is not configured in VRF default |
