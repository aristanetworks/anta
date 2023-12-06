<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/anta/blob/main/LICENSE)
[![Linting and Testing Anta](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml/badge.svg)](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/m/arista-netdevops-community/anta)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/anta.svg)](https://github.com/arista-netdevops-community/anta/releases/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/anta)
![coverage](https://raw.githubusercontent.com/arista-netdevops-community/anta/coverage-badge/latest-release-coverage.svg)

# Arista Network Test Automation (ANTA) Framework

ANTA is Python framework that automates tests for Arista devices.

- ANTA provides a [set of tests](api/tests.md) to validate the state of your network
- ANTA can be used to:
    - Automate NRFU (Network Ready For Use) test on a preproduction network
    - Automate tests on a live network (periodically or on demand)
- ANTA can be used with:
    - The [ANTA CLI](cli/overview.md)
    - As a [Python library](advanced_usages/as-python-lib.md) in your own application

![anta nrfu](https://raw.githubusercontent.com/arista-netdevops-community/anta/main/docs/imgs/anta-nrfu.svg)

```bash
# Install ANTA CLI
$ pip install anta

# Run ANTA CLI
$ anta --help
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test Automation (ANTA) CLI

Options:
  --version                       Show the version and exit.
  --log-file FILE                 Send the logs to a file. If logging level is
                                  DEBUG, only INFO or higher will be sent to
                                  stdout.  [env var: ANTA_LOG_FILE]
  -log, --log-level [CRITICAL|ERROR|WARNING|INFO|DEBUG]
                                  ANTA logging level  [env var:
                                  ANTA_LOG_LEVEL; default: INFO]
  --help                          Show this message and exit.

Commands:
  check  Check commands for building ANTA
  debug  Debug commands for building ANTA
  exec   Execute commands to inventory devices
  get    Get data from/to ANTA
  nrfu   Run NRFU against inventory devices
```

## Documentation

The documentation is published on [ANTA package website](https://www.anta.ninja). Also, a [demo repository](https://github.com/titom73/atd-anta-demo) is available to facilitate your journey with ANTA.

## Contribution guide

Contributions are welcome. Please refer to the [contribution guide](contribution.md)

## Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle), [Guillaume Mulocher](https://github.com/gmuloc) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
