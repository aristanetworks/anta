<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Tag management

## Overview

ANTA comes with tag option. This approach helps user to run a set of tests on devices marked with same tag. So you can run tests dedicated to leaf devices on your leaf device only and not on other devices.

Tags are string defined by the user and can be anything consider as a string by Python. A [default one](#default-tags) is present for all tests and devices.

The next table provides a short summary of the scope of tags using CLI

| Command | Description |
| ------- | ----------- |
| `none` | Run all tests on all devices according `tag` definition in your inventory and tests catalog. And tests with no tag are executed on all devices|
| `--tags leaf` | Run all tests marked with `leaf` tag on all devices configured with `leaf` tag.<br/> All other tags are ignored |
| `--tags leaf,spine` | Run all tests marked with `leaf` tag on all devices configured with `leaf` tag.<br/>Run all tests marked with `spine` tag on all devices configured with `spine` tag.<br/> All other tags are ignored |

## Inventory and Catalog for tests

All commands in this page are based on the following inventory and tests catalog.

=== "Inventory"

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
        tags: ['fabric', 'leaf'
    ```

=== "Tests Catalog"

    ```yaml
    anta.tests.system:
      - VerifyUptime:
          minimum: 10
          filters:
            tags: ['fabric']
      - VerifyReloadCause:
          tags: ['leaf', spine']
      - VerifyCoredump:
      - VerifyAgentLogs:
      - VerifyCPUUtilization:
          filters:
            tags: ['spine', 'leaf']
      - VerifyMemoryUtilization:
      - VerifyFileSystemUtilization:
      - VerifyNTP:

    anta.tests.mlag:
      - VerifyMlagStatus:


    anta.tests.interfaces:
      - VerifyL3MTU:
          mtu: 1500
          filters:
            tags: ['demo']
    ```

## Default tags

By default, ANTA uses a default tag for both devices and tests. This default tag is `all` and it can be explicit if you want to make it visible in your inventory and also implicit since the framework injects this tag if it is not defined.

So this command will run all tests from your catalog on all devices. With a mapping for `tags` defined in your inventory and catalog. If no `tags` configured, then tests are executed against all devices.

```bash
$ anta nrfu -c .personal/catalog-class.yml table --group-by device

╭────────────────────── Settings ──────────────────────╮
│ Running ANTA tests:                                  │
│ - ANTA Inventory contains 6 devices (AsyncEOSDevice) │
│ - Tests catalog contains 10 tests                    │
╰──────────────────────────────────────────────────────╯

┏━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Device  ┃ # of success ┃ # of skipped ┃ # of failure ┃ # of errors ┃ List of failed or error test cases ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ spine01 │ 5            │ 1            │ 1            │ 0           │ ['VerifyCPUUtilization']           │
│ spine02 │ 5            │ 1            │ 1            │ 0           │ ['VerifyCPUUtilization']           │
│ leaf01  │ 6            │ 0            │ 1            │ 0           │ ['VerifyCPUUtilization']           │
│ leaf02  │ 6            │ 0            │ 1            │ 0           │ ['VerifyCPUUtilization']           │
│ leaf03  │ 6            │ 0            │ 1            │ 0           │ ['VerifyCPUUtilization']           │
│ leaf04  │ 6            │ 0            │ 1            │ 0           │ ['VerifyCPUUtilization']           │
└─────────┴──────────────┴──────────────┴──────────────┴─────────────┴────────────────────────────────────┘
```

## Use a single tag in CLI

The most used approach is to use a single tag in your CLI to filter tests & devices configured with this one.

In such scenario, ANTA will run tests marked with `$tag` only on devices marked with `$tag`. All other tests and devices will be ignored

```bash
$ anta nrfu -c .personal/catalog-class.yml text --tags leaf
╭────────────────────── Settings ──────────────────────╮
│ Running ANTA tests:                                  │
│ - ANTA Inventory contains 6 devices (AsyncEOSDevice) │
│ - Tests catalog contains 10 tests                    │
╰──────────────────────────────────────────────────────╯

leaf01 :: VerifyUptime :: SUCCESS
leaf01 :: VerifyReloadCause :: SUCCESS
leaf01 :: VerifyCPUUtilization :: SUCCESS
leaf02 :: VerifyUptime :: SUCCESS
leaf02 :: VerifyReloadCause :: SUCCESS
leaf02 :: VerifyCPUUtilization :: SUCCESS
leaf03 :: VerifyUptime :: SUCCESS
leaf03 :: VerifyReloadCause :: SUCCESS
leaf03 :: VerifyCPUUtilization :: SUCCESS
leaf04 :: VerifyUptime :: SUCCESS
leaf04 :: VerifyReloadCause :: SUCCESS
leaf04 :: VerifyCPUUtilization :: SUCCESS
```

In this case, only `leaf` devices defined in your [inventory](#inventory-and-catalog-for-tests) are used to run tests marked with `leaf` in your [tests catalog](#inventory-and-catalog-for-tests)

## Use multiple tags in CLI

A more advanced usage of the tag feature is to list multiple tags in your CLI using `--tags $tag1,$tag2` syntax.

In such scenario, all devices marked with `$tag1` will be selected and ANTA will run tests with `$tag1`, then devices with `$tag2` will be selected and will be tested with tests marked with `$tag2`

```bash
anta nrfu -c .personal/catalog-class.yml text --tags leaf,fabric

spine01 :: VerifyUptime :: SUCCESS
spine02 :: VerifyUptime :: SUCCESS
leaf01 :: VerifyUptime :: SUCCESS
leaf01 :: VerifyReloadCause :: SUCCESS
leaf01 :: VerifyCPUUtilization :: SUCCESS
leaf02 :: VerifyUptime :: SUCCESS
leaf02 :: VerifyReloadCause :: SUCCESS
leaf02 :: VerifyCPUUtilization :: SUCCESS
leaf03 :: VerifyUptime :: SUCCESS
leaf03 :: VerifyReloadCause :: SUCCESS
leaf03 :: VerifyCPUUtilization :: SUCCESS
leaf04 :: VerifyUptime :: SUCCESS
leaf04 :: VerifyReloadCause :: SUCCESS
leaf04 :: VerifyCPUUtilization :: SUCCESS
```
