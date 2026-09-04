---
title: ANTA PSIRT CLI
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
and exit handling with [`anta nrfu`](../cli/nrfu.md).

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

The command accepts the shared ANTA environment variables documented in the
[ANTA CLI overview](../cli/overview.md#anta-environment-variables).
`ANTA_CATALOG` is optional for `anta psirt`: when unset, the command uses the
complete catalog of advisory tests installed with ANTA. When set, it replaces
that default catalog.

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

The table, text, JSON, and Jinja template reports reuse the generic NRFU
renderers. CSV and Markdown use the security advisory reporters to include
advisory and vulnerability metadata with per-device findings. Markdown reports
also include a run overview with execution timing, inventory and filter details,
and assessment counts. CSV also includes result remediation when provided by
the advisory test.

See [Security Advisory Reports](reports.md) for the
report schemas, result semantics, and detailed rendering behavior.

```bash
anta psirt --inventory inventory.yml --catalog sa.yml csv --csv-output sa-report.csv
anta psirt --inventory inventory.yml --catalog sa.yml md-report --md-output sa-report.md
anta psirt --inventory inventory.yml --catalog sa.yml md-report --md-output sa-report-expanded.md --expand
```

Use `--expand` on the Markdown report to include atomic advisory findings and
their vulnerability associations beneath each device result.

See the [NRFU documentation](../cli/nrfu.md) for report options, filters, and dry-run
behavior.
