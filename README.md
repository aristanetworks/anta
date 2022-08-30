[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/network-test-automation/blob/master/LICENSE)
[![CI](https://github.com/arista-netdevops-community/network-test-automation/actions/workflows/test.yml/badge.svg)](https://github.com/arista-netdevops-community/network-test-automation/actions)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/network-test-automation.svg)](https://github.com/arista-netdevops-community/network-test-automation/releases/)

# Arista Network Test Automation (ANTA) Framework

This repository is a Python package to automate tests on Arista devices.

- The package name is [ANTA](./anta), which stands for **Arista Network Test Automation**.
- This package (or some functions of this package) can be imported in Python scripts:
  - To automate NRFU (Network Ready For Use) test on a preproduction network
  - To automate tests on a live network (periodically or on demand)

ANTA provides a set of tests to validate the state of your network. All these tests are documented in the [repository](./docs/api/README.md) and can be used in your own python environment by importing this python package in your scripts.

This repository comes with a set of [scripts](./scripts) to run __Arista Network Test Automation__ (ANTA) framework

- `check-devices.py` is an easy to use script to test your network with ANTA.
- `collect-eos-commands.py` to collect commands output from devices
- `collect-sheduled-show-tech.py` to collect the scheduled show tech-support files from devices

In addition you have also some useful scripts to help around testing:

- `clear-counters.py` to clear counters on devices
- `evpn-blacklist-recovery.py` to clear the list of MAC addresses which are blacklisted in EVPN
- `create-devices-inventory-from-cvp.py`: Build inventory for scripts from Arista Cloudvision (CVP)

> Most of these scripts use eAPI (EOS API). You can find examples of EOS automation with eAPI in this [repository](https://github.com/arista-netdevops-community/arista_eos_automation_with_eAPI).

# Installation

The easiest way to intall ANTA package is to run Python (`>=3.7`) and its pip package to install:

```bash
pip install git+https://github.com/arista-netdevops-community/network-test-automation.git
```

For more details about how to install package, please see the [requirements and intallation docs](docs/requirements-and-installation.md).

# Getting Started

This section shows how to use ANTA scripts with basic configuration. For more information, please refer to this [page](./docs/usage.md). Also a demo page is available in the [repository](./docs/demo.md) with full outputs.

## Configure Arista EOS devices

First, you need to configure your management interface

```eos
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
```

Then, configure access to eAPI:

```eos
management api http-commands
   protocol https port 443
   no shutdown
   vrf MGMT
      no shutdown
   !
!
```

## Create your inventory

First, we need to list devices we want to test. You can create a file manually with this format:

```yaml
anta_inventory:
  hosts:
  - host: 192.168.0.10
  - host: 192.168.0.11
  - host: 192.168.0.12
  - host: 192.168.0.13
  - host: 192.168.0.14
  - host: 192.168.0.15
  networks:
  - network: '192.168.110.0/24'
  ranges:
  - start: 10.0.0.9
    end: 10.0.0.11
  - start: 10.0.0.100
    end: 10.0.0.101
```

Or you can use [`create-devices-inventory-from-cvp.py`](scripts/create-devices-inventory-from-cvp.py) script to generate from Cloudvision

```bash
create-devices-inventory-from-cvp.py -cvp 192.168.0.5 -u arista -o inventory -c Spine
```

> __Note:__ Because repository is transitioning to this YAML inventory, some scripts are still based on legacy text based approach
>
> ```text
> 192.168.0.10
> 192.168.0.11
> 192.168.0.12
> 192.168.0.13
> 192.168.0.14
> 192.168.0.15
> ```

## Test Catalog

To test your network, it is important to define a test catalog to list all the tests to run against your inventory. Test catalog references python functions into a yaml file. This file can be loaded by [`anta.loader.parse_catalog`](anta/loader.py)

The structure to follow is like:

```yaml
<anta_tests_submodule>:
  - <anta_tests_submodule function name>:
      <test function option>:
        <test function option value>
```

Here is an example for basic things:

```yaml
# Load anta.tests.software
software:
  - verify_eos_version: # Verifies the device is running one of the allowed EOS version.
      versions: # List of allowed EOS versions.
        - 4.25.4M
        - 4.26.1F

# Load anta.tests.system
system:
  - verify_uptime: # Verifies the device uptime is higher than a value.
      minimum: 1

# Load anta.tests.configuration
configuration:
  - verify_zerotouch: # Verifies ZeroTouch is disabled.
  - verify_running_config_diffs:
```

## Test your network

To test EOS devices, this package comes with a generic script to run tests in your network. It requires an inventory file as well as a test catalog.

This script has multiple options to manage test coverage and reporting.

```bash
python scripts/check-devices.py -h

optional arguments:
  -h, --help            show this help message and exit
  --inventory INVENTORY, -i INVENTORY
                        ANTA Inventory file
  --catalog CATALOG, -c CATALOG
                        ANTA Tests catalog
  --username USERNAME, -u USERNAME
                        EOS Username
  --password PASSWORD, -p PASSWORD
                        EOS Password
  --enable_password ENABLE_PASSWORD, -e ENABLE_PASSWORD
                        EOS Enable Password
  --timeout TIMEOUT, -t TIMEOUT
                        eAPI connection timeout
  --hostip HOSTIP       search result for host
  --test TEST           search result for test
  --list                Display internal data
  --table               Result represented in tables
  --all-results         Display all test cases results. Default table view (Only valid with --table)
  --by-host             Provides summary of test results per device (Only valid with --table)
  --by-test-cases       Provides summary of test results per test case (Only valid with --table)
```

Default output is a table format listing all test results, and it can be changed to a report per test case or per host

### Default report

```bash
                             All tests results
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Device IP     ┃ Test Name              ┃ Test Status ┃ Message(s)       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ 10.73.252.11  │ verify_mlag_interfaces │ success     │                  │
│ 10.73.252.12  │ verify_mlag_interfaces │ success     │                  │
│ 10.73.252.102 │ verify_mlag_interfaces │ skipped     │ MLAG is disabled │
└───────────────┴────────────────────────┴─────────────┴──────────────────┘
```

### Report per test case

```
                                        Summary per test case
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Test Case              ┃ # of success ┃ # of failure ┃ # of errors ┃ List of failed or error nodes ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ verify_mlag_interfaces │ 8            │ 0            │ 0           │ []                            │
└────────────────────────┴──────────────┴──────────────┴─────────────┴───────────────────────────────┘
```

### Report per host

```bash
                                     Summary per host
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Host IP       ┃ # of success ┃ # of failure ┃ # of errors ┃ List of failed case        ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 10.73.252.11  │ 1            │ 0            │ 0           │ []                         │
│ 10.73.252.12  │ 1            │ 0            │ 0           │ []                         │
│ 10.73.252.13  │ 1            │ 0            │ 0           │ []                         │
│ 10.73.252.102 │ 0            │ 0            │ 0           │ []                         │
└───────────────┴──────────────┴──────────────┴─────────────┴────────────────────────────┘
````


You can find more information about usage in the following [docs](./docs/usage.md). Also a demo page is available in the [repository](./docs/demo.md) with full outputs.

# Contribution guide

Contributions are welcome. Please refer to the [contribution guide](CONTRIBUTING.md)

# Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
