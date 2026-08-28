# 🛡️ ANTA Security Advisory Report <a id="anta-security-advisory-report"></a>

**Table of Contents:**

- [ANTA Security Advisory Report](#anta-security-advisory-report)
  - [Advisory Exposure Summary](#advisory-exposure-summary)
  - [Security Advisory Details](#security-advisory-details)
  - [Security Advisory Run Overview](#security-advisory-run-overview)

## 📊 Advisory Exposure Summary <a id="advisory-exposure-summary"></a>

| Security Advisory | Severity | Devices | ❌&nbsp;Affected | ❓&nbsp;Inconclusive | ✅&nbsp;Not Affected | ❗&nbsp;Error | ⏭️&nbsp;Skipped |
| :- | :- | :- | :- | :- | :- | :- | :- |
| [SA0120: Example Management API Authentication Bypass](#sa-0120) | 🔴&nbsp;Critical | 8 | 4 | 0 | 2 | 1 | 1 |
| [SA0121: Example EOS Process Denial of Service](#sa-0121) | 🟠&nbsp;High | 8 | 1 | 0 | 5 | 1 | 1 |
| [SA0117: Security Advisory 0117](#sa-0117) | 🟡&nbsp;Medium | 8 | 2 | 0 | 4 | 1 | 1 |

## 🔐 Security Advisory Details <a id="security-advisory-details"></a>

### [SA0120: Example Management API Authentication Bypass](https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120) <a id="sa-0120"></a>

🔴 **Severity:** Critical

An example vulnerability in an enabled management API could allow an unauthenticated remote actor to bypass authentication under specific configurations. This fictional advisory is used only to exercise realistic report rendering.

#### Vulnerabilities

| Vulnerability | Description | Severity |
| :- | :- | :- |
| CVE-2026-12001 | CVE-2026-12001 Authentication bypass in an enabled management API. | Critical |
| GHSA-2345-6789-cfgh | GHSA-2345-6789-cfgh Authorization flaw affecting management API access controls. | High |

#### 🔎 Device Findings

| Device | Test | Result | Messages |
| :- | :- | :- | :- |
| DC1-LEAF1 | VerifySA120 | ❌&nbsp;Affected | Affected API is enabled and reachable from an untrusted network.<br>CVE-2026-12001 vulnerable management API - The device is affected because the vulnerable management API is enabled.<br>External network reachability - The assessment is inconclusive because external reachability could not be verified.<br>GHSA-2345-6789-cfgh authorization controls - The device is not affected by this issue because authorization controls are enabled. |
| DC1-LEAF3 | VerifySA120 | ❌&nbsp;Affected | Affected API is enabled without a control-plane ACL. |
| DC1-SPINE2 | VerifySA120 | ❌&nbsp;Affected | Affected release detected; management API exposure requires remediation. |
| DC2-LEAF2 | VerifySA120 | ❌&nbsp;Affected | Affected API is exposed through the default VRF. |
| DC1-LEAF2 | VerifySA120 | ✅&nbsp;Not Affected | The management API is restricted to the trusted management VRF. |
| DC1-SPINE1 | VerifySA120 | ✅&nbsp;Not Affected | Installed EOS release contains the security fix. |
| DC2-LEAF1 | VerifySA120 | ❗&nbsp;Error | Management API configuration could not be parsed. |
| DC1-LEAF4 | VerifySA120 | ⏭️&nbsp;Skipped | Device was unreachable during test execution. |

### [SA0121: Example EOS Process Denial of Service](https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121) <a id="sa-0121"></a>

🟠 **Severity:** High

An example malformed packet could restart an EOS process when received on an exposed service. This fictional advisory demonstrates a larger fleet with mixed findings and no published mitigation.

#### Vulnerabilities

| Vulnerability | Description | Severity |
| :- | :- | :- |
| GTI-EXAMPLE-12101 | GTI-EXAMPLE-12101 Malformed packet may restart an exposed EOS process. | High |

#### 🔎 Device Findings

| Device | Test | Result | Messages |
| :- | :- | :- | :- |
| DC1-SPINE1 | VerifySA121 | ❌&nbsp;Affected | Affected EOS release and exposed service detected. |
| DC1-LEAF1 | VerifySA121 | ✅&nbsp;Not Affected | The affected service is disabled. |
| DC1-LEAF2 | VerifySA121 | ✅&nbsp;Not Affected | Installed EOS release contains the security fix. |
| DC1-LEAF3 | VerifySA121 | ✅&nbsp;Not Affected | The service is limited to a trusted interface. |
| DC1-SPINE2 | VerifySA121 | ✅&nbsp;Not Affected | Installed EOS release contains the security fix. |
| DC2-LEAF2 | VerifySA121 | ✅&nbsp;Not Affected | The affected service is disabled. |
| DC2-LEAF1 | VerifySA121 | ❗&nbsp;Error | Service state could not be determined. |
| DC1-LEAF4 | VerifySA121 | ⏭️&nbsp;Skipped | Device was unreachable during test execution. |

### [SA0117: Security Advisory 0117](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117) <a id="sa-0117"></a>

🟡 **Severity:** Medium

On affected platforms running Arista EOS with a gNMI transport enabled, running the gNOI File TransferToRemote RPC with credentials for a remote server may cause these remote-server credentials to be logged or accounted on the local EOS device or possibly on other remote accounting servers (i.e. TACACS, RADIUS, etc).

#### Vulnerabilities

| Vulnerability | Description | Severity |
| :- | :- | :- |
| CVE-2025-0936 | CVE-2025-0936 Remote server credentials may be exposed through gNOI File TransferToRemote logging or accounting. | Medium |

#### 🔎 Device Findings

| Device | Test | Result | Messages |
| :- | :- | :- | :- |
| DC1-LEAF1 | VerifySA117 | ❌&nbsp;Affected | EOS 4.32.4M is affected. OpenConfig gNMI has accounting requests enabled. |
| DC1-SPINE2 | VerifySA117 | ❌&nbsp;Affected | EOS 4.31.6M is affected. OpenConfig tracing includes a risky selector. |
| DC1-LEAF2 | VerifySA117 | ✅&nbsp;Not Affected | EOS 4.32.5M is not affected by this advisory. |
| DC1-SPINE1 | VerifySA117 | ✅&nbsp;Not Affected | EOS 4.33.2F is not affected by this advisory. |
| DC2-LEAF1 | VerifySA117 | ✅&nbsp;Not Affected | The device configuration is not affected by this advisory. |
| DC2-LEAF2 | VerifySA117 | ✅&nbsp;Not Affected | EOS 4.30.10M is not affected by this advisory. |
| DC1-LEAF3 | VerifySA117 | ❗&nbsp;Error | The EOS version could not be determined from the available command output. |
| DC1-LEAF4 | VerifySA117 | ⏭️&nbsp;Skipped | Device was unreachable during test execution. |

## 📋 Security Advisory Run Overview <a id="security-advisory-run-overview"></a>

| ⚙️ Run Metric | 📝 Details |
| :- | :- |
| **ANTA Version** | v1.4.0 |
| **Test Execution Start Time** | 2025-05-20 08:30:00.000+00:00 |
| **Test Execution End Time** | 2025-05-20 08:35:30.500+00:00 |
| **Total Duration** | 5 minutes, 30 seconds |
| **Total Devices In Inventory** | 8 |
| **Devices Unreachable At Setup** | s1-spine2 |
| **Devices Filtered At Setup** | s1-leaf1<br>s1-leaf2 |
| **Filters Applied** | Tags: spine |
| **Security Advisories Assessed** | 3 |
| **Devices Assessed** | 8 |
