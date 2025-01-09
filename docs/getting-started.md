<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

This section shows how to use ANTA with basic configuration. All examples are based on Arista Test Drive (ATD) topology you can access by reaching out to your preferred SE.

## Installation

The easiest way to install ANTA package is to run Python (`>=3.9`) and its pip package to install:

```bash
pip install anta[cli]
```

For more details about how to install package, please see the [requirements and installation](./requirements-and-installation.md) section.

## Configure Arista EOS devices

For ANTA to be able to connect to your target devices, you need to configure your management interface

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

ANTA uses an inventory to list the target devices for the tests. You can create a file manually with this format:

```yaml
--8<-- "getting-started/inventory.yml"
```

> You can read more details about how to build your inventory [here](usage-inventory-catalog.md#device-inventory)

## Test Catalog

To test your network, ANTA relies on a test catalog to list all the tests to run against your inventory. A test catalog references python functions into a yaml file.

The structure to follow is like:

```yaml
<anta_tests_submodule>:
  - <anta_tests_submodule function name>:
      <test function option>:
        <test function option value>
```

> You can read more details about how to build your catalog [here](usage-inventory-catalog.md#test-catalog)

Here is an example for basic tests:

```yaml
--8<-- "getting-started/catalog.yml"
```

## Test your network

### CLI

ANTA comes with a generic CLI entrypoint to run tests in your network. It requires an inventory file as well as a test catalog.

This entrypoint has multiple options to manage test coverage and reporting.

```bash
--8<-- "anta_help.txt"
```

```bash
--8<-- "anta_nrfu_help.txt"
```

To run the NRFU, you need to select an output format amongst ["json", "table", "text", "tpl-report"]. For a first usage, `table` is recommended.  By default all test results for all devices are rendered but it can be changed to a report per test case or per host

!!! Note
    The following examples shows how to pass all the CLI options.

    See how to use environment variables instead in the [CLI overview](cli/overview.md#anta-environment-variables)

#### Default report using table

```bash
--8<-- "getting-started/anta_nrfu_table.sh"
--8<-- "getting-started/anta_nrfu_table.output"
```

#### Report in text mode

```bash
--8<-- "getting-started/anta_nrfu_text.sh"
--8<-- "getting-started/anta_nrfu_text.output"
```

#### Report in JSON format

```bash
--8<-- "getting-started/anta_nrfu_json.sh"
--8<-- "getting-started/anta_nrfu_json.output"
```

### Basic usage in a Python script

```python
--8<-- "anta_runner.py"
```
