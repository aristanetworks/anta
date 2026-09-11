---
title: Security Advisory Reports
hide:
  - tags
tags:
  - Reports
  - Security Advisories
  - Preview
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

!!! warning "Preview"
    Security advisory reports are a preview feature. Their interface, schema, and behavior may change at any time without a deprecation notice.

Security advisory reports combine device test results with published advisory metadata. Generate them with the `anta psirt` command as described in
the [ANTA PSIRT CLI](usage.md) documentation.

## Choose a report format

| Format | Choose it for | Contents |
| --- | --- | --- |
| Markdown | Human review and remediation planning | An assessment summary, advisory metadata, per-device findings and remediations, and run context. |
| CSV | Filtering, spreadsheets, and automated processing | One row per reported vulnerability assessment, with the authoritative whole-advisory result repeated on every row. |
| Jinja template | Advanced custom presentation or integration | User-defined output built from the ANTA result data. Reach out to the ANTA maintainers if you need help creating a template. |

JSON, text, and table reports are not currently implemented for `anta psirt`.

## Interpret results

| Report result | Where it appears / scope | Meaning | What to do |
| --- | --- | --- | --- |
| 🛑 Affected | Detailed vulnerability result; may determine the whole-advisory result. | The device satisfies the advisory's vulnerability or exposure conditions and is not fully mitigated. Exploitation, compromise, triggering, or indicators of compromise do not need to be observed. | Apply the reported remediation and consult the linked advisory. |
| ❓ Inconclusive | Detailed vulnerability result; may determine the whole-advisory result. | Device facts indicate possible vulnerability, but a necessary property is not observable under the supported assessment. Collection or parsing failures are errors, not inconclusive results. | Resolve the stated uncertainty and follow the reported remediation. |
| 🛡️ Mitigated | Detailed vulnerability result; may determine the whole-advisory result. | The device would otherwise be affected, but every exposure is covered by a verified, device-enforced mitigation expressly documented by the advisory. General security practice alone is insufficient. | Preserve the verified control and follow the remaining remediation and advisory guidance. |
| ✅ Not affected | Detailed vulnerability result; may determine the whole-advisory result. | The device does not satisfy the vulnerability or exposure conditions, for example because it runs a fixed release, uses an excluded platform, or lacks a required feature. Disabling a necessary vulnerable feature is not affected, even if the advisory calls it a mitigation. | No remediation is required by this assessment. |
| ❗ Error | Either a detailed vulnerability-assessment error or a parent advisory execution/lifecycle error before detailed results exist. | Required device-observable evidence is missing, uncollectable, malformed, or contradictory, or the assessment cannot execute. Neither error scope makes a security claim. | Correct the evidence or execution problem and rerun. Any recovery instructions obtain an assessment; they are not security remediation. |
| ⏭️ Skipped | Lifecycle-only; a parent row appears when no detailed result exists. | The assessment did not run and makes no security claim. | Correct the reported reachability or support condition and rerun. |

## Understand advisory and vulnerability rows

Each device has an authoritative result for the complete advisory and may have several detailed vulnerability results. When several detailed results
exist, the whole-advisory result uses this precedence:

```text
error > affected > inconclusive > mitigated > not affected
```

Use the whole-advisory result to decide whether the advisory assessment for a device is complete and actionable. Then use the detailed rows to identify
the affected vulnerability, decisive evidence, and remediation. Do not aggregate detailed CSV rows to reconstruct the advisory result; the report
already provides it.

A detailed result normally produces one row for each associated vulnerability. A detailed advisory-wide result has no vulnerability identifier. If a
test ends with `error` or `skipped` before producing any detailed result, the report emits one **parent lifecycle row** so the device and
execution outcome remain visible. A parent lifecycle row has no vulnerability metadata or remediation.

## Act on remediation

Affected, mitigated, and inconclusive vulnerability results include a structured plan containing the applicable fixed release, configuration, command,
or operational action. Follow the plan on each detailed row and consult the linked Arista advisory for newly published fixed releases and current
mitigation guidance.

## Markdown report

