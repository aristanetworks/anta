<h1 id="anta-security-advisory-report" align="center">🛡️ ANTA Security Advisory Report 🛡️</h1>

**Table of Contents:**

- [Advisory Assessment Summary](#advisory-assessment-summary)
- [Security Advisory Details](#security-advisory-details)
  - [Example Management API Authentication Bypass](#sa-0120)
  - [Example EOS Process Denial of Service](#sa-0121)
  - [Security Advisory 0117](#sa-0117)
- [Run Overview](#run-overview)

## 📊 Advisory Assessment Summary <a id="advisory-assessment-summary"></a>

| Security Advisory | Severity | Devices | 🛑&nbsp;Affected | ❓&nbsp;Inconclusive | ✅&nbsp;Mitigated | ✅&nbsp;Not Affected | ❗&nbsp;Error | ⏭️&nbsp;Skipped |
| :- | :- | :- | :- | :- | :- | :- | :- | :- |
| [Example Management API Authentication Bypass](#sa-0120) | 🔴&nbsp;Critical | 8 | 4 | 0 | 0 | 2 | 1 | 1 |
| [Example EOS Process Denial of Service](#sa-0121) | 🟠&nbsp;High | 8 | 1 | 0 | 0 | 5 | 1 | 1 |
| [Security Advisory 0117](#sa-0117) | 🟡&nbsp;Medium | 8 | 0 | 2 | 0 | 4 | 1 | 1 |

## 🔐 Security Advisory Details <a id="security-advisory-details"></a>

### Example Management API Authentication Bypass <a id="sa-0120"></a>

> **Severity:** 🔴 Critical\
> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120>
>
> An example vulnerability in an enabled management API could allow an unauthenticated remote actor to bypass authentication under specific configurations. This fictional advisory is used only to exercise realistic report rendering.
>
> | Vulnerability | Severity | Description |
> | :- | :- | :- |
> | CVE-2026-12001 | 🔴&nbsp;Critical | Authentication bypass in an enabled management API. |
> | GHSA-2345-6789-cfgh | 🟠&nbsp;High | Authorization flaw affecting management API access controls. |
>

#### 🔎 Device Findings

| Device | Description | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- | :- |
| DC1-LEAF1 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | 🛑&nbsp;Affected | **Detailed findings:** 1/3&nbsp;checks&nbsp;affected; 1/3&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** Affected API is enabled and reachable from an untrusted network.<br>Vulnerable management API - The device is affected because the vulnerable management API is enabled.<br>External network reachability - The assessment is inconclusive because external reachability could not be verified.<br>Authorization controls - The device is not affected by this issue because authorization controls are enabled. | - |
| | &nbsp;&nbsp;├──&nbsp;Authentication bypass in an enabled management API. | 🔴&nbsp;CVE-2026-12001 | 🛑&nbsp;Affected | The device is affected because the vulnerable management API is enabled. | - |
| | &nbsp;&nbsp;├──&nbsp;External network reachability | - | ❓&nbsp;Inconclusive | The assessment is inconclusive because external reachability could not be verified. | - |
| | &nbsp;&nbsp;└──&nbsp;Authorization flaw affecting management API access controls. | 🟠&nbsp;GHSA-2345-6789-cfgh | ✅&nbsp;Not Affected | The device is not affected by this issue because authorization controls are enabled. | - |
| DC1-LEAF3 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | 🛑&nbsp;Affected | Affected API is enabled without a control-plane ACL. | - |
| DC1-SPINE2 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | 🛑&nbsp;Affected | Affected release detected; management API exposure requires remediation. | - |
| DC2-LEAF2 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | 🛑&nbsp;Affected | Affected API is exposed through the default VRF. | - |
| DC1-LEAF2 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | ✅&nbsp;Not Affected | The management API is restricted to the trusted management VRF. | - |
| DC1-SPINE1 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | ✅&nbsp;Not Affected | Installed EOS release contains the security fix. | - |
| DC2-LEAF1 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | ❗&nbsp;Error | Management API configuration could not be parsed. | - |
| DC1-LEAF4 | Verify that the device is not exposed to Arista Security Advisory 0120. | - | ⏭️&nbsp;Skipped | Device was unreachable during test execution. | - |

### Example EOS Process Denial of Service <a id="sa-0121"></a>

> **Severity:** 🟠 High\
> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121>
>
> An example malformed packet could restart an EOS process when received on an exposed service. This fictional advisory demonstrates a larger fleet with mixed findings and no published mitigation.
>
> | Vulnerability | Severity | Description |
> | :- | :- | :- |
> | GTI-EXAMPLE-12101 | 🟠&nbsp;High | Malformed packet may restart an exposed EOS process. |
> | CVE-2026-12102 | 🔵&nbsp;Low | Low-impact information disclosure in process diagnostics. |
> | CVE-2026-12103 | ⚪&nbsp;Unknown | Process behavior with severity pending assessment. |
>

#### 🔎 Device Findings

| Device | Description | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- | :- |
| DC1-SPINE1 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | 🛑&nbsp;Affected | **Detailed findings:** 1/3&nbsp;checks&nbsp;affected; 1/3&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** Affected EOS release and exposed service detected.<br>Malformed packet may restart an exposed EOS process. - The device is affected because an affected EOS release and exposed service were detected.<br>Low-impact information disclosure in process diagnostics. - The device is not affected by the low-severity issue because process diagnostics are restricted.<br>Process behavior with severity pending assessment. - The assessment is inconclusive because the severity and affected conditions are still being investigated. | •&nbsp;GTI-EXAMPLE-12101: Disable or restrict the exposed service and upgrade to a fixed EOS release.<br>•&nbsp;CVE-2026-12103: Monitor the advisory for updated severity and remediation guidance.<br>•&nbsp;CVE-2026-12102: Keep process diagnostics restricted to trusted operators. |
| | &nbsp;&nbsp;├──&nbsp;Malformed packet may restart an exposed EOS process. | 🟠&nbsp;GTI-EXAMPLE-12101 | 🛑&nbsp;Affected | The device is affected because an affected EOS release and exposed service were detected. | Disable or restrict the exposed service and upgrade to a fixed EOS release. |
| | &nbsp;&nbsp;├──&nbsp;Process behavior with severity pending assessment. | ⚪&nbsp;CVE-2026-12103 | ❓&nbsp;Inconclusive | The assessment is inconclusive because the severity and affected conditions are still being investigated. | Monitor the advisory for updated severity and remediation guidance. |
| | &nbsp;&nbsp;└──&nbsp;Low-impact information disclosure in process diagnostics. | 🔵&nbsp;CVE-2026-12102 | ✅&nbsp;Not Affected | The device is not affected by the low-severity issue because process diagnostics are restricted. | Keep process diagnostics restricted to trusted operators. |
| DC1-LEAF1 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ✅&nbsp;Not Affected | The affected service is disabled. | - |
| DC1-LEAF2 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ✅&nbsp;Not Affected | Installed EOS release contains the security fix. | - |
| DC1-LEAF3 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ✅&nbsp;Not Affected | The service is limited to a trusted interface. | - |
| DC1-SPINE2 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ✅&nbsp;Not Affected | Installed EOS release contains the security fix. | - |
| DC2-LEAF2 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ✅&nbsp;Not Affected | The affected service is disabled. | - |
| DC2-LEAF1 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ❗&nbsp;Error | Service state could not be determined. | - |
| DC1-LEAF4 | Verify that the device is not exposed to Arista Security Advisory 0121. | - | ⏭️&nbsp;Skipped | Device was unreachable during test execution. | - |

### Security Advisory 0117 <a id="sa-0117"></a>

> **Severity:** 🟡 Medium\
> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117>
>
> On affected platforms running Arista EOS with a gNMI transport enabled, running the gNOI File TransferToRemote RPC with credentials for a remote server may cause these remote-server credentials to be logged or accounted on the local EOS device or possibly on other remote accounting servers (i.e. TACACS, RADIUS, etc).
>
> | Vulnerability | Severity | Description |
> | :- | :- | :- |
> | CVE-2025-0936 | 🟡&nbsp;Medium | gNOI TransferToRemote credential exposure through OpenConfig accounting or tracing. |
>

#### 🔎 Device Findings

| Device | Description | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- | :- |
| DC1-LEAF1 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ❓&nbsp;Inconclusive | **Detailed findings:** 1/1&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** The assessment is inconclusive and the device may be affected because EOS version '4.32.4M' has an enabled gNMI transport with accounting enabled, but the gNOI File and effective gNSI Authz controls cannot be determined.<br>gNOI TransferToRemote credential exposure through OpenConfig accounting or tracing. - The assessment is inconclusive because required gNOI File and gNSI Authz evidence is unavailable. | •&nbsp;CVE-2025-0936: Upgrade to a fixed EOS release when one is published, then rerun the test. |
| | &nbsp;&nbsp;└──&nbsp;gNOI TransferToRemote credential exposure through OpenConfig accounting or tracing. | 🟡&nbsp;CVE-2025-0936 | ❓&nbsp;Inconclusive | The assessment is inconclusive because required gNOI File and gNSI Authz evidence is unavailable. | Upgrade to a fixed EOS release when one is published, then rerun the test. |
| DC1-SPINE2 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ❓&nbsp;Inconclusive | The assessment is inconclusive and the device may be affected because EOS version '4.31.6M' has an enabled gNMI transport and OpenConfig tracing includes a selector identified by the advisory, but the gNOI File and effective gNSI Authz controls cannot be determined. | Upgrade to a fixed EOS release when one is published, then rerun the test. |
| DC1-LEAF2 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ✅&nbsp;Not Affected | EOS 4.32.5M is not affected by this advisory. | - |
| DC1-SPINE1 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ✅&nbsp;Not Affected | EOS 4.33.2F is not affected by this advisory. | - |
| DC2-LEAF1 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ✅&nbsp;Not Affected | The device configuration is not affected by this advisory. | - |
| DC2-LEAF2 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ✅&nbsp;Not Affected | EOS 4.30.10M is not affected by this advisory. | - |
| DC1-LEAF3 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ❗&nbsp;Error | The EOS version could not be determined from the available command output. | Collect valid EOS version evidence and rerun the test. |
| DC1-LEAF4 | Verify that the device is not exposed to Arista Security Advisory 0117. | - | ⏭️&nbsp;Skipped | Device was unreachable during test execution. | Restore device reachability and rerun the test. |

## 📋 Run Overview <a id="run-overview"></a>

| | |
| :- | :- |
| **ANTA Version** | v1.4.0 |
| **Duration** | 5 minutes, 30 seconds (2025-05-20 08:30:00.000+00:00 → 2025-05-20 08:35:30.500+00:00) |
| **Security Advisories Tested** | 3 |
| **Total Devices In Inventory** | 8 |
| **Devices Assessed** | 8 |
| **Devices Unreachable At Setup** | s1-spine2 |
| **Devices Filtered At Setup** | s1-leaf1<br>s1-leaf2 |
| **Filters Applied** | Tags: spine |
