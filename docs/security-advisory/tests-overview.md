---
title: Security Advisory Tests Overview
hide:
  - tags
tags:
  - Tests
  - Security
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The following matrix shows the Arista security advisories supported by ANTA.

!!! note "Detailed security advisory tests"
    To view the implementation details and inputs for each available test, see
    [Security Advisory Tests](tests.md).

!!! note
    `TBD` means **To Be Determined**.

## Assessment results

Each vulnerability assessment produces one of the following results:

| Result | Meaning |
| --- | --- |
| `Not affected` | The device does not meet the advisory's conditions for vulnerability or exposure. |
| `Affected` | The device meets the advisory's conditions and is not fully protected by a verified mitigation. |
| `Mitigated` | The device would otherwise be affected, but every exposure is protected by a device-enforced mitigation documented by the advisory. |
| `Inconclusive` | Available device information indicates possible exposure, but a necessary property cannot be determined from the device. |
| `Error` | Required device information is missing, invalid, contradictory, or could not be collected. This result makes no claim about whether the device is affected. |

An assessment may instead be `Skipped` when it could not be applied to the device.

| Security advisory | Last updated | Supported in ANTA version | Comment |
| --- | --- | --- | --- |
| Security Advisory 0148 | | N/A | Advance Notice |
| [Security Advisory 0147](https://www.arista.com/en/support/advisories-notices/security-advisory/24515-security-advisory-0147) | 2026-08-31 | v1.10 | |
| [Security Advisory 0146](https://www.arista.com/en/support/advisories-notices/security-advisory/24500-security-advisory-0146) | 2026-08-19 | v1.10 | |
| Security Advisories 0145–0143 | | TBD | |
| [Security Advisory 0142](https://www.arista.com/en/support/advisories-notices/security-advisory/24111-security-advisory-0142) | 2026-08-10 | v1.10 | |
| Security Advisory 0141 | | TBD | |
| [Security Advisory 0140](https://www.arista.com/en/support/advisories-notices/security-advisory/24074-security-advisory-0140) | 2026-06-03 | v1.10 | |
| Security Advisories 0139–0118 | | TBD | |
| [Security Advisory 0117](https://www.arista.com/en/support/advisories-notices/security-advisory/21394-security-advisory-0117) | 2025-05-20 | v1.10 | |
| Security Advisories 0116–0061 | | TBD | |
| Security Advisory 0060 | | N/A | Not Published |
| Security Advisories 0059–0001 | | TBD | |