The Markdown report is organized for human review:

1. **Advisory Assessment Summary** counts devices by whole-advisory result. `mitigated` is separate from `not affected` so active mitigations remain
   visible. The summary includes affected, inconclusive, mitigated, not-affected, error, and skipped counts.
2. **Security Advisory Details** presents the advisory severity, source URL, description, vulnerability metadata, and per-device findings and
   remediations. Advisories and vulnerabilities are ordered from critical to unknown severity.
3. **Run Overview** records the ANTA version, timing, tested advisories, inventory and assessed-device counts, setup exclusions and failures, applied
   filters, and setup warnings.

Advisory severity is the highest normalized severity among its vulnerabilities. It is `unknown` when the advisory has no known vulnerability severity.

The `--hide` option filters displayed findings without changing the assessment counts. If it hides every finding, the report still contains the run
overview.

## CSV report

The CSV report is intended for programmatic consumption. Each row combines three scopes:

- the assessed device and test;
- the authoritative result and metadata for the complete advisory;
- one detailed vulnerability result, or a parent lifecycle result when no detailed result exists.

### Columns

| Column | Scope | Meaning | When empty |
| --- | --- | --- | --- |
| `Device` | Execution | Device assessed by the test. | Never. |
| `Test Name` | Execution | Security advisory test class name. | Never. |
| `Advisory Result` | Advisory | Authoritative aggregated result of the complete advisory test for the device. It is repeated on every row for that device and advisory. | Never. |
| `Advisory Result Messages` | Advisory | Messages from the complete advisory result, joined with literal `\n` separators. | The advisory result has no messages. |
| `Vulnerability Result` | Detailed result | Security conclusion or error for the detailed assessment. A parent lifecycle row contains `error` or `skipped`. | Never for an emitted row. |
| `Vulnerability Result Messages` | Detailed result | Findings or execution messages belonging to `Vulnerability Result`, joined with literal `\n` separators. A parent lifecycle row uses the parent messages. | The detailed or parent result has no messages. |
| `Vulnerability Remediation` | Detailed result | Rendered structured plan belonging to the detailed result. | The result has no plan, including `not affected` and parent lifecycle rows. |
| `Advisory Remediation` | Advisory | Stable, deduplicated aggregation of the structured plans from all detailed results for this device and advisory. | No detailed result has a remediation plan. |
| `Advisory ID` | Advisory metadata | Text identifier such as `SA0117`; the prefix preserves leading zeroes in spreadsheet applications. | Never. |
| `Advisory Title` | Advisory metadata | Published advisory title. | Never. |
| `Advisory Severity` | Advisory metadata | Highest normalized vulnerability severity: `unknown`, `none`, `low`, `medium`, `high`, or `critical`. | Never; `unknown` represents the absence of a known severity. |
| `Advisory URL` | Advisory metadata | Published Arista advisory URL. | Never. |
| `Advisory Description` | Advisory metadata | Published advisory description. | Never. |
| `Vulnerability ID` | Vulnerability metadata | Published identifier represented by the row. | The result is advisory-wide or is a parent lifecycle row. |
| `Vulnerability Description` | Vulnerability metadata | Published description for `Vulnerability ID`. | `Vulnerability ID` is empty. |
| `Vulnerability Severity` | Vulnerability metadata | Normalized published severity for `Vulnerability ID`. | `Vulnerability ID` is empty. |

### CSV value conventions

- `Advisory Result` is repeated on every detailed row; consumers should use it directly instead of deriving a whole-advisory status.
- A detailed result associated with multiple vulnerabilities is emitted once for each identifier. An advisory-wide detailed result uses empty vulnerability
  metadata fields.
- Message collections, lines within a remediation plan, and multiple consolidated plans use literal `\n` separators inside CSV cells. Cells are not
  JSON-encoded.
- Empty message collections, missing remediation plans, and unavailable vulnerability metadata use empty cells.
- Advisory and vulnerability descriptions are published metadata. Result messages contain conclusions and decisive device evidence. Remediation appears
  only in the remediation fields and is not inferred from published descriptions.
