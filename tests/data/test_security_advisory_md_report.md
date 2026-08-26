# 🛡️ ANTA Security Advisory Report <a id="anta-security-advisory-report"></a>

**Table of Contents:**

- [ANTA Security Advisory Report](#anta-security-advisory-report)
  - [Run Overview](#run-overview)
  - [Advisory Exposure Summary](#advisory-exposure-summary)
  - [Security Advisory Details](#security-advisory-details)

## 📋 Run Overview <a id="run-overview"></a>

| ⚙️ Run Metric | 📝 Details |
| :- | :- |
| **ANTA Version** | 2.0.0 |
| **Test Execution Start Time** | 2026-08-26 14:30:00.000+00:00 |
| **Test Execution End Time** | 2026-08-26 14:31:12.450+00:00 |
| **Total Duration** | 1 minute, 12 seconds |
| **Total Devices In Inventory** | 8 |
| **Devices Unreachable At Setup** | DC1-LEAF4 |
| **Devices Filtered At Setup** | None |
| **Filters Applied** | Tags: fabric, security-advisory<br>Tests: VerifySA117, VerifySA120, VerifySA121 |

## 📊 Advisory Exposure Summary <a id="advisory-exposure-summary"></a>

| Security Advisory | Severity | Devices | ✅ Success | ❌ Failure | ❗ Error | ⏭️ Skipped |
| :- | :- | :- | :- | :- | :- | :- |
| [SA0117: Security Advisory 0117](#sa-0117) | 🟡&nbsp;Medium | 8 | 4 | 2 | 1 | 1 |
| [SA0120: Example Management API Authentication Bypass](#sa-0120) | 🔴&nbsp;Critical | 8 | 2 | 4 | 1 | 1 |
| [SA0121: Example EOS Process Denial of Service](#sa-0121) | 🟠&nbsp;High | 8 | 5 | 1 | 1 | 1 |

## 🔐 Security Advisory Details <a id="security-advisory-details"></a>

### [SA0117: Security Advisory 0117](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117) <a id="sa-0117"></a>

🟡 **Severity:** Medium

On affected platforms running Arista EOS with a gNMI transport enabled, running the gNOI File TransferToRemote RPC with credentials for a remote server may cause these remote-server credentials to be logged or accounted on the local EOS device or possibly on other remote accounting servers (i.e. TACACS, RADIUS, etc).

#### CVEs

| CVE | Severity | CVSS Version | Base Score | Vector |
| :- | :- | :- | :- | :- |
| CVE-2025-0936 | Medium | 3.1 | 6.5 | `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:H/A:N` |

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

#### 🛠️ Mitigations

- **Disable accounting and logging:** Disable accounting requests for enabled OpenConfig transports and disable OpenConfig tracing. ([Reference](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117))
- **Disable the gNOI File service:** Set OCGNOIFileToggle to 0 and restart the OpenConfig agent. ([Reference](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117))
- **Block TransferToRemote using gNSI Authz:** Use gNSI Authz to deny the /gnoi.file.File/TransferToRemote RPC on EOS 4.31.0F and later. ([Reference](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117))

#### ✅ Resolutions

- **Upgrade to a remediated EOS release:** Upgrade to 4.30.10M or later in the 4.30.x train, 4.31.7M or later in the 4.31.x train, 4.32.5M or later in the 4.32.x train, or 4.33.2F or later. ([Reference](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117))

### [SA0120: Example Management API Authentication Bypass](https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120) <a id="sa-0120"></a>

🔴 **Severity:** Critical

An example vulnerability in an enabled management API could allow an unauthenticated remote actor to bypass authentication under specific configurations. This fictional advisory is used only to exercise realistic report rendering.

#### CVEs

| CVE | Severity | CVSS Version | Base Score | Vector |
| :- | :- | :- | :- | :- |
| CVE-2026-12001 | Critical | 3.1 | 9.8 | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| CVE-2026-12001 | Critical | 4.0 | 9.3 | `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H` |
| CVE-2026-12002 | High | 3.1 | 8.1 | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H` |

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

#### 🛠️ Mitigations

- **Restrict management-plane access:** Apply control-plane ACLs so the affected API is reachable only from trusted management subnets.

#### ✅ Resolutions

- **Upgrade EOS:** Upgrade every affected device to a fixed EOS release from the recommended release train. ([Reference](https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120))
- **Rotate management credentials:** Rotate credentials after upgrading if the vulnerable API was reachable from an untrusted network.

### [SA0121: Example EOS Process Denial of Service](https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121) <a id="sa-0121"></a>

🟠 **Severity:** High

An example malformed packet could restart an EOS process when received on an exposed service. This fictional advisory demonstrates a larger fleet with mixed findings and no published mitigation.

#### CVEs

| CVE | Severity | CVSS Version | Base Score | Vector |
| :- | :- | :- | :- | :- |
| CVE-2026-12101 | High | 3.1 | 7.5 | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H` |

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

#### 🛠️ Mitigations

*No mitigations are published for this advisory.*

#### ✅ Resolutions

- **Install a fixed release:** Upgrade to a fixed EOS release and verify process stability after the maintenance window. ([Reference](https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121))
