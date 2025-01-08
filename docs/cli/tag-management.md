<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA uses tags to define test-to-device mappings (tests run on devices with matching tags) and the `--tags` CLI option acts as a filter to execute specific test/device combinations.

## Defining tags

### Device tags

Device tags can be defined in the inventory:

```yaml
anta_inventory:
  hosts:
    - name: leaf1
      host: leaf1.anta.arista.com
      tags: ["leaf"]
    - name: leaf2
      host: leaf2.anta.arista.com
      tags: ["leaf"]
    - name: spine1
      host: spine1.anta.arista.com
      tags: ["spine"]
```

Each device also has its own name automatically added as a tag:

```bash
$ anta get inventory
Current inventory content is:
{
    'leaf1': AsyncEOSDevice(
        name='leaf1',
        tags={'leaf', 'leaf1'},  <--
        [...]
        host='leaf1.anta.arista.com',
        [...]
    ),
    'leaf2': AsyncEOSDevice(
        name='leaf2',
        tags={'leaf', 'leaf2'},  <--
        [...]
        host='leaf2.anta.arista.com',
        [...]
    ),
    'spine1': AsyncEOSDevice(
        name='spine1',
        tags={'spine1', 'spine'},  <--
        [...]
        host='spine1.anta.arista.com',
        [...]
    )
}
```

### Test tags

Tags can be defined in the test catalog to restrict tests to tagged devices:

```yaml
anta.tests.system:
  - VerifyUptime:
      minimum: 10
      filters:
        tags: ['spine']
  - VerifyUptime:
      minimum: 9
      filters:
        tags: ['leaf']
  - VerifyReloadCause:
      filters:
        tags: ['spine', 'leaf']
  - VerifyCoredump:
  - VerifyAgentLogs:
  - VerifyCPUUtilization:
  - VerifyMemoryUtilization:
  - VerifyFileSystemUtilization:
  - VerifyNTP:

anta.tests.mlag:
  - VerifyMlagStatus:
      filters:
        tags: ['leaf']

anta.tests.interfaces:
  - VerifyL3MTU:
      mtu: 1500
      filters:
        tags: ['spine']
```

> [!TIP]
>
> - A tag used to filter a test can also be a device name
>
> - **Use different input values for a specific test**: Leverage tags to define different input values for a specific test. See the `VerifyUptime` example above.

## Using tags

| Command | Description |
| ------- | ----------- |
| No `--tags` option | Run all tests on all devices according to the `tag` definitions in your inventory and test catalog.<br/> Tests without tags are executed on all devices. |
| `--tags leaf` | Run all tests marked with the `leaf` tag on all devices configured with the `leaf` tag.<br/> All other tests are ignored. |
| `--tags leaf,spine` | Run all tests marked with the `leaf` tag on all devices configured with the `leaf` tag.<br/>Run all tests marked with the `spine` tag on all devices configured with the `spine` tag.<br/> All other tests are ignored. |

### Examples

The following examples use the inventory and test catalog defined above.

#### No `--tags` option

Tests without tags are run on all devices.
Tests with tags will only run on devices with matching tags.

```bash
$ anta nrfu table --group-by device
╭────────────────────── Settings ──────────────────────╮
│ - ANTA Inventory contains 3 devices (AsyncEOSDevice) │
│ - Tests catalog contains 11 tests                    │
╰──────────────────────────────────────────────────────╯

--- ANTA NRFU Run Information ---
Number of devices: 3 (3 established)
Total number of selected tests: 27
---------------------------------
                                            Summary per device
┏━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Device ┃ # of success ┃ # of skipped ┃ # of failure ┃ # of errors ┃ List of failed or error test cases ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ leaf1  │ 9            │ 0            │ 0            │ 0           │                                    │
├────────┼──────────────┼──────────────┼──────────────┼─────────────┼────────────────────────────────────┤
│ leaf2  │ 7            │ 1            │ 1            │ 0           │ VerifyAgentLogs                    │
├────────┼──────────────┼──────────────┼──────────────┼─────────────┼────────────────────────────────────┤
│ spine1 │ 9            │ 0            │ 0            │ 0           │                                    │
└────────┴──────────────┴──────────────┴──────────────┴─────────────┴────────────────────────────────────┘
```

#### Single tag

With a tag specified, only tests matching this tag will be run on matching devices.

