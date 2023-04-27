[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/anta/blob/master/LICENSE)
[![CI](https://github.com/arista-netdevops-community/network-test-automation/actions/workflows/test.yml/badge.svg)](https://github.com/arista-netdevops-community/anta/actions)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/network-test-automation.svg)](https://github.com/arista-netdevops-community/anta/releases/)

# Arista Network Test Automation (ANTA) Framework

__WARNING:__ A work is in progress to make test definition easier and more scalable starting with PR#173. As it is a breaking change, it is highly recommended to use version published on Pypi until we complete the work.

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

  Arista Network Test CLI

Options:
  --username TEXT         Username to connect to EOS  [env var: ANTA_USERNAME]
  --password TEXT         Password to connect to EOS  [env var: ANTA_PASSWORD]
  --timeout INTEGER       Connection timeout (default 5)  [env var: ANTA_TIMEOUT]
  --enable-password TEXT  Enable password if required to connect  [env var: ANTA_ENABLE_PASSWORD]
  -i, --inventory PATH    Path to your inventory file  [env var: ANTA_INVENTORY]
  --timeout INTEGER       Connection timeout (default 5)  [env var: ANTA_TIMEOUT]
  --help                  Show this message and exit.

Commands:
  exec  Execute commands to inventory devices
  get   Get data from/to ANTA
  nrfu  Run NRFU against inventory devices
```

<img src="https://github.com/arista-netdevops-community/anta/raw/master/docs/imgs/anta-nrfu-table-group-by-test-output.png"></img>

# Documentation

The documentation is published on [ANTA package website](https://www.anta.ninja)

# Contribution guide

Contributions are welcome. Please refer to the [contribution guide](https://raw.githubusercontent.com/arista-netdevops-community/anta/master/docs/contribution.md)

# Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle), [Guillaume Mulocher](https://github.com/gmuloc) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
