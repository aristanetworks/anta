[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/anta/blob/main/LICENSE)
[![Linting and Testing Anta](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml/badge.svg)](https://github.com/arista-netdevops-community/anta/actions/workflows/code-testing.yml)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/anta.svg)](https://github.com/arista-netdevops-community/anta/releases/)
![PyPI - Downloads/month](https://img.shields.io/pypi/dm/eos-downloader)
![coverage](https://raw.githubusercontent.com/arista-netdevops-community/anta/gh-pages/latest-release-coverage.svg)

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
--8<-- "anta_help.txt"
```

!!! info
    `username`, `password`, `enable`, and `enable-password` values are the same for all devices


## Documentation

The documentation is published on [ANTA package website](https://www.anta.ninja)

## Contribution guide

Contributions are welcome. Please refer to the [contribution guide](https://www.anta.ninja/main/contribution/)

## Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle), [Guillaume Mulocher](https://github.com/gmuloc) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
