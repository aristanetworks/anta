---
anta_title: Bug Compliance Analysis
---
<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The `anta bug` command checks inventory devices against the Arista bug database (`AlertBase-CVP.json`) and produces a compliance report showing which known bugs may affect each device based on its EOS version, hardware model, and active features.

## Overview

```bash
--8<-- "anta_bug_help.txt"
```

## Bug Database

The bug database can be provided in two ways:

### Local file

Use the `--bug-database` (or `-b`) option to point to a local copy of `AlertBase-CVP.json`:

```bash
anta bug -b AlertBase-CVP.json table
```

### Download from arista.com

Use the `--token` option (or `ANTA_BUG_TOKEN` environment variable) to download the database directly from arista.com:

```bash
export ANTA_BUG_TOKEN="your-api-token"
anta bug table
```

When downloading, ANTA caches the database locally in the XDG cache directory (`$XDG_CACHE_HOME/anta/` or `~/.cache/anta/`) to avoid re-downloading on every run. The cache expires after **12 hours** and is automatically refreshed on the next run. The `--disable-cache` flag forces a fresh download, bypassing the cached copy.

## How It Works

For each device in the inventory, `anta bug` performs the following:

1. **Version check** — Determines if the device's EOS version falls within the affected range of each bug (between `versionIntroduced` and `versionFixed`).

2. **Hardware tag resolution** — Maps the device's hardware model (e.g., `DCS-7280SR3-48YC8-F`) to platform and ASIC tags (e.g., `Sand`, `SandGen4`, `Jericho2`) using the `tagImplication` graph from the bug database.

3. **Feature tag resolution** — Queries the device's SysDB via Acons to evaluate AQL (Arista Query Language) rules from the database's `queryRules`. This determines which features are active on the device (e.g., `bgpEnabled`, `vxlanEnabled`, `mlagEnabled`).

4. **Bug matching** — For each bug, evaluates its `conjunction` expression (a logical OR of AND clauses over tags) against the device's resolved tags. A bug matches if the version is affected AND at least one conjunction clause is satisfied (or the bug has no conjunction).

## Output Formats

### Table (default)

```bash
anta bug -b AlertBase-CVP.json table
```

Produces a summary table with bug counts per severity, followed by a detail table:

```text
                              Bug Compliance Summary
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━┓
┃ Device ┃ Model               ┃ EOS Version ┃ Sev1 ┃ Sev2 ┃ Sev3 ┃ Sev4 ┃ Total ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━┩
│ smv030 │ DCS-7280CR3K-32P4-F │ 4.35.4M     │  -   │  2   │  1   │  -   │   3   │
└────────┴─────────────────────┴─────────────┴──────┴──────┴──────┴──────┴───────┘
```

Use `--wide` to show full bug summaries and fixed-in versions without truncation:

```bash
anta bug -b AlertBase-CVP.json table --wide
```

### JSON

```bash
anta bug -b AlertBase-CVP.json json
anta bug -b AlertBase-CVP.json json -o report.json
```

Outputs a JSON array with full details including resolved tags and match reasons. Use `-o` / `--output` to save to a file instead of printing to the console.

### CSV

```bash
anta bug -b AlertBase-CVP.json csv --csv-output report.csv
```

Saves a CSV file with columns: Device, Model, EOS Version, Bug ID, Severity, CVE, Bites, Summary, Fixed In, Matched By.

### Markdown report

```bash
anta bug -b AlertBase-CVP.json md-report --md-output report.md
```

Saves a Markdown report with a summary table and per-device bug details.

## Upgrade Impact Analysis

Use the `--target-version` (or `-t`) option to evaluate the impact of upgrading to a specific EOS version. This splits the matching bugs into two groups for each device:

- **Fixed by upgrade** — Bugs that would be resolved by upgrading to the target version.
- **Still present** — Bugs that remain even after upgrading.

```bash
anta bug -b AlertBase-CVP.json --target-version 4.36.0F table
```

The summary table adds "Fixed by Upgrade" and "Still Present" columns, and the detail table is split into two sections accordingly.

This works with all output formats:

```bash
# JSON — adds target_version, fixed_by_upgrade, and still_present fields
anta bug -b AlertBase-CVP.json -t 4.36.0F json -o report.json

# CSV — adds an "Upgrade Impact" column
anta bug -b AlertBase-CVP.json -t 4.36.0F csv --csv-output report.csv

# Markdown — adds target version header and split detail sections
anta bug -b AlertBase-CVP.json -t 4.36.0F md-report --md-output report.md
```

## Filtering

### By severity

Show only bugs at or above a given severity level:

```bash
anta bug -b AlertBase-CVP.json --severity sev2 table
```

### By device

Analyze specific devices only:

```bash
anta bug -b AlertBase-CVP.json -d spine1 -d spine2 table
```

### By tags

Filter devices by inventory tags:

```bash
anta bug -b AlertBase-CVP.json --tags dc1,leafs table
```

## Caching

When using `--token` to download the bug database, ANTA automatically caches the downloaded file to avoid repeated downloads:

- **Cache location**: `$XDG_CACHE_HOME/anta/AlertBase-CVP.json` (defaults to `~/.cache/anta/AlertBase-CVP.json`)
- **TTL**: 12 hours — after this period, the cache is considered expired and the database is re-downloaded
- **Force refresh**: Use `--disable-cache` to skip the cached copy and download a fresh database

When using `--bug-database` with a local file, the cache is not used.

## Environment Variables

| Variable            | Description                                           |
| ------------------- | ----------------------------------------------------- |
| `ANTA_BUG_TOKEN`    | Arista.com API token for downloading the bug database |
| `ANTA_BUG_DATABASE` | Path to a local `AlertBase-CVP.json` file             |

These are in addition to the standard ANTA environment variables (`ANTA_USERNAME`, `ANTA_PASSWORD`, `ANTA_INVENTORY`, etc.).

## Requirements

- The `--enable` flag is recommended to allow SysDB queries via Acons for feature tag resolution.
- Without `--enable`, only hardware/platform tags are resolved. Feature tags (e.g., `bgpEnabled`, `vxlanEnabled`) require privileged mode to query SysDB.
