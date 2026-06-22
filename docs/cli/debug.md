---
anta_title: ANTA debug commands
---
<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The ANTA CLI includes a set of debugging tools, making it easier to build and test ANTA content. This functionality is accessed via the `debug` subcommand and offers the following options:

- Executing a command on a device from your inventory and retrieving the result.
- Running a templated command on a device from your inventory and retrieving the result.

These tools are especially helpful in building the tests, as they give a visual access to the output received from the eAPI. They also facilitate the extraction of output content for use in unit tests, as described in our [contribution guide](../contribution.md).

!!! warning
    The `debug` tools require a device from your inventory. Thus, you must use a valid [ANTA Inventory](../usage-inventory-catalog.md#device-inventory).

## DEBUG command overview

```bash
--8<-- "anta_debug_help.txt"
```

## Executing an EOS command

You can use the `run-cmd` entrypoint to run a command, which includes the following options:

### Command overview

```bash
--8<-- "anta_debug_runcmd_help.txt"
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
--8<-- "anta_debug_runtemplate_help.txt"
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
