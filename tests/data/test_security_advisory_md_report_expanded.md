<h1 id="anta-security-advisory-report" align="center">🛡️ ANTA Security Advisory Report 🛡️</h1>

**Table of Contents:**

- [Advisory Assessment Summary](#advisory-assessment-summary)
- [Security Advisory Details](#security-advisory-details)
  - [Security Advisory 0147](#sa-0147)
  - [Security Advisory 0146](#sa-0146)
  - [Security Advisory 0117](#sa-0117)
  - [Reporter Rendering Coverage Advisory](#sa-9999)
- [Run Overview](#run-overview)

## 📊 Advisory Assessment Summary <a id="advisory-assessment-summary"></a>

| Security Advisory | Severity | Devices | 🛑&nbsp;Affected | ❓&nbsp;Inconclusive | ✅&nbsp;Mitigated | ✅&nbsp;Not Affected | ❗&nbsp;Error | ⏭️&nbsp;Skipped |
| :- | :- | :- | :- | :- | :- | :- | :- | :- |
| [Security Advisory 0147](#sa-0147) | 🔴&nbsp;Critical | 8 | 4 | 0 | 0 | 2 | 1 | 1 |
| [Security Advisory 0146](#sa-0146) | 🟠&nbsp;High | 8 | 1 | 0 | 0 | 5 | 1 | 1 |
| [Security Advisory 0117](#sa-0117) | 🟡&nbsp;Medium | 8 | 0 | 2 | 0 | 4 | 1 | 1 |
| [Reporter Rendering Coverage Advisory](#sa-9999) | 🔵&nbsp;Low | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

## 🔐 Security Advisory Details <a id="security-advisory-details"></a>

### Security Advisory 0147 <a id="sa-0147"></a>

> **Severity:** 🔴 Critical\
> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/24515-security-advisory-0147>
>
> Multiple vulnerabilities have been discovered in OpenSSH before version 10.4, which is shipped with multiple Arista products. One vulnerability (CVE-2026-60001) affects the server-side SSH daemon (sshd). The remaining three vulnerabilities (CVE-2026-60002, CVE-2026-59995, CVE-2026-59996) affect the client-side SSH, Secure File Transfer Protocol (SFTP), and Secure Copy Protocol (SCP) utilities, respectively.
>
> | Vulnerability | Severity | Description |
> | :- | :- | :- |
> | CVE-2026-60002 | 🔴&nbsp;Critical | SSH client issue when connecting to a malicious or compromised server. |
> | CVE-2026-59995 | 🟡&nbsp;Medium | SFTP client issue when connecting to an untrusted server. |
> | CVE-2026-59996 | 🟡&nbsp;Medium | SCP remote-to-remote client issue involving an untrusted server. |
> | CVE-2026-60001 | 🟡&nbsp;Medium | OpenSSH server issue affecting accepted SSH connections. |
>

#### 🔎 Device Findings

| Device | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- |
| DC1-LEAF1 | - | 🛑&nbsp;Affected | **Detailed findings:** 1/4&nbsp;checks&nbsp;affected; 3/4&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections.<br>CVE-2026-59995: The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected, but operator-initiated SFTP use with an untrusted server cannot be determined.<br>CVE-2026-59996: The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected, but operator-initiated SCP remote-to-remote use with an untrusted server cannot be determined.<br>CVE-2026-60001: The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections.<br>CVE-2026-60002: The device is affected but mitigated because openssh-clients '9.9p1' uses strict host-key checking. | - |
| &nbsp;&nbsp;├── | 🟡&nbsp;CVE-2026-60001 | 🛑&nbsp;Affected | The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections. | - |
| &nbsp;&nbsp;├── | 🟡&nbsp;CVE-2026-59995 | ❓&nbsp;Inconclusive | The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected, but operator-initiated SFTP use with an untrusted server cannot be determined. | - |
| &nbsp;&nbsp;├── | 🟡&nbsp;CVE-2026-59996 | ❓&nbsp;Inconclusive | The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected, but operator-initiated SCP remote-to-remote use with an untrusted server cannot be determined. | - |
| &nbsp;&nbsp;└── | 🔴&nbsp;CVE-2026-60002 | ❓&nbsp;Inconclusive | The device is affected but mitigated because openssh-clients '9.9p1' uses strict host-key checking. | - |
| DC1-LEAF3 | - | 🛑&nbsp;Affected | The device is affected because openssh-server '9.8p1' is affected and SSH accepts connections. | - |
| DC1-SPINE2 | - | 🛑&nbsp;Affected | The device is affected because openssh-server '9.9p2' is affected and SSH accepts connections. | - |
| DC2-LEAF2 | - | 🛑&nbsp;Affected | The device is affected because openssh-server '9.7p1' is affected and SSH accepts connections. | - |
| DC1-LEAF2 | - | ✅&nbsp;Not Affected | The device is not affected because its EOS version is outside the published affected range. | - |
| DC1-SPINE1 | - | ✅&nbsp;Not Affected | The device is not affected because openssh-clients and openssh-server '10.4p1' are fixed. | - |
| DC2-LEAF1 | - | ❗&nbsp;Error | The openssh-clients package version could not be determined from 'show version detail'. | - |
| DC1-LEAF4 | - | ⏭️&nbsp;Skipped | Device was unreachable during test execution. | - |

### Security Advisory 0146 <a id="sa-0146"></a>

> **Severity:** 🟠 High\
> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/24500-security-advisory-0146>
>
> Arista Networks is providing this security update in response to the gRPC-Go security vulnerabilities published as GHSA-hrxh-6v49-42gf. Arista products are affected solely by the HTTP/2 Rapid Reset denial-of-service bypass, in which an unauthenticated remote attacker can exploit unthrottled HTTP/2 stream resets to bypass rate-limiting controls, consume excessive CPU resources, and cause a denial of service.
>
> | Vulnerability | Severity | Description |
> | :- | :- | :- |
> | GHSA-hrxh-6v49-42gf | 🟠&nbsp;High | HTTP/2 Rapid Reset denial-of-service rate-limit bypass in affected gRPC servers. |
>

#### 🔎 Device Findings

| Device | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- |
| DC1-SPINE1 | - | 🛑&nbsp;Affected | **Detailed findings:** 1/1&nbsp;checks&nbsp;affected<br>**Overall evidence:** The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI.<br>GHSA-hrxh-6v49-42gf: The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI. | •&nbsp;GHSA-hrxh-6v49-42gf: Upgrade to EOS 4.36.2F or later in the 4.36 train or EOS 4.35.6M or later in the 4.35 train.<br>Refer to the advisory for newly fixed releases and current mitigation guidance. |
| &nbsp;&nbsp;└── | 🟠&nbsp;GHSA-hrxh-6v49-42gf | 🛑&nbsp;Affected | The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI. | Upgrade to EOS 4.36.2F or later in the 4.36 train or EOS 4.35.6M or later in the 4.35 train.<br>Refer to the advisory for newly fixed releases and current mitigation guidance. |
| DC1-LEAF1 | - | ✅&nbsp;Not Affected | The device is not affected because no enabled gRPC server is on an affected software version. | - |
| DC1-LEAF2 | - | ✅&nbsp;Not Affected | The device is not affected because no enabled gRPC server is on an affected software version. | - |
| DC1-LEAF3 | - | ✅&nbsp;Not Affected | The device is not affected because no enabled gRPC server is on an affected software version. | - |
| DC1-SPINE2 | - | ✅&nbsp;Not Affected | The device is not affected because no enabled gRPC server is on an affected software version. | - |
| DC2-LEAF2 | - | ✅&nbsp;Not Affected | The device is not affected because no enabled gRPC server is on an affected software version. | - |
| DC2-LEAF1 | - | ❗&nbsp;Error | The following required evidence is unavailable or invalid: gRIBI enabled state. | - |
| DC1-LEAF4 | - | ⏭️&nbsp;Skipped | Device was unreachable during test execution. | - |

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

| Device | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- |
| DC1-LEAF1 | - | ❓&nbsp;Inconclusive | **Detailed findings:** 1/1&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** The assessment is inconclusive and the device may be affected because EOS version '4.32.4M' has an enabled gNMI transport with accounting enabled, but the gNOI File and effective gNSI Authz controls cannot be determined.<br>CVE-2025-0936: The assessment is inconclusive because required gNOI File and gNSI Authz evidence is unavailable. | •&nbsp;CVE-2025-0936: Upgrade to EOS 4.32.5M or later in the 4.32 train or EOS 4.33.2F or later in the 4.33 train.<br>Refer to the advisory to determine whether the unresolved condition applies, for newly fixed releases, and for current mitigation guidance. |
| &nbsp;&nbsp;└── | 🟡&nbsp;CVE-2025-0936 | ❓&nbsp;Inconclusive | The assessment is inconclusive because required gNOI File and gNSI Authz evidence is unavailable. | Upgrade to EOS 4.32.5M or later in the 4.32 train or EOS 4.33.2F or later in the 4.33 train.<br>Refer to the advisory to determine whether the unresolved condition applies, for newly fixed releases, and for current mitigation guidance. |
| DC1-SPINE2 | - | ❓&nbsp;Inconclusive | **Detailed findings:** 1/1&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** The assessment is inconclusive and the device may be affected because EOS version '4.31.6M' has an enabled gNMI transport and OpenConfig tracing includes a selector identified by the advisory, but the gNOI File and effective gNSI Authz controls cannot be determined. | •&nbsp;Upgrade to EOS 4.32.5M or later in the 4.32 train or EOS 4.33.2F or later in the 4.33 train.<br>Refer to the advisory to determine whether the unresolved condition applies, for newly fixed releases, and for current mitigation guidance. |
| &nbsp;&nbsp;└── | - | ❓&nbsp;Inconclusive | - | Upgrade to EOS 4.32.5M or later in the 4.32 train or EOS 4.33.2F or later in the 4.33 train.<br>Refer to the advisory to determine whether the unresolved condition applies, for newly fixed releases, and for current mitigation guidance. |
| DC1-LEAF2 | - | ✅&nbsp;Not Affected | EOS 4.32.5M is not affected by this advisory. | - |
| DC1-SPINE1 | - | ✅&nbsp;Not Affected | EOS 4.33.2F is not affected by this advisory. | - |
| DC2-LEAF1 | - | ✅&nbsp;Not Affected | The device configuration is not affected by this advisory. | - |
| DC2-LEAF2 | - | ✅&nbsp;Not Affected | EOS 4.30.10M is not affected by this advisory. | - |
| DC1-LEAF3 | - | ❗&nbsp;Error | **Detailed findings:** 1/1&nbsp;checks&nbsp;errored<br>**Overall evidence:** The EOS version could not be determined from the available command output. | •&nbsp;Collect or correct valid refreshed device EOS version metadata and rerun the test. |
| &nbsp;&nbsp;└── | - | ❗&nbsp;Error | - | Collect or correct valid refreshed device EOS version metadata and rerun the test. |
| DC1-LEAF4 | - | ⏭️&nbsp;Skipped | **Detailed findings:** 1/1&nbsp;checks&nbsp;skipped<br>**Overall evidence:** Device was unreachable during test execution. | •&nbsp;Restore device reachability and rerun the test. |
| &nbsp;&nbsp;└── | - | ⏭️&nbsp;Skipped | - | Restore device reachability and rerun the test. |

### Reporter Rendering Coverage Advisory <a id="sa-9999"></a>

> **Severity:** 🔵 Low\
> **URL:** <https://example.com/security-advisory-rendering-coverage>
>
> This fictional advisory exists only to exercise low and unknown severity report rendering, which published ANTA advisory tests do not currently use.
>
> | Vulnerability | Severity | Description |
> | :- | :- | :- |
> | TEST-LOW-SEVERITY | 🔵&nbsp;Low | Synthetic low-severity vulnerability used to verify report rendering. |
> | TEST-UNKNOWN-SEVERITY | ⚪&nbsp;Unknown | Synthetic unknown-severity vulnerability used to verify report rendering. |
>

#### 🔎 Device Findings

| Device | Vulnerability ID(s) | Result | Findings | Remediations |
| :- | :- | :- | :- | :- |
| DC1-LEAF1 | - | ❓&nbsp;Inconclusive | **Detailed findings:** 1/2&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** Synthetic result used only to verify low and unknown severity report rendering.<br>TEST-LOW-SEVERITY: Synthetic low-severity rendering check passed.<br>TEST-UNKNOWN-SEVERITY: Synthetic unknown-severity rendering check is inconclusive. | - |
| &nbsp;&nbsp;├── | ⚪&nbsp;TEST-UNKNOWN-SEVERITY | ❓&nbsp;Inconclusive | Synthetic unknown-severity rendering check is inconclusive. | - |
| &nbsp;&nbsp;└── | 🔵&nbsp;TEST-LOW-SEVERITY | ✅&nbsp;Not Affected | Synthetic low-severity rendering check passed. | - |

## 📋 Run Overview <a id="run-overview"></a>

| | |
| :- | :- |
| **ANTA Version** | v1.4.0 |
| **Duration** | 5 minutes, 30 seconds (2025-05-20 08:30:00.000+00:00 → 2025-05-20 08:35:30.500+00:00) |
| **Security Advisories Tested** | 4 |
| **Total Devices In Inventory** | 8 |
| **Devices Assessed** | 8 |
| **Devices Unreachable At Setup** | s1-spine2 |
| **Devices Filtered At Setup** | s1-leaf1<br>s1-leaf2 |
| **Filters Applied** | Tags: spine |
