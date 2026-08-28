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

## Markdown report

The Markdown report supports flattened and expanded device findings. Flattened output is the default and renders one row per advisory result with the authoritative parent advisory result and its issue-attributed messages.

Expanded output follows the regular ANTA Markdown parent/child layout:

- The parent row contains the device, test description, authoritative advisory result, and a summary of its detailed findings. All parent messages, when present, follow the summary as labelled overall evidence. Messages propagated from detailed findings may therefore also appear in the child rows.
- Each indented `├──` or `└──` row represents one detailed issue assessment emitted by the test.
- `Description` identifies the issue, `CVE(s)` lists its explicit CVE associations, and `Result` and `Messages` contain its final semantic conclusion and decisive device evidence.
- One issue may cover multiple CVEs or have no CVE association. Multiple independent issues associated with the same CVE remain separate rows.
- When the test emits no detailed issue assessments, expanded output contains only the parent row.

Expansion changes only presentation. It does not recalculate the parent advisory result or create findings for CVEs that the test did not assess independently.

Advisory severity is derived from the highest severity among its CVEs, or reported as `unknown` when the advisory has no CVEs.

## CSV report

The security advisory CSV uses one row for one reported finding and CVE association. Consumers do not need to know whether a test produced a detailed issue result internally: the `CVE Result` columns always contain the most specific result available for that row.

`Advisory Result` is the authoritative result of the complete advisory test for the device and is repeated on every row. Use it to answer questions about the advisory as a whole; consumers do not need to aggregate the individual rows to recover that conclusion.

Results use advisory-facing lowercase wording: `affected`, `not affected`, `mitigated`, `inconclusive`, and `error`. Results that were not evaluated retain the explicit execution states `skipped` or `unset`. Until a dedicated semantic state is available, a successful result is `mitigated` when its message contains the required "The device is affected but mitigated because ..." clause and `not affected` otherwise.

### Row selection

The reporter selects rows as follows:

- When a CVE has a detailed issue result, that result is emitted for the CVE.
- When a CVE has no detailed issue result, the parent advisory result is emitted as its fallback.
- A detailed result associated with multiple CVEs is emitted once for each CVE.
- Multiple independent detailed results for the same CVE remain separate rows.
- A detailed result without a CVE association is emitted as an additional row with empty CVE fields.
- An advisory without CVEs emits detailed non-CVE rows when available, or one parent-result row otherwise.

### Columns

| Column | Meaning |
| --- | --- |
| `Device` | Device assessed by the test. |
| `Test Name` | Advisory test class name. |
| `Advisory Result` | Authoritative, aggregated result of the complete advisory test. |
| `Advisory Result Messages` | Parent result messages, joined with newline characters. |
| `CVE Result` | Result of the detailed issue finding, or the parent result when no more specific finding exists. |
| `CVE Description` | Static description from the detailed issue finding. For a fallback row, this repeats the parent test description. |
| `CVE Result Messages` | Messages belonging to `CVE Result`, joined with newline characters. |
| `CVE Remediation` | Remediation entries belonging to `CVE Result`, joined with newline characters. |
| `Remediation` | Remediation entries belonging to the complete advisory result, joined with newline characters. |
| `Advisory ID` | Textual identifier such as `SA0117`; the prefix preserves leading zeroes in spreadsheet applications. |
| `Advisory Title`, `Advisory URL`, `Advisory Description` | Published advisory metadata. |
| `Advisory Severity` | Highest severity among the advisory's CVEs, or `unknown` without CVEs. |
| `CVE ID`, `CVE Severity` | Published metadata for the CVE represented by the row; empty for a non-CVE finding. |

### Text fields

The CSV contains no JSON-encoded cells. When a result carries multiple messages or remediation entries, the reporter joins them with real newline characters and the CSV writer quotes the field. Empty lists are represented by empty cells.

Descriptions remain static metadata containing the advisory title, issue identifiers, public URL when available, and a brief issue description. Result messages contain the semantic conclusion and decisive device evidence. Neither field contains remediation advice.

Result-specific remediation comes directly from the advisory result. It is not inferred from published advisory text.
