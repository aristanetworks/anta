<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Arista Network Test Automation (ANTA) Framework

| **Code** | [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Numpy](https://img.shields.io/badge/Docstring_format-numpy-blue)](https://numpydoc.readthedocs.io/en/latest/format.html) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aristanetworks_anta&metric=alert_status&branch=main)](https://sonarcloud.io/summary/new_code?id=aristanetworks_anta) [![codecov](https://codecov.io/gh/aristanetworks/anta/graph/badge.svg?token=ZAQ6RJMDYS)](https://codecov.io/gh/aristanetworks/anta) |
| :------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **License** | [![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/aristanetworks/anta/blob/main/LICENSE) |
| **GitHub** | [![CI](https://github.com/aristanetworks/anta/actions/workflows/code-testing.yml/badge.svg)](https://github.com/aristanetworks/anta/actions/workflows/code-testing.yml) ![Commit](https://img.shields.io/github/last-commit/aristanetworks/anta) ![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/m/aristanetworks/anta) [![GitHub release](https://img.shields.io/github/release/aristanetworks/anta.svg)](https://github.com/aristanetworks/anta/releases/) [![Contributors](https://img.shields.io/github/contributors/aristanetworks/anta)](https://github.com/aristanetworks/anta/graphs/contributors) |
| **PyPI** | ![PyPI Version](https://img.shields.io/pypi/v/anta) ![Python Versions](https://img.shields.io/pypi/pyversions/anta) ![Python format](https://img.shields.io/pypi/format/anta) ![PyPI - Downloads](https://img.shields.io/pypi/dm/anta) |

ANTA is a Python framework that automates tests for Arista devices.

- ANTA provides a [set of tests](https://anta.arista.com/stable/api/tests/) to validate the state of your network
- ANTA can be used to:
  - Automate NRFU (Network Ready For Use) tests on a preproduction network
  - Automate tests on a live network (periodically or on demand)
- ANTA can be used:
  - As a [Python library](https://anta.arista.com/stable/advanced_usages/as-python-lib/) in your own application
  - Via the [ANTA CLI](https://anta.arista.com/stable/cli/overview/)

![anta nrfu](https://raw.githubusercontent.com/aristanetworks/anta/main/docs/imgs/anta-nrfu.svg)

## Install ANTA library

The library will **NOT** install the necessary dependencies for the CLI.

```bash
# Install ANTA as a library
pip install anta
```

## Install ANTA CLI

If you plan to use ANTA only as a CLI tool you can use `pipx` to install it.
[`pipx`](https://pipx.pypa.io/stable/) is a tool to install and run Python applications in isolated environments. Refer to `pipx` instructions to install on your system.
`pipx` installs ANTA in an isolated Python environment and makes it available globally.

<!-- markdownlint-disable no-emphasis-as-heading -->
**This is not recommended if you plan to contribute to ANTA**
<!-- markdownlint-enable no-emphasis-as-heading -->

```bash
# Install ANTA CLI with pipx
$ pipx install anta[cli]

# Run ANTA CLI
$ anta --help
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test Automation (ANTA) CLI.

Options:
  --help                          Show this message and exit.
  --version                       Show the version and exit.
  --log-file FILE                 Send the logs to a file. If logging level is
                                  DEBUG, only INFO or higher will be sent to
                                  stdout.  [env var: ANTA_LOG_FILE]
  -l, --log-level [critical|error|warning|info|debug]
                                  ANTA logging level  [env var:
                                  ANTA_LOG_LEVEL; default: INFO]

Commands:
  check  Commands to validate configuration files.
  debug  Commands to execute EOS commands on remote devices.
  exec   Commands to execute various scripts on EOS devices.
  get    Commands to get information from or generate inventories.
  nrfu   Run ANTA tests on selected inventory devices.
```

You can also still choose to install it directly with `pip`:

```bash
pip install anta[cli]
```

## Documentation

The documentation is published on the [ANTA package website](https://anta.arista.com).

## Contribution guide

Contributions are welcome. Please refer to the [contribution guide](https://anta.arista.com/stable/contribution/).

## Credits

Thank you to [Jeremy Schulman](https://github.com/jeremyschulman) for [aio-eapi](https://github.com/jeremyschulman/aio-eapi/tree/main/aioeapi), the upstream source for ANTA's `asynceapi` client.

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle), [Guillaume Mulocher](https://github.com/gmuloc) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidance.
