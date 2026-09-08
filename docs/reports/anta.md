---
title: ANTA Test Reports
hide:
  - tags
tags:
  - Reports
  - NRFU
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

Regular ANTA reports present the test results produced by an NRFU run. Generate them with `anta nrfu`, or use the reporter classes directly when integrating ANTA into a Python application.

## Choose a report format

| Format | Best suited for | Output | Documentation |
| --- | --- | --- | --- |
| Text | Compact, human-readable terminal output | Terminal | [NRFU text report](../cli/nrfu.md#performing-nrfu-with-text-rendering) |
| JSON | Automation and data interchange | Terminal or file | [NRFU JSON report](../cli/nrfu.md#performing-nrfu-with-json-rendering) |
| CSV | Spreadsheet analysis and tabular data processing | File | [NRFU CSV report](../cli/nrfu.md#performing-nrfu-and-saving-results-in-a-csv-file) |
| Markdown | A shareable report with summaries and detailed results | File | [NRFU Markdown report](../cli/nrfu.md#performing-nrfu-and-saving-results-in-a-markdown-file) |
| Jinja | A custom text-based report and layout | Terminal or file | [NRFU custom report](../cli/nrfu.md#performing-nrfu-with-custom-reports) |

The NRFU documentation contains the command options and rendered examples for each format. Common inventory, catalog, device, test, status, and dry-run controls are also documented there because they determine which results are passed to the selected reporter.

## Python reporter API

Python applications can render an ANTA `ResultManager` with the regular reporter implementations:

- [CSV reporter](../api/reporter/csv.md)
- [Markdown reporter](../api/reporter/markdown.md)
- [Jinja reporter](../api/reporter/jinja.md)

These API references document the reporter classes and their supported methods. JSON serialization and text rendering are exposed by the CLI rather than as equivalent public reporter classes.

!!! note "ANTA PSIRT reports"
    For security advisory report formats and semantics, see
    [Security Advisory Reports](../security-advisory/reports.md).
