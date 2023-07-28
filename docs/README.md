[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/anta/blob/main/LICENSE)
[![Linting and Testing Anta](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml/badge.svg)](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/anta.svg)](https://github.com/arista-netdevops-community/anta/releases/)
![PyPI - Downloads/month](https://img.shields.io/pypi/dm/eos-downloader)
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

![anta nrfu](imgs/anta-nrfu.svg)

```bash
# Install ANTA CLI
$ pip install anta

# Run ANTA CLI
$ anta --help
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test Automation (ANTA) CLI

Options:
  --version                       Show the version and exit.
  --username TEXT                 Username to connect to EOS  [env var:
                                  ANTA_USERNAME; required]
  --password TEXT                 Password to connect to EOS  [env var:
                                  ANTA_PASSWORD; required]
  --timeout INTEGER               Global connection timeout  [env var:
                                  ANTA_TIMEOUT; default: 5]
  --insecure                      Disable SSH Host Key validation  [env var:
                                  ANTA_INSECURE]
  --enable                        Add enable mode towards the devices if
                                  required to connect  [env var: ANTA_ENABLE]
  --enable-password TEXT          Enable password if required to connect,
                                  --enable MUST be set  [env var:
                                  ANTA_ENABLE_PASSWORD]
  -i, --inventory FILE            Path to the inventory YAML file  [env var:
                                  ANTA_INVENTORY; required]
  --log-level, --log [CRITICAL|ERROR|WARNING|INFO|DEBUG]
                                  ANTA logging level  [env var:
                                  ANTA_LOG_LEVEL; default: INFO]
  --ignore-status                 Always exit with success  [env var:
                                  ANTA_IGNORE_STATUS]
  --ignore-error                  Only report failures and not errors  [env
                                  var: ANTA_IGNORE_ERROR]
  --help                          Show this message and exit.

Commands:
  debug  Debug commands for building ANTA
  exec   Execute commands to inventory devices
  get    Get data from/to ANTA
  nrfu   Run NRFU against inventory devices
```

!!! info
    `username`, `password`, `enable`, and `enable-password` values are the same for all devices


## Documentation

The documentation is published on [ANTA package website](https://www.anta.ninja)

## Contribution guide

Contributions are welcome. Please refer to the [contribution guide](https://www.anta.ninja/main/contribution/)

## Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle), [Guillaume Mulocher](https://github.com/gmuloc) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
