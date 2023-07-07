[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/anta/blob/master/LICENSE)
[![Linting and Testing Anta](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml/badge.svg)](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/anta.svg)](https://github.com/arista-netdevops-community/anta/releases/)

# Arista Network Test Automation (ANTA) Framework

__WARNING:__ Documentation is work in progress for version 0.6.0 available in Pypi.

This repository is a Python package to automate tests on Arista devices.

- The package name is ANTA, which stands for **Arista Network Test Automation**.
- This package provides a set of tests to validate the state of your network.
- This package can be imported in Python scripts:
  - To automate NRFU (Network Ready For Use) test on a preproduction network
  - To automate tests on a live network (periodically or on demand)

This repository comes with a cli to run __Arista Network Test Automation__ (ANTA) framework using your preferred shell:

```bash
# Install ANTA CLI
$ pip install anta

# Run ANTA CLI
$ anta
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
  --enable-password TEXT          Enable password if required to connect  [env
                                  var: ANTA_ENABLE_PASSWORD]
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

<img src="https://github.com/arista-netdevops-community/anta/raw/master/docs/imgs/anta-nrfu-table-group-by-test-output.png"></img>

# Documentation

The documentation is published on [ANTA package website](https://www.anta.ninja)

# Contribution guide

Contributions are welcome. Please refer to the [contribution guide](https://raw.githubusercontent.com/arista-netdevops-community/anta/master/docs/contribution.md)

# Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle), [Guillaume Mulocher](https://github.com/gmuloc) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
