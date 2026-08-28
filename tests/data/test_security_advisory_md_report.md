# 🛡️ ANTA Security Advisory Report <a id="anta-security-advisory-report"></a>

**Table of Contents:**

- [ANTA Security Advisory Report](#anta-security-advisory-report)
  - [Advisory Exposure Summary](#advisory-exposure-summary)
  - [Security Advisory Details](#security-advisory-details)

## 📊 Advisory Exposure Summary <a id="advisory-exposure-summary"></a>

| Security Advisory | Severity | Devices | ✅&nbsp;Success | ❓&nbsp;Inconclusive | ❌&nbsp;Failure | ❗&nbsp;Error | ⏭️&nbsp;Skipped |
| :- | :- | :- | :- | :- | :- | :- | :- |
| [SA0117: Security Advisory 0117](#sa-0117) | 🟡&nbsp;Medium | 8 | 4 | 0 | 2 | 1 | 1 |
| [SA0120: Example Management API Authentication Bypass](#sa-0120) | 🔴&nbsp;Critical | 8 | 2 | 0 | 4 | 1 | 1 |
| [SA0121: Example EOS Process Denial of Service](#sa-0121) | 🟠&nbsp;High | 8 | 5 | 0 | 1 | 1 | 1 |

## 🔐 Security Advisory Details <a id="security-advisory-details"></a>

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
| DC1-LEAF1 | VerifySA117 | ❌&nbsp;Failure | EOS 4.32.4M is affected. OpenConfig gNMI has accounting requests enabled. |
| DC1-LEAF2 | VerifySA117 | ✅&nbsp;Success | EOS 4.32.5M is not affected by this advisory. |
| DC1-LEAF3 | VerifySA117 | ❗&nbsp;Error | The EOS version could not be determined from the available command output. |
| DC1-LEAF4 | VerifySA117 | ⏭️&nbsp;Skipped | Device was unreachable during test execution. |
| DC1-SPINE1 | VerifySA117 | ✅&nbsp;Success | EOS 4.33.2F is not affected by this advisory. |
| DC1-SPINE2 | VerifySA117 | ❌&nbsp;Failure | EOS 4.31.6M is affected. OpenConfig tracing includes a risky selector. |
| DC2-LEAF1 | VerifySA117 | ✅&nbsp;Success | The device configuration is not affected by this advisory. |
| DC2-LEAF2 | VerifySA117 | ✅&nbsp;Success | EOS 4.30.10M is not affected by this advisory. |

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
| DC1-LEAF1 | VerifySA120 | ❌&nbsp;Failure | Affected API is enabled and reachable from an untrusted network. |
| DC1-LEAF2 | VerifySA120 | ✅&nbsp;Success | The management API is restricted to the trusted management VRF. |
| DC1-LEAF3 | VerifySA120 | ❌&nbsp;Failure | Affected API is enabled without a control-plane ACL. |
| DC1-LEAF4 | VerifySA120 | ⏭️&nbsp;Skipped | Device was unreachable during test execution. |
| DC1-SPINE1 | VerifySA120 | ✅&nbsp;Success | Installed EOS release contains the security fix. |
| DC1-SPINE2 | VerifySA120 | ❌&nbsp;Failure | Affected release detected; management API exposure requires remediation. |
| DC2-LEAF1 | VerifySA120 | ❗&nbsp;Error | Management API configuration could not be parsed. |
| DC2-LEAF2 | VerifySA120 | ❌&nbsp;Failure | Affected API is exposed through the default VRF. |

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
| DC1-LEAF1 | VerifySA121 | ✅&nbsp;Success | The affected service is disabled. |
| DC1-LEAF2 | VerifySA121 | ✅&nbsp;Success | Installed EOS release contains the security fix. |
| DC1-LEAF3 | VerifySA121 | ✅&nbsp;Success | The service is limited to a trusted interface. |
| DC1-LEAF4 | VerifySA121 | ⏭️&nbsp;Skipped | Device was unreachable during test execution. |
| DC1-SPINE1 | VerifySA121 | ❌&nbsp;Failure | Affected EOS release and exposed service detected. |
| DC1-SPINE2 | VerifySA121 | ✅&nbsp;Success | Installed EOS release contains the security fix. |
| DC2-LEAF1 | VerifySA121 | ❗&nbsp;Error | Service state could not be determined. |
| DC2-LEAF2 | VerifySA121 | ✅&nbsp;Success | The affected service is disabled. |
