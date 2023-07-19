# ANTA debug commands

The ANTA CLI includes a set of debugging tools, making it easier to build and test ANTA content. This functionality is accessed via the `debug` subcommand and offers the following options:

- Executing a command on a device from your inventory and retrieving the result.
- Running a templated command on a device from your inventory and retrieving the result.

These tools are especially helpful in building the tests, as they give a visual access to the output received from the eAPI. They also facilitate the extraction of output content for use in unit tests, as described in our [contribution guide](../contribution.md).

!!! warning
    The `debug` tools require a device from your inventory. Thus, you MUST use a valid [ANTA Inventory](../usage-inventory-catalog.md#create-an-inventory-file).

## Executing an EOS command

You can use the `run-cmd` entrypoint to run a command, which includes the following options:

### Command overview

```bash
$ anta debug run-cmd --help
Usage: anta debug run-cmd [OPTIONS]

  Run arbitrary command to an ANTA device

Options:
  -c, --command TEXT        Command to run  [required]
  --ofmt [json|text]        EOS eAPI format to use. can be text or json
  -v, --version [1|latest]  EOS eAPI version
  -r, --revision INTEGER    eAPI command revision
  -d, --device TEXT         Device from inventory to use  [required]
  --help                    Show this message and exit.
```

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
$ anta debug run-template --help
Usage: anta debug run-template [OPTIONS] PARAMS...

  Run arbitrary templated command to an ANTA device.

  Takes a list of arguments (keys followed by a value) to build a dictionary
  used as template parameters. Example:

  anta debug run-template -d leaf1a -t 'show vlan {vlan_id}' vlan_id 1

Options:
  -t, --template TEXT       Command template to run. E.g. 'show vlan
                            {vlan_id}'  [required]
  --ofmt [json|text]        EOS eAPI format to use. can be text or json
  -v, --version [1|latest]  EOS eAPI version
  -r, --revision INTEGER    eAPI command revision
  -d, --device TEXT         Device from inventory to use  [required]
  --help                    Show this message and exit.
```

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
!!! warning
    If multiple arguments of the same key are provided, only the last argument value will be kept in the template parameters.

### Example of multiple arguments

```bash
anta --log DEBUG debug run-template --template "ping {dst} source {src}" dst "8.8.8.8" src Loopback0 --device DC1-SPINE1    
> {'dst': '8.8.8.8', 'src': 'Loopback0'}

anta --log DEBUG debug run-template --template "ping {dst} source {src}" dst "8.8.8.8" src Loopback0 dst "1.1.1.1" src Loopback1 --device DC1-SPINE1           
> {'dst': '1.1.1.1', 'src': 'Loopback1'}
# Notice how `src` and `dst` keep only the latest value
```
