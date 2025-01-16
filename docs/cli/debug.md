---
anta_title: ANTA debug commands
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The ANTA CLI includes a set of debugging tools, making it easier to build and test ANTA content. This functionality is accessed via the `debug` subcommand and offers the following options:

- Executing a command on a device from your inventory and retrieving the result.
- Running a templated command on a device from your inventory and retrieving the result.

These tools are especially helpful in building the tests, as they give a visual access to the output received from the eAPI. They also facilitate the extraction of output content for use in unit tests, as described in our [contribution guide](../contribution.md).

!!! warning
    The `debug` tools require a device from your inventory. Thus, you must use a valid [ANTA Inventory](../usage-inventory-catalog.md#device-inventory).

## Executing an EOS command

You can use the `run-cmd` entrypoint to run a command, which includes the following options:

### Command overview

```bash
Usage: anta debug run-cmd [OPTIONS]

  Run arbitrary command to an ANTA device.

Options:
  -u, --username TEXT       Username to connect to EOS  [env var:
                            ANTA_USERNAME; required]
  -p, --password TEXT       Password to connect to EOS that must be provided.
                            It can be prompted using '--prompt' option.  [env
                            var: ANTA_PASSWORD]
  --enable-password TEXT    Password to access EOS Privileged EXEC mode. It
                            can be prompted using '--prompt' option. Requires
                            '--enable' option.  [env var:
                            ANTA_ENABLE_PASSWORD]
  --enable                  Some commands may require EOS Privileged EXEC
                            mode. This option tries to access this mode before
                            sending a command to the device.  [env var:
                            ANTA_ENABLE]
  -P, --prompt              Prompt for passwords if they are not provided.
                            [env var: ANTA_PROMPT]
  --timeout FLOAT           Global API timeout. This value will be used for
                            all devices.  [env var: ANTA_TIMEOUT; default:
                            30.0]
  --insecure                Disable SSH Host Key validation.  [env var:
                            ANTA_INSECURE]
  --disable-cache           Disable cache globally.  [env var:
                            ANTA_DISABLE_CACHE]
  -i, --inventory FILE      Path to the inventory YAML file.  [env var:
                            ANTA_INVENTORY; required]
  --ofmt [json|text]        EOS eAPI format to use. can be text or json
  -v, --version [1|latest]  EOS eAPI version
  -r, --revision INTEGER    eAPI command revision
  -d, --device TEXT         Device from inventory to use  [required]
  -c, --command TEXT        Command to run  [required]
  --help                    Show this message and exit.
```

> [!TIP]
> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

### Example

This example illustrates how to run the `show interfaces description` command with a `JSON` format (default):

```bash
anta debug run-cmd --command "show interfaces description" --device DC1-SPINE1
Run command show interfaces description on DC1-SPINE1
{
    'interfaceDescriptions': {
        'Ethernet1': {'lineProtocolStatus': 'up', 'description': 'P2P_LINK_TO_DC1-LEAF1A_Ethernet1', 'interfaceStatus': 'up'},
        'Ethernet2': {'lineProtocolStatus': 'up', 'description': 'P2P_LINK_TO_DC1-LEAF1B_Ethernet1', 'interfaceStatus': 'up'},
        'Ethernet3': {'lineProtocolStatus': 'up', 'description': 'P2P_LINK_TO_DC1-BL1_Ethernet1', 'interfaceStatus': 'up'},
        'Ethernet4': {'lineProtocolStatus': 'up', 'description': 'P2P_LINK_TO_DC1-BL2_Ethernet1', 'interfaceStatus': 'up'},
        'Loopback0': {'lineProtocolStatus': 'up', 'description': 'EVPN_Overlay_Peering', 'interfaceStatus': 'up'},
        'Management0': {'lineProtocolStatus': 'up', 'description': 'oob_management', 'interfaceStatus': 'up'}
    }
}
```

## Executing an EOS command using templates

The `run-template` entrypoint allows the user to provide an [`f-string`](https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python) templated command. It is followed by a list of arguments (key-value pairs) that build a dictionary used as template parameters.

### Command overview

```bash
Usage: anta debug run-template [OPTIONS] PARAMS...

  Run arbitrary templated command to an ANTA device.

  Takes a list of arguments (keys followed by a value) to build a dictionary
  used as template parameters.

  Example
  -------
      anta debug run-template -d leaf1a -t 'show vlan {vlan_id}' vlan_id 1

Options:
  -u, --username TEXT       Username to connect to EOS  [env var:
                            ANTA_USERNAME; required]
  -p, --password TEXT       Password to connect to EOS that must be provided.
                            It can be prompted using '--prompt' option.  [env
                            var: ANTA_PASSWORD]
  --enable-password TEXT    Password to access EOS Privileged EXEC mode. It
                            can be prompted using '--prompt' option. Requires
                            '--enable' option.  [env var:
                            ANTA_ENABLE_PASSWORD]
  --enable                  Some commands may require EOS Privileged EXEC
                            mode. This option tries to access this mode before
                            sending a command to the device.  [env var:
                            ANTA_ENABLE]
  -P, --prompt              Prompt for passwords if they are not provided.
                            [env var: ANTA_PROMPT]
  --timeout FLOAT           Global API timeout. This value will be used for
                            all devices.  [env var: ANTA_TIMEOUT; default:
                            30.0]
  --insecure                Disable SSH Host Key validation.  [env var:
                            ANTA_INSECURE]
  --disable-cache           Disable cache globally.  [env var:
                            ANTA_DISABLE_CACHE]
  -i, --inventory FILE      Path to the inventory YAML file.  [env var:
                            ANTA_INVENTORY; required]
  --ofmt [json|text]        EOS eAPI format to use. can be text or json
  -v, --version [1|latest]  EOS eAPI version
  -r, --revision INTEGER    eAPI command revision
  -d, --device TEXT         Device from inventory to use  [required]
  -t, --template TEXT       Command template to run. E.g. 'show vlan
                            {vlan_id}'  [required]
  --help                    Show this message and exit.
```

> `username`, `password`, `enable-password`, `enable`, `timeout` and `insecure` values are the same for all devices

### Example

This example uses the `show vlan {vlan_id}` command in a `JSON` format:

```bash
anta debug run-template --template "show vlan {vlan_id}" vlan_id 10 --device DC1-LEAF1A
Run templated command 'show vlan {vlan_id}' with {'vlan_id': '10'} on DC1-LEAF1A
{
    'vlans': {
        '10': {
            'name': 'VRFPROD_VLAN10',
            'dynamic': False,
            'status': 'active',
            'interfaces': {
                'Cpu': {'privatePromoted': False, 'blocked': None},
                'Port-Channel11': {'privatePromoted': False, 'blocked': None},
                'Vxlan1': {'privatePromoted': False, 'blocked': None}
            }
        }
    },
    'sourceDetail': ''
}
```

### Example of multiple arguments

> [!WARNING]
> If multiple arguments of the same key are provided, only the last argument value will be kept in the template parameters.

```bash
anta -log DEBUG debug run-template --template "ping {dst} source {src}" dst "8.8.8.8" src Loopback0 --device DC1-SPINE1    
> {'dst': '8.8.8.8', 'src': 'Loopback0'}

anta -log DEBUG debug run-template --template "ping {dst} source {src}" dst "8.8.8.8" src Loopback0 dst "1.1.1.1" src Loopback1 --device DC1-SPINE1          
> {'dst': '1.1.1.1', 'src': 'Loopback1'}
# Notice how `src` and `dst` keep only the latest value
```
