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

These reports are generated with the `anta psirt` command. See the [PSIRT CLI documentation](cli/psirt.md) for usage instructions and examples.

## Vulnerability metadata

An advisory may contain zero or more vulnerabilities. Each vulnerability has one identifier, a description, and a manually assigned normalized severity. The generic model accepts identifiers from CVE, the GitHub Advisory Database, Google Threat Intelligence, and other providers without provider-specific subclasses or validation.

Severity can be `unknown`, `none`, `low`, `medium`, `high`, or `critical`. Advisory authors select the appropriate value from the source material.

## Markdown report

The Markdown report supports flattened and expanded device findings. Flattened output is the default and renders one row per advisory result with the authoritative parent advisory result and its issue-attributed messages. Each advisory detail presents its severity, published URL, and description in a standard Markdown blockquote.

The assessment summary reports `mitigated` devices separately from `not affected` devices so that successful mitigations remain visible at a glance. Advisories and their vulnerability metadata are ordered from critical to unknown severity.

Every Markdown report ends with a **Run Overview** containing one vertical table. It lists the ANTA version, execution duration and timestamps, number of security advisories tested, initial inventory size, assessed devices, devices excluded by filters, devices unreachable during setup, applied filters, and setup warnings when present.

The overview describes the execution context. The `--expand` option affects only the presentation of device findings.
Likewise, `--hide` filters displayed findings without changing the assessment counts; when it hides every finding, the report still contains the run overview.

Expanded output follows the regular ANTA Markdown parent/child layout:

- The parent row contains the device, test description, authoritative advisory result, and a summary of its detailed findings. All parent messages, when present, follow the summary as labelled overall evidence. Messages propagated from detailed findings may therefore also appear in the child rows.
- Each indented `├──` or `└──` row represents one detailed issue assessment emitted by the test.
- `Description` uses the published vulnerability descriptions for associated findings and the atomic description for unassociated findings. `Vulnerability ID(s)` lists explicit vulnerability associations prefixed by their severity icons, while `Result` and `Findings` contain the final semantic conclusion and decisive device evidence.
- `Remediations` contains issue-specific remediation on atomic rows. Parent rows in both flattened and expanded reports display the stable, deduplicated aggregation of test-level and atomic remediation entries as bullets when atomic remediation contributes to the aggregation.
- One issue may cover multiple vulnerabilities or have no vulnerability association. Multiple independent issues associated with the same vulnerability remain separate rows.
- When the test emits no detailed issue assessments, expanded output contains only the parent row.

Expansion changes only presentation. It does not recalculate the parent advisory result or create findings for vulnerabilities that the test did not assess independently.

Advisory severity is derived from the highest normalized severity among its vulnerabilities. It is `unknown` when the advisory has no vulnerabilities or every vulnerability has unknown severity.

## CSV report

The security advisory CSV uses one row for one reported vulnerability result and vulnerability association. `Vulnerability Result`, `Vulnerability Result Messages`, and `Vulnerability Remediation` contain the most specific result data available for that row. `Vulnerability ID`, `Vulnerability Description`, and `Vulnerability Severity` contain published metadata rather than device evidence.

`Advisory Result` is the authoritative result of the complete advisory test for the device and is repeated on every row. Use it to answer questions about the advisory as a whole; consumers do not need to aggregate the individual rows to recover that conclusion.

Results use advisory-facing lowercase wording: `affected`, `not affected`, `mitigated`, `inconclusive`, and `error`. Results that were not evaluated retain the explicit execution states `skipped` or `unset`. Until a dedicated semantic state is available, a successful result is `mitigated` when its message contains the required "The device is affected but mitigated because ..." clause and `not affected` otherwise.

### Row selection

The reporter selects rows as follows:

- When a vulnerability has a detailed issue result, that result is emitted for the vulnerability.
- When a vulnerability has no detailed issue result, the parent advisory result is emitted as its fallback.
- A detailed result associated with multiple vulnerabilities is emitted once for each vulnerability.
- Multiple independent detailed results for the same vulnerability remain separate rows.
- A detailed result without a vulnerability association is emitted as an additional row with empty vulnerability fields.
- An advisory without vulnerabilities emits unassociated detailed rows when available, or one parent-result row otherwise.

### Columns

| Column | Meaning |
| --- | --- |
| `Device` | Device assessed by the test. |
| `Test Name` | Advisory test class name. |
| `Advisory Result` | Authoritative, aggregated result of the complete advisory test. |
| `Advisory Result Messages` | Parent result messages, joined with newline characters. |
| `Vulnerability Result` | Result of the detailed issue result, or the parent result when no more specific result exists. |
| `Vulnerability Result Messages` | Messages belonging to `Vulnerability Result`, joined with newline characters. |
| `Vulnerability Remediation` | Remediation entries belonging to `Vulnerability Result`, joined with newline characters. |
| `Advisory Remediation` | Remediation entries belonging to the complete advisory result, joined with newline characters. |
| `Advisory ID` | Textual identifier such as `SA0117`; the prefix preserves leading zeroes in spreadsheet applications. |
| `Advisory Title`, `Advisory URL`, `Advisory Description` | Published advisory metadata. |
| `Advisory Severity` | Highest normalized severity among the advisory's vulnerabilities, or `unknown` without a known severity. |
| `Vulnerability ID`, `Vulnerability Description`, `Vulnerability Severity` | Published metadata for the vulnerability represented by the row; empty for an unassociated result. |

### Text fields

The CSV contains no JSON-encoded cells. When a result carries multiple messages or remediation entries, the reporter joins them with real newline characters and the CSV writer quotes the field. Empty lists are represented by empty cells.

Advisory and vulnerability descriptions are published metadata. Result messages contain the semantic conclusion and decisive device evidence. Neither field contains remediation advice.

Result-specific remediation comes directly from the advisory result. It is not inferred from published advisory text.
