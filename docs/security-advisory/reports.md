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

Security advisory reports combine device test results with published advisory metadata. The advisory result answers whether the complete advisory affects a device, while detailed results preserve the conclusions and evidence for individual issues.

These reports are generated with the `anta psirt` command. See the [ANTA PSIRT CLI](usage.md) documentation for usage instructions and examples.

## Vulnerability metadata

An advisory may contain zero or more vulnerabilities. Each vulnerability has one identifier, a description, and a manually assigned normalized severity. The generic model accepts identifiers from CVE, the GitHub Advisory Database, Google Threat Intelligence, and other providers without provider-specific subclasses or validation.

Severity can be `unknown`, `none`, `low`, `medium`, `high`, or `critical`. Advisory authors select the appropriate value from the source material. When multiple CVSS versions are published, use the severity explicitly assigned by the Arista advisory. For SA149 through SA178, this is the severity in SA148's CVSS 3.1 table.

## Markdown report

The Markdown report renders one device finding row per vulnerability assessment emitted by the advisory test. Each advisory detail presents its severity, published URL, and description in a standard Markdown blockquote.

The assessment summary reports `mitigated` devices separately from `not affected` devices so that successful mitigations remain visible at a glance. Advisories and their vulnerability metadata are ordered from critical to unknown severity.

Every Markdown report ends with a **Run Overview** containing one vertical table. It lists the ANTA version, execution duration and timestamps, number of security advisories tested, initial inventory size, assessed devices, devices excluded by filters, devices unreachable during setup, applied filters, and setup warnings when present.

The overview describes the execution context. `--hide` filters displayed findings without changing the assessment counts; when it hides every finding, the report still contains the run overview.

Device findings primarily use the atomic results produced by security advisory tests. When a test ends with `error`, `skipped`, or `unset` before producing an atomic result, the report emits one parent lifecycle row so the device and execution outcome remain visible:

- Each atomic row is one vulnerability assessment for one device. `Vulnerability` lists the associated identifier prefixed by its severity icon. A detailed result associated with multiple vulnerabilities is emitted once for each identifier. An unassociated result uses `-`.
- `Result` and `Findings` contain the final semantic conclusion and decisive device evidence for that assessment.
- `Remediations` contains the rendered structured remediation plan for an atomic issue when that issue is affected, mitigated, or inconclusive. Error and skipped issues may carry an operational plan that restores reachability or the missing evidence. Not-affected results do not carry remediation plans.
- A parent lifecycle row uses `-` for the vulnerability and remediation and reports the parent status and messages in `Result` and `Findings`.

Advisory severity is derived from the highest normalized severity among its vulnerabilities. It is `unknown` when the advisory has no vulnerabilities or every vulnerability has unknown severity.

## CSV report

The security advisory CSV normally uses one row for one atomic vulnerability assessment, matching the Markdown device findings. `Vulnerability Result`, `Vulnerability Result Messages`, and `Vulnerability Remediation` contain that atomic result. `Vulnerability ID`, `Vulnerability Description`, and `Vulnerability Severity` contain published metadata rather than device evidence. A test that ends with `error`, `skipped`, or `unset` without atomic results instead emits one parent lifecycle row with empty vulnerability metadata and remediation fields.

`Advisory Result` is the authoritative result of the complete advisory test for the device and is repeated on every row. Use it to answer questions about the advisory as a whole; consumers do not need to aggregate the individual rows to recover that conclusion.

Results use advisory-facing lowercase wording: `affected`, `not affected`, `mitigated`, `inconclusive`, and `error`. Results that were not evaluated retain the explicit execution states `skipped` or `unset`. `unset` is the status of tests that were prepared but not executed, which is the dry-run path; `anta psirt --dry-run` exits before writing CSV or Markdown reports. Advisory-specific reporters use the retained semantic status rather than inferring it from the generic result or message text.

### Row selection

The reporter selects rows as follows:

- Each atomic row is one vulnerability assessment emitted by the advisory test.
- A detailed result associated with multiple vulnerabilities is emitted once for each vulnerability.
- A detailed result without a vulnerability association is emitted with empty vulnerability fields.
- An advisory without vulnerabilities emits its unassociated detailed rows.
- An `error`, `skipped`, or `unset` parent result without detailed results is emitted once with empty vulnerability fields.
- A `failure` parent result without detailed results is currently omitted; support is postponed until its advisory-facing semantics, including known EOS command errors, are defined.

### Columns

| Column | Meaning |
| --- | --- |
| `Device` | Device assessed by the test. |
| `Test Name` | Advisory test class name. |
| `Advisory Result` | Authoritative, aggregated result of the complete advisory test. |
| `Advisory Result Messages` | Parent result messages, joined with newline characters. |
| `Vulnerability Result` | Result of the atomic issue result, or the parent lifecycle result when no atomic result exists. |
| `Vulnerability Result Messages` | Messages belonging to `Vulnerability Result`, joined with newline characters. Parent messages are used for a lifecycle row. |
| `Vulnerability Remediation` | Rendered structured remediation plan belonging to `Vulnerability Result`, or empty when that result has no plan. |
| `Advisory Remediation` | Stable, deduplicated aggregation of the structured remediation plans from the advisory's detailed issue results. |
| `Advisory ID` | Textual identifier such as `SA0117`; the prefix preserves leading zeroes in spreadsheet applications. |
| `Advisory Title`, `Advisory URL`, `Advisory Description` | Published advisory metadata. |
| `Advisory Severity` | Highest normalized severity among the advisory's vulnerabilities, or `unknown` without a known severity. |
| `Vulnerability ID`, `Vulnerability Description`, `Vulnerability Severity` | Published metadata for the vulnerability represented by the row; empty for an unassociated result. |

### Text fields

The CSV contains no JSON-encoded cells. Message collections, lines within a structured remediation plan, and multiple consolidated plans use literal `\n` separators inside their CSV cells. Empty message collections and missing remediation plans are represented by empty cells.

Advisory and vulnerability descriptions are published metadata. Result messages contain the semantic conclusion and decisive device evidence. Neither field contains remediation advice.

Result-specific remediation is rendered from the structured plan attached to the detailed advisory result. Advisory-level remediation is derived by consolidating those detailed plans; it is not inferred from published advisory text.
