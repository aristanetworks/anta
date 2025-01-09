---
anta_title: ANTA check commands
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The ANTA check command allow to execute some checks on the ANTA input files.
Only checking the catalog is currently supported.

```bash
anta check --help
Usage: anta check [OPTIONS] COMMAND [ARGS]...

  Check commands for building ANTA

Options:
  --help  Show this message and exit.

Commands:
  catalog  Check that the catalog is valid
```

## Checking the catalog

```bash
Usage: anta check catalog [OPTIONS]

  Check that the catalog is valid.

Options:
  -c, --catalog FILE            Path to the test catalog file  [env var:
                                ANTA_CATALOG; required]
  --catalog-format [yaml|json]  Format of the catalog file, either 'yaml' or
                                'json'  [env var: ANTA_CATALOG_FORMAT]
  --help                        Show this message and exit.
```
