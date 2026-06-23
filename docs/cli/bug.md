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

```
                          Bug Compliance Summary
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━┓
┃ Device ┃ Model               ┃ EOS Version ┃ Sev1 ┃ Sev2 ┃ Sev3 ┃ Total ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━┩
│ smv030 │ DCS-7280CR3K-32P4-F │ 4.35.4M     │  -   │  2   │  1   │   3   │
└────────┴─────────────────────┴─────────────┴──────┴──────┴──────┴───────┘
```

### JSON

```bash
anta bug -b AlertBase-CVP.json json
anta bug -b AlertBase-CVP.json json -o report.json
```

Outputs a JSON array with full details including resolved tags and match reasons.

### CSV

```bash
anta bug -b AlertBase-CVP.json csv --csv-output report.csv
```

Saves a CSV file with columns: Device, Model, EOS Version, Bug ID, Severity, CVE, Bites, Summary, Fixed In, Matched By.

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

## Environment Variables

| Variable | Description |
|---|---|
| `ANTA_BUG_TOKEN` | Arista.com API token for downloading the bug database |
| `ANTA_BUG_DATABASE` | Path to a local `AlertBase-CVP.json` file |

These are in addition to the standard ANTA environment variables (`ANTA_USERNAME`, `ANTA_PASSWORD`, `ANTA_INVENTORY`, etc.).

## Requirements

- The `--enable` flag is recommended to allow SysDB queries via Acons for feature tag resolution.
- Without `--enable`, only hardware/platform tags are resolved. Feature tags (e.g., `bgpEnabled`, `vxlanEnabled`) require privileged mode to query SysDB.
