# Getting Started

This section shows how to use ANTA with basic configuration.

## Installation

The easiest way to intall ANTA package is to run Python (`>=3.7`) and its pip package to install:

```bash
pip install \
  git+https://github.com/arista-netdevops-community/network-test-automation.git
```

For more details about how to install package, please see the [requirements and intallation](./requirements-and-installation.md) section.

## Configure Arista EOS devices

First, you need to configure your management interface

```eos
vrf instance MGMT
!
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
!
```

Then, configure access to eAPI:

```eos
!
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
  - host: 10.73.1.105
```

## Test Catalog

To test your network, it is important to define a test catalog to list all the tests to run against your inventory. Test catalog references python functions into a yaml file. This file can be loaded by anta.loader.py

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
  --tags TAGS           List of device tags to limit scope of testing
  --list                Display internal data
  --json                Display data in json format
  --table               Result represented in tables
  --save SAVE           Save output to file. Only valid for --list and --json
  --all-results         Display all test cases results. Default table view (Only valid with --table)
  --by-host             Provides summary of test results per device (Only valid with --table)
  --by-test             Provides summary of test results per test case (Only valid with --table)
```

Default output is a table format listing all test results, and it can be changed to a report per test case or per host

### Default report

```bash
$ check-devices.py -i .personal/avd-lab.yml -c .personal/ceos-catalog.yml --table

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
$ check-devices.py -i .personal/avd-lab.yml -c .personal/ceos-catalog.yml --table --by-test --test verify_mlag_status

                                              Summary per test case
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Test Case          ┃ # of success ┃ # of skipped ┃ # of failure ┃ # of errors ┃ List of failed or error nodes ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ verify_mlag_status │ 8            │ 13           │ 0            │ 0           │ []                            │
└────────────────────┴──────────────┴──────────────┴──────────────┴─────────────┴───────────────────────────────┘
```

### Report per host

```bash
$ check-devices.py -i .personal/avd-lab.yml -c .personal/ceos-catalog.yml --table --by-host --test verify_mlag_status --hostip 10.73.252.21

                                            Summary per host
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Host IP      ┃ # of success ┃ # of skipped ┃ # of failure ┃ # of errors ┃ List of failed ortest case ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 10.73.252.21 │ 0            │ 1            │ 0            │ 0           │ []                         │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────┴────────────────────────────┘
```

You can find more information under the __usage__ section of the website