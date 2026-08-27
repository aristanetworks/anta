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

## Markdown report

The Markdown report supports flattened and expanded device findings. Flattened output is the default and renders one row per advisory result with the authoritative parent advisory result and its issue-attributed messages.

Expanded output follows the regular ANTA Markdown parent/child layout:

- The parent row contains the device, test description, authoritative advisory result, and a summary of its detailed findings. All parent messages, when present, follow the summary as labelled overall evidence. Messages propagated from detailed findings may therefore also appear in the child rows.
- Each indented `├──` or `└──` row represents one detailed issue assessment emitted by the test.
- `Description` identifies the issue, `CVE(s)` lists its explicit CVE associations, and `Result` and `Messages` contain its final semantic conclusion and decisive device evidence.
- One issue may cover multiple CVEs or have no CVE association. Multiple independent issues associated with the same CVE remain separate rows.
- When the test emits no detailed issue assessments, expanded output contains only the parent row.

Expansion changes only presentation. It does not recalculate the parent advisory result or create findings for CVEs that the test did not assess independently.

## CSV report

The security advisory CSV uses one row for one reported finding and CVE association. Consumers do not need to know whether a test produced a detailed issue result internally: the `Result` column always contains the most specific result available for that row.

`Advisory Result` is the authoritative result of the complete advisory test for the device and is repeated on every row. Use it to answer questions about the advisory as a whole. For example, the device is not affected by an advisory only when its `Advisory Result` is `success`; consumers do not need to aggregate the individual rows to recover that conclusion.

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
| `Description` | Static test metadata. It does not contain device evidence, results, or remediation. |
| `Advisory Result` | Authoritative, aggregated result of the complete advisory test. |
| `Result` | Result of the detailed issue finding, or the parent result when no more specific finding exists. |
| `Result Description` | Identifier for the detailed issue finding. For a fallback row, this repeats the parent test description. |
| `Result Message(s) JSON` | JSON array containing the messages belonging to `Result`. |
| `Advisory ID` | Textual identifier such as `SA0117`; the prefix preserves leading zeroes in spreadsheet applications. |
| `Advisory Title`, `Advisory Severity`, `Advisory URL`, `Advisory Description` | Published advisory metadata. |
| `CVE ID`, `CVE Severity` | Published metadata for the CVE represented by the row; empty for a non-CVE finding. |
| `CVSS Scores JSON` | JSON array of `{version, score, vector}` objects for the row's CVE. |
| `Published Mitigations JSON`, `Published Resolutions JSON` | JSON arrays of `{name, details, url}` objects from the advisory. These are published guidance, not result-specific remediation. |

### Structured values

Structured values use JSON arrays instead of delimiter-joined text. Empty collections are represented by `[]`, and an unavailable action URL is represented by `null`. This preserves boundaries in descriptions and URLs that may themselves contain punctuation, and lets Excel, pandas, or database import pipelines parse the values without guessing a delimiter.

Result-specific remediation is intentionally absent until ANTA exposes a remediation field on results. When that field is available, remediation must follow the row's `Result`; it must not be inferred from the advisory's published mitigations or resolutions.
