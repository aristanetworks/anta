# 🛡️ ANTA Security Advisory Report <a id="anta-security-advisory-report"></a>

**Table of Contents:**

- [ANTA Security Advisory Report](#anta-security-advisory-report)
  - [Advisory Exposure Summary](#advisory-exposure-summary)
  - [Security Advisory Details](#security-advisory-details)

## 📊 Advisory Exposure Summary <a id="advisory-exposure-summary"></a>

| Security Advisory | Severity | Devices | ✅&nbsp;Success | ❓&nbsp;Inconclusive | ❌&nbsp;Failure | ❗&nbsp;Error | ⏭️&nbsp;Skipped |
| :- | :- | :- | :- | :- | :- | :- | :- |
| [SA0001: Test advisory](#sa-0001) | 🟠&nbsp;High | 1 | 0 | 0 | 1 | 0 | 0 |

## 🔐 Security Advisory Details <a id="security-advisory-details"></a>

### [SA0001: Test advisory](https://example.com/advisory) <a id="sa-0001"></a>

🟠 **Severity:** High

Test advisory description.

#### CVEs

| CVE | Severity |
| :- | :- |
| CVE-2026-0001 | Medium |
| CVE-2026-0002 | High |

#### 🔎 Device Findings

| Device | Test | Description | CVE(s) | Result | Messages |
| :- | :- | :- | :- | :- | :- |
| leaf1 | VerifySA1 | Test advisory (CVE-2026-0001, CVE-2026-0002): Verify exposure to the issues described at https://example.com/advisory. | - | ❌&nbsp;Failure | **Detailed findings:** 1/3&nbsp;checks&nbsp;failed; 1/3&nbsp;checks&nbsp;inconclusive<br>**Overall evidence:** CVE-2026-0001 vulnerable service - The device is affected because EOS 4.31.1F enables the vulnerable service.<br>CVE-2026-0001 and CVE-2026-0002 platform applicability - The device is not affected because platform DCS-7050SX3 is outside the affected family.<br>External trust condition - The assessment is inconclusive and the device may be affected because external trust configuration could not be verified. |
| | | &nbsp;&nbsp;├──&nbsp;CVE-2026-0001 vulnerable service | CVE-2026-0001 | ❌&nbsp;Failure | The device is affected because EOS 4.31.1F enables the vulnerable service. |
| | | &nbsp;&nbsp;├──&nbsp;CVE-2026-0001 and CVE-2026-0002 platform applicability | CVE-2026-0001, CVE-2026-0002 | ✅&nbsp;Success | The device is not affected because platform DCS-7050SX3 is outside the affected family. |
| | | &nbsp;&nbsp;└──&nbsp;External trust condition | - | ❓&nbsp;Inconclusive | The assessment is inconclusive and the device may be affected because external trust configuration could not be verified. |
