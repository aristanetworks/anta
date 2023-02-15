# Getting Started

This section shows how to use ANTA with basic configuration. All examples are based on Arista Test Drive (ATD) topology you can access by reaching out to your prefered SE.

## Installation

The easiest way to intall ANTA package is to run Python (`>=3.8`) and its pip package to install:

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
interface Management0
   description oob_management
   vrf MGMT
   ip address 192.168.0.10/24
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
  - host: 192.168.0.10
    name: spine01
    tags: ['fabric', 'spine']
  - host: 192.168.0.11
    name: spine02
    tags: ['fabric', 'spine']
  - host: 192.168.0.12
    name: leaf01
    tags: ['fabric', 'leaf']
  - host: 192.168.0.13
    name: leaf02
    tags: ['fabric', 'leaf']
  - host: 192.168.0.14
    name: leaf03
    tags: ['fabric', 'leaf']
  - host: 192.168.0.15
    name: leaf04
    tags: ['fabric', 'leaf']
```

> You can read more details about how to build your inventory [here](../usage-inventory-catalog/#create-an-inventory-file)

## Test Catalog

To test your network, it is important to define a test catalog to list all the tests to run against your inventory. Test catalog references python functions into a yaml file. This file can be loaded by anta.loader.py

The structure to follow is like:

```yaml
<anta_tests_submodule>:
  - <anta_tests_submodule function name>:
      <test function option>:
        <test function option value>
```

> You can read more details about how to build your catalog [here](../usage-inventory-catalog/#test-catalog)

Here is an example for basic things:

```yaml
# Load anta.tests.software
anta.tests.software:
  - verify_eos_version: # Verifies the device is running one of the allowed EOS version.
      versions: # List of allowed EOS versions.
        - 4.25.4M
        - 4.26.1F
        - '4.28.3M-28837868.4283M (engineering build)'
  - verify_terminattr_version:
      versions:
        - v1.22.1

anta.tests.system:
  - verify_uptime: # Verifies the device uptime is higher than a value.
      minimum: 1
  - verify_ntp:
  - verify_syslog:

anta.tests.mlag:
  - verify_mlag_status:
  - verify_mlag_interfaces:
  - verify_mlag_config_sanity:

anta.tests.configuration:
  - verify_zerotouch: # Verifies ZeroTouch is disabled.
  - verify_running_config_diffs:
```

## Test your network

To test EOS devices, this package comes with a generic script to run tests in your network. It requires an inventory file as well as a test catalog.

This script has multiple options to manage test coverage and reporting.

```bash
# Generic ANTA options
$ anta
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test CLI

Options:
  --version               Show the version and exit.
  --username TEXT         Username to connect to EOS  [env var: ANTA_USERNAME;
                          required]
  --password TEXT         Password to connect to EOS  [env var: ANTA_PASSWORD;
                          required]
  --timeout INTEGER       Connection timeout (default 5)  [env var:
                          ANTA_TIMEOUT]
  --enable-password TEXT  Enable password if required to connect  [env var:
                          ANTA_ENABLE_PASSWORD]
  -i, --inventory PATH    Path to your inventory file  [env var:
                          ANTA_INVENTORY; required]
  --help                  Show this message and exit.

Commands:
  exec  Execute commands to inventory devices
  get   Get data from/to ANTA
  nrfu  Run NRFU against inventory devices



# NRFU part of ANTA
$ anta nrfu
Usage: anta nrfu [OPTIONS] COMMAND [ARGS]...

  Run NRFU against inventory devices

Options:
  --help  Show this message and exit.

Commands:
  json   ANTA command to check network state with JSON result
  table  ANTA command to check network states with table result
  text   ANTA command to check network states with text result
```

Default output is a table format listing all test results, and it can be changed to a report per test case or per host

### Default report using table

```bash
anta \
    --username tom \
    --password arista123 \
    --enable-password t \
    --inventory .personal/inventory_atd.yml \
    nrfu table --tags leaf --catalog .personal/tests-bases.yml

╭──────────────────────── Settings ────────────────────────╮
│ Running check-devices with:                              │
│               - Inventory: .personal/inventory_atd.yml   │
│               - Tests catalog: .personal/tests-bases.yml │
╰──────────────────────────────────────────────────────────╯
                                                                            All tests results
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Device IP ┃ Test Name                          ┃ Test Status ┃ Message(s)                                                     ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ leaf01    │ verify_eos_version                 │ success     │                                                                │
│ leaf01    │ verify_terminattr_version          │ success     │                                                                │
│ leaf01    │ verify_uptime                      │ success     │                                                                │
│ leaf01    │ verify_ntp                         │ failure     │ not sync with NTP server (NTP is disabled.)                    │
│ leaf01    │ verify_syslog                      │ failure     │ Device has some log messages with a severity WARNING or higher │
└───────────┴────────────────────────────────────┴─────────────┴────────────────────────────────────────────────────────────────┘
```

### Report in text mode

```
$ anta \
    --username tom \
    --password arista123 \
    --enable-password t \
    --inventory .personal/inventory_atd.yml \
    nrfu text --tags leaf --catalog .personal/tests-bases.yml

leaf01 :: verify_eos_version :: SUCCESS
leaf01 :: verify_terminattr_version :: SUCCESS
leaf01 :: verify_uptime :: SUCCESS
leaf01 :: verify_ntp :: FAILURE (not sync with NTP server (NTP is disabled.))
leaf01 :: verify_syslog :: FAILURE (Device has some log messages with a severity WARNING or higher)
leaf01 :: verify_mlag_status :: SUCCESS
leaf01 :: verify_mlag_interfaces :: SUCCESS
leaf01 :: verify_mlag_config_sanity :: SUCCESS
leaf01 :: verify_zerotouch :: SUCCESS
leaf01 :: verify_running_config_diffs :: SUCCESS
leaf01 :: verify_interface_utilization :: SUCCESS
leaf01 :: verify_interface_errors :: SUCCESS
leaf01 :: verify_interface_discards :: SUCCESS
leaf01 :: verify_interface_errdisabled :: SUCCESS
leaf01 :: verify_interfaces_status :: SUCCESS
leaf01 :: verify_storm_control_drops :: SKIPPED (verify_storm_control_drops test is not supported on cEOSLab.)
...
```

### Report per host

```bash
$ anta \
    --username tom \
    --password arista123 \
    --enable-password t \
    --inventory .personal/inventory_atd.yml \
    nrfu json --tags leaf --catalog .personal/tests-bases.yml

╭──────────────────────────────────────────────────────────────────────────────╮
│ JSON results of all tests                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
[
  {
    "name": "leaf01",
    "test": "verify_eos_version",
    "result": "success",
    "messages": "[]"
  },
  {
    "name": "leaf01",
    "test": "verify_terminattr_version",
    "result": "success",
    "messages": "[]"
  },
...
]
```

You can find more information under the __usage__ section of the website
