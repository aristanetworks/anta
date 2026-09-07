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

Severity can be `unknown`, `none`, `low`, `medium`, `high`, or `critical`. Advisory authors select the appropriate value from the source material.

## Markdown report

The Markdown report renders one device finding row per vulnerability assessment emitted by the advisory test. Each advisory detail presents its severity, published URL, and description in a standard Markdown blockquote.

The assessment summary reports `mitigated` devices separately from `not affected` devices so that successful mitigations remain visible at a glance. Advisories and their vulnerability metadata are ordered from critical to unknown severity.

Every Markdown report ends with a **Run Overview** containing one vertical table. It lists the ANTA version, execution duration and timestamps, number of security advisories tested, initial inventory size, assessed devices, devices excluded by filters, devices unreachable during setup, applied filters, and setup warnings when present.

The overview describes the execution context. `--hide` filters displayed findings without changing the assessment counts; when it hides every finding, the report still contains the run overview.

Evaluated device findings use the atomic results produced by every security advisory test. Framework lifecycle outcomes remain on the parent test result and are expanded into rows only by the reporting layer:

- Each row is one vulnerability assessment for one device. Every detailed result is associated with zero or one vulnerability: `Vulnerability` lists that identifier prefixed by its severity icon. An advisory with no published vulnerabilities uses `-`.
- `Result` and `Findings` contain the final semantic conclusion and decisive device evidence for that assessment.
- `Remediations` contains the remediation for an affected, mitigated, or inconclusive finding. Not-affected, error, and skipped results have no remediation.
- Multiple independent issues associated with the same vulnerability remain separate rows.
- If execution is skipped or fails before assessment, the reporter derives one fallback row per published vulnerability from the parent result. An advisory with no published vulnerabilities contains one whole-advisory row instead. These fallback rows are presentation data and are not stored as atomic assessment results.

Advisory severity is derived from the highest normalized severity among its vulnerabilities. It is `unknown` when the advisory has no vulnerabilities or every vulnerability has unknown severity.

## CSV report

The security advisory CSV uses one row for one vulnerability assessment, matching the Markdown device findings. Evaluated rows come from atomic results; pre-assessment framework errors and skips are expanded from the parent result. `Vulnerability Result`, `Vulnerability Result Messages`, and `Vulnerability Remediation` contain the row's assessment or lifecycle outcome. `Vulnerability ID`, `Vulnerability Description`, and `Vulnerability Severity` contain published metadata rather than device evidence.

`Advisory Result` is the report-level conclusion for the complete advisory test on the device and is repeated on every row. The reporter derives evaluated conclusions from the structured findings retained by the atomic results and lifecycle outcomes from the parent result; consumers do not need to aggregate the individual rows themselves.

Results use advisory-facing lowercase wording: `affected`, `not affected`, `mitigated`, `inconclusive`, `error`, and `skipped`. Each evaluated atomic result retains the corresponding typed finding object. For generic ANTA behavior, not-affected and mitigated findings project to `success`; affected and inconclusive findings project to `failure`; error findings project to `error`. Reporters read the finding objects directly and never infer advisory semantics from messages. Reports reject `unset` results because dry-run stops before reporting.

An atomic `error` with an `ErrorResult` is an evaluated advisory conclusion: required observable evidence was unavailable or invalid. A parent-only `error` is instead a framework lifecycle outcome that prevented assessment. Both use the generic ANTA error status, but only the evaluated conclusion has a structured finding.

The complete advisory conclusion uses this precedence: `error` > `affected` > `inconclusive` > `mitigated` > `not affected`. The generic parent result remains aggregation plumbing for `ResultManager`, filtering, summaries, and CLI exit status; it is not a second copy of the advisory conclusion.

Advisory tests create atomic results only when they assess a vulnerability. If a test is skipped or encounters a framework error before assessment, the reporting layer expands the parent result so every published vulnerability is displayed with that status. Completed assessments always include the finding that explains the result. Like `anta nrfu --dry-run`, `anta psirt --dry-run` stops after planning and does not create a report.

### Row selection

The reporter selects rows as follows:

- Each evaluated row is one vulnerability assessment emitted by the advisory test.
- Each atomic result is associated with at most one vulnerability and emits exactly one evaluated row.
- Multiple independent detailed results for the same vulnerability remain separate rows.
- A detailed result without a vulnerability association is emitted with empty vulnerability fields.
- An advisory without vulnerabilities emits its unassociated detailed rows.
- Parent-only skipped and framework-error outcomes that prevent assessment are expanded by the reporter into one row per published vulnerability. An advisory with no published vulnerabilities produces one whole-advisory fallback row with empty vulnerability fields.

### Columns

| Column | Meaning |
| --- | --- |
| `Device` | Device assessed by the test. |
| `Test Name` | Advisory test class name. |
| `Advisory Result` | Report-level conclusion derived from the complete set of atomic findings. |
| `Advisory Result Messages` | Parent result messages, joined with newline characters. |
| `Vulnerability Result` | Result of the atomic assessment, or the parent lifecycle result for a fallback row. |
| `Vulnerability Result Messages` | Messages belonging to the atomic assessment or parent lifecycle result, joined with newline characters. |
| `Vulnerability Remediation` | Rendered structured remediation plan belonging to `Vulnerability Result`, or empty when that result has no plan. |
| `Advisory Remediation` | Stable, deduplicated aggregation of the structured remediation plans from the advisory's detailed issue results. |
| `Advisory ID` | Textual identifier such as `SA0117`; the prefix preserves leading zeroes in spreadsheet applications. |
| `Advisory Title`, `Advisory URL`, `Advisory Description` | Published advisory metadata. |
| `Advisory Severity` | Highest normalized severity among the advisory's vulnerabilities, or `unknown` without a known severity. |
| `Vulnerability ID`, `Vulnerability Description`, `Vulnerability Severity` | Published metadata for the vulnerability represented by the row; empty for an unassociated result. |

### Text fields

The CSV contains no JSON-encoded cells. Message collections, lines within a structured remediation plan, and multiple consolidated plans use literal `\n` separators inside their CSV cells. Empty message collections and missing remediation plans are represented by empty cells.

Advisory and vulnerability descriptions are published metadata. Result messages contain the semantic conclusion and decisive device evidence. Neither field contains remediation advice.

Result-specific remediation is rendered from the structured plan carried by the atomic finding. Advisory-level remediation is derived by consolidating those finding plans; it is not inferred from messages or published advisory text.
