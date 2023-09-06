<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Inventory and Catalog definition

This page describes how to create an inventory and a tests catalog.

## Create an inventory file

`anta` cli needs an inventory file to list all devices to tests. This inventory is a YAML file with the folowing keys:

```yaml
anta_inventory:
  hosts:
    - host: < ip address value >
      port: < TCP port for eAPI. Default is 443 (Optional)>
      name: < name to display in report. Default is host:port (Optional) >
      tags: < list of tags to use to filter inventory during tests. Default is ['all']. (Optional) >
  networks:
    - network: < network using CIDR notation >
      tags: < list of tags to use to filter inventory during tests. Default is ['all']. (Optional) >
  ranges:
    - start: < first ip address value of the range >
      end: < last ip address value of the range >
      tags: < list of tags to use to filter inventory during tests. Default is ['all']. (Optional) >
```

Your inventory file can be based on any of these 3 keys and MUST start with `anta_inventory` key. A full description of the inventory model is available in [API documentation](../api/inventory.models.input/)

An inventory example:

```yaml
---
anta_inventory:
  hosts:
  - host: 192.168.0.10
    name: spine01
    tags: ['fabric', 'spine']
  - host: 192.168.0.11
    name: spine02
    tags: ['fabric', 'spine']
  networks:
  - network: '192.168.110.0/24'
    tags: ['fabric', 'leaf']
  ranges:
  - start: 10.0.0.9
    end: 10.0.0.11
    tags: ['fabric', 'l2leaf']
```

## Test Catalog

In addition to your inventory file, you also have to define a catalog of tests to execute against all your devices. This catalog list all your tests and their parameters.
Its format is a YAML file and keys are tests functions inherited from the python path.

### Default tests catalog

All tests are located under `anta.tests` module and are categorised per family (one submodule). So to run test for software version, you can do:

```yaml
anta.tests.software:
  - VerifyEosVersion:
```

It will load the test `VerifyEosVersion` located in `anta.tests.software`. But since this function has parameters, we will create a catalog with the following structure:

```yaml
anta.tests.software:
  - VerifyEosVersion:
      # List of allowed EOS versions.
      versions:
        - 4.25.4M
        - 4.26.1F
```

To get a list of all available tests and their respective parameters, you can read the [tests section](./api/tests.md) of this website.

The following example gives a very minimal tests catalog you can use in almost any situation

```yaml
---
# Load anta.tests.software
anta.tests.software:
  # Verifies the device is running one of the allowed EOS version.
  - VerifyEosVersion:
      # List of allowed EOS versions.
      versions:
        - 4.25.4M
        - 4.26.1F

# Load anta.tests.system
anta.tests.system:
  # Verifies the device uptime is higher than a value.
  - VerifyUptime:
      minimum: 1

# Load anta.tests.configuration
anta.tests.configuration:
  # Verifies ZeroTouch is disabled.
  - VerifyZeroTouch:
  - VerifyRunningConfigDiffs:
```

### Custom tests catalog

In case you want to leverage your own tests collection, you can use the following syntax:

```yaml
<your package name>:
  - <your test in your package name>:
```

So for instance, it could be:

```yaml
titom73.tests.system:
  - VerifyPlatform:
    type: ['cEOS-LAB']
```

!!! tip "How to create custom tests"
    To create your custom tests, you should refer to this [following documentation](advanced_usages/as-python-lib.md)

### Customize test description and categories

It might be interesting to use your own categories and customized test description to build a better report for your environment. ANTA comes with a handy feature to define your own `categories` and `description` in the report.

In your test catalog, use `result_overwrite` dictionary with `categories` and `description` to just overwrite this values in your report:

```yaml
anta.tests.configuration:
  - VerifyZeroTouch: # Verifies ZeroTouch is disabled.
      result_overwrite:
        categories: ['demo', 'pr296']
        description: A custom test
  - VerifyRunningConfigDiffs:
anta.tests.interfaces:
  - VerifyInterfaceUtilization:
```

Once you run `anta nrfu table`, you will see following output:

```bash
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Device IP ┃ Test Name                  ┃ Test Status ┃ Message(s) ┃ Test description                              ┃ Test category ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ spine01   │ VerifyZeroTouch            │ success     │            │ A custom test                                 │ demo, pr296   │
│ spine01   │ VerifyRunningConfigDiffs   │ success     │            │                                               │ configuration │
│ spine01   │ VerifyInterfaceUtilization │ success     │            │ Verifies interfaces utilization is below 75%. │ interfaces    │
└───────────┴────────────────────────────┴─────────────┴────────────┴───────────────────────────────────────────────┴───────────────┘
```