```bash
$ anta nrfu --tags leaf text
╭────────────────────── Settings ──────────────────────╮
│ - ANTA Inventory contains 3 devices (AsyncEOSDevice) │
│ - Tests catalog contains 11 tests                    │
╰──────────────────────────────────────────────────────╯

--- ANTA NRFU Run Information ---
Number of devices: 3 (2 established)
Total number of selected tests: 6
---------------------------------

leaf1 :: VerifyReloadCause :: SUCCESS
leaf1 :: VerifyUptime :: SUCCESS
leaf1 :: VerifyMlagStatus :: SUCCESS
leaf2 :: VerifyReloadCause :: SUCCESS
leaf2 :: VerifyUptime :: SUCCESS
leaf2 :: VerifyMlagStatus :: SKIPPED (MLAG is disabled)
```

In this case, only `leaf` devices defined in the inventory are used to run tests marked with the `leaf` in the test catalog.

#### Multiple tags

It is possible to use multiple tags using the `--tags tag1,tag2` syntax.

```bash
$ anta nrfu --tags leaf,spine text
╭────────────────────── Settings ──────────────────────╮
│ - ANTA Inventory contains 3 devices (AsyncEOSDevice) │
│ - Tests catalog contains 11 tests                    │
╰──────────────────────────────────────────────────────╯

--- ANTA NRFU Run Information ---
Number of devices: 3 (3 established)
Total number of selected tests: 15
---------------------------------

leaf1 :: VerifyReloadCause :: SUCCESS
leaf1 :: VerifyMlagStatus :: SUCCESS
leaf1 :: VerifyUptime :: SUCCESS
leaf1 :: VerifyL3MTU :: SUCCESS
leaf1 :: VerifyUptime :: SUCCESS
leaf2 :: VerifyReloadCause :: SUCCESS
leaf2 :: VerifyMlagStatus :: SKIPPED (MLAG is disabled)
leaf2 :: VerifyUptime :: SUCCESS
leaf2 :: VerifyL3MTU :: SUCCESS
leaf2 :: VerifyUptime :: SUCCESS
spine1 :: VerifyReloadCause :: SUCCESS
spine1 :: VerifyMlagStatus :: SUCCESS
spine1 :: VerifyUptime :: SUCCESS
spine1 :: VerifyL3MTU :: SUCCESS
spine1 :: VerifyUptime :: SUCCESS
```

## Obtaining all configured tags

As most ANTA commands accommodate tag filtering, this command is useful for enumerating all tags configured in the inventory. Running the `anta get tags` command will return a list of all tags configured in the inventory.

### Command overview

```bash
Usage: anta get tags [OPTIONS]

  Get list of configured tags in user inventory.

Options:
  -u, --username TEXT     Username to connect to EOS  [env var: ANTA_USERNAME;
                          required]
  -p, --password TEXT     Password to connect to EOS that must be provided. It
                          can be prompted using '--prompt' option.  [env var:
                          ANTA_PASSWORD]
  --enable-password TEXT  Password to access EOS Privileged EXEC mode. It can
                          be prompted using '--prompt' option. Requires '--
                          enable' option.  [env var: ANTA_ENABLE_PASSWORD]
  --enable                Some commands may require EOS Privileged EXEC mode.
                          This option tries to access this mode before sending
                          a command to the device.  [env var: ANTA_ENABLE]
  -P, --prompt            Prompt for passwords if they are not provided.  [env
                          var: ANTA_PROMPT]
  --timeout FLOAT         Global API timeout. This value will be used for all
                          devices.  [env var: ANTA_TIMEOUT; default: 30.0]
  --insecure              Disable SSH Host Key validation.  [env var:
                          ANTA_INSECURE]
  --disable-cache         Disable cache globally.  [env var:
                          ANTA_DISABLE_CACHE]
  -i, --inventory FILE    Path to the inventory YAML file.  [env var:
                          ANTA_INVENTORY; required]
  --tags TEXT             List of tags using comma as separator:
                          tag1,tag2,tag3.  [env var: ANTA_TAGS]
  --help                  Show this message and exit.
```

### Example

To get the list of all configured tags in the inventory, run the following command:

```bash
$ anta get tags
Tags found:
[
  "leaf",
  "leaf1",
  "leaf2",
  "spine",
  "spine1"
]
```
