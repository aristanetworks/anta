---
title: Run ANTA PSIRT Tests
hide:
  - tags
tags:
  - CLI
  - PSIRT
  - Preview
  - Security
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

!!! warning "Preview"
    The `anta psirt` command is a preview feature. Its interface and behavior may change at any time without a deprecation notice.

The `anta psirt` command runs the complete catalog of security advisory tests
installed with ANTA. It shares inventory options, filters, execution behavior,
and exit handling with [`anta nrfu`](nrfu.md).

## Command overview

```bash
--8<-- "anta_psirt_help.txt"
```

Provide an inventory and credentials as for NRFU. When no report subcommand is
specified, ANTA renders the table report:

```bash
anta psirt --inventory inventory.yml --username admin --prompt
```

By default, the command runs every test registered in the built-in
`anta.tests.advisories` catalog.

PSIRT-specific execution settings can be configured with
`ANTA_PSIRT_IGNORE_STATUS`, `ANTA_PSIRT_IGNORE_ERROR`,
and `ANTA_PSIRT_DRY_RUN`. Disconnect behavior remains global through
`ANTA_DISCONNECT_INVENTORY`.

## Override the catalog

Use `--catalog` to replace the package catalog with a YAML or JSON catalog:

```bash
anta psirt --inventory inventory.yml --catalog selected-advisories.yml table
```

The `ANTA_CATALOG` environment variable provides the same override. Overrides
replace the default catalog; they are not merged with it. Table, text, JSON,
and template reports may mix advisory and ordinary ANTA tests. The
advisory-specific CSV and Markdown reports require a catalog containing only
advisory tests.

## Reports

The text, JSON, and Jinja template reports reuse the generic NRFU renderers.
Table, CSV, and Markdown use security-advisory-specific reporters to include
advisory and vulnerability metadata with per-device findings. Markdown reports
also include a run overview with execution timing, inventory and filter details,
and assessment counts. CSV and table reports include result remediation when
provided by the advisory test:

```bash
anta psirt --inventory inventory.yml --catalog sa.yml csv --csv-output sa-report.csv
anta psirt --inventory inventory.yml --catalog sa.yml md-report --md-output sa-report.md
anta psirt --inventory inventory.yml --catalog sa.yml md-report --md-output sa-report-expanded.md --expand
```

Use `--expand` on the Markdown report to include atomic advisory findings and
their vulnerability associations beneath each device result.

### Table report

```bash
--8<-- "anta_psirt_table_help.txt"
```

The default table report first renders a summary grouped by advisory, followed
by one device findings table per advisory. Advisories are ordered from critical
to unknown severity. Each findings table title identifies and links its
advisory, and includes the advisory severity. Rows use advisory-facing results
such as `affected`, `mitigated`, and `not affected`, with findings and
remediations shown alongside the device. All per-advisory tables use the same
full-width column layout so their fields remain aligned.

Use `--summary-only` to omit all per-advisory device findings tables. Use
`--expand` to add each atomic finding as a `├──` or `└──` child beneath its
authoritative device result. Child rows show their vulnerability associations,
result, findings, and issue-specific remediation. Parent rows summarize their
detailed checks and aggregate stable, deduplicated remediation as bulleted
actions, prefixed by vulnerability IDs when the association is unambiguous.
These options cannot be combined.

The existing PSIRT `--device`, `--test`, and `--hide` options filter the visible
results. For example, this command limits execution to one advisory test and
expands its findings:

```bash
anta psirt --inventory inventory.yml --test VerifySA117 table --expand
```

When a catalog override mixes advisory and ordinary ANTA tests, advisory
results use the PSIRT tables and ordinary results follow in the generic ANTA
table. With `--summary-only`, ordinary results use the generic per-test summary.

See the [NRFU documentation](nrfu.md) for report options, filters, and dry-run
behavior.
