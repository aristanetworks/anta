[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/network-test-automation/blob/master/LICENSE)
[![CI](https://github.com/arista-netdevops-community/network-test-automation/actions/workflows/test.yml/badge.svg)](https://github.com/arista-netdevops-community/network-test-automation/actions)
[![github release](https://img.shields.io/github/release/arista-netdevops-community/network-test-automation.svg)](https://github.com/arista-netdevops-community/network-test-automation/releases/)

# About this repository

This repository is a Python package to automate tests on Arista devices.

- The package name is [anta](anta), which stands for **Arista Network Test Automation**.
- This package (or some functions of this package) can be imported in Python scripts:
  - To automate NRFU (Network Ready For Use) test on a preproduction network
  - To automate tests on a live network (periodically or on demand)

ANTA provides a set of tests to validate the state of your network. All these tests are documented in the [repository](./documentation/overview.md) and can be used in your own python environment by importing this python package in your scripts.

This repository comes with a set of script to run __Arista Network Test Automation__ framework

- `check-devices.py` is an easy to use script to test your network with ANTA.
- `check-devices-reachability.py` to test your devices are ready to be tested.
- `collect-eos-commands.py` to collect commands output from devices
- `collect-sheduled-show-tech.py` to collect the scheduled show tech-support files from devices

In addition you have also some useful scripts to help around testing:

- Clear counters on devices (`clear-counters.py`)
- Clear the list of MAC addresses which are blacklisted in EVPN (`clear-counters.py`)
- Build inventory for scripts from Arista Cloudvision (CVP) (`create-devices-inventory-from-cvp.py`)


> Most of these scripts use eAPI (EOS API). You can find examples of EOS automation with eAPI in this [repository](https://github.com/arista-netdevops-community/arista_eos_automation_with_eAPI).

# Requirements and installation

The easiest way to intall ANTA package is to run Python (`>=3.7`) and its pip package to install:

```bash
pip install git+https://github.com/arista-netdevops-community/network-test-automation.git
```

For more details about how to install package, please see the [requirements and intallation documentation](documentation/requirements-and-installation.md) for the requirements and installation procedure.

# Getting Started

This section shows how to use ANTA scripts with basic configuration. For more information, please refer to this [page](./documentation/usage.md). Also a demo page is available in the [repository](./documentation/demo.md) with full outputs.

## Configure Arista EOS devices.

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

```txt
10.73.1.101
2.2.2.2
10.73.1.102
10.73.1.106
```

Or you can use [`create-devices-inventory-from-cvp.py`](scripts/create-devices-inventory-from-cvp.py) script to generate from Cloudvision

```bash
create-devices-inventory-from-cvp.py -cvp 192.168.0.5 -u arista -o inventory -c Spine
```

## Test device reachability

Before running NRFU tests, we are going to test if we can connect to devices:

```bash
check-devices-reachability.py -i devices.txt -u username
```

## Test you network

Now we can run tests across the entire inventory

```bash
check-devices.py -i devices.txt -t tests.yaml -o output.txt -u <username>
```

> Note the `-t tests.yml` that list all your tests. An example is available under [examples folder](./examples/tests.yaml)

You can find more information about usage in the following [documentation](./documentation/usage.md). Also a demo page is available in the [repository](./documentation/demo.md) with full outputs.
# Contribution guide

Contributions are welcome. Please refer to the [contribution guide](CONTRIBUTING.md)

# Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
