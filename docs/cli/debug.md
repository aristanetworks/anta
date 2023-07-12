# ANTA debug commands

ANTA CLI also provides a set of entrypoints to help building ANTA content. We call it `debug` and it provides different options:

- Run a command on a device from your inventory and expose the result.
- Run a templated command on a device from your inventory and expose the result.

Both are extremly useful to build your tests since you have a visual access to the output you receive from the eAPI. It also help extracting output content to be used by the unit tests, as described in our [contribution guide](../contribution.md).

!!! warning "Use your inventory"
    Because `debug` is based on a device from your inventory, you MUST use a valid [ANTA Inventory](../usage-inventory-catalog.md#create-an-inventory-file).

## Get the result of an EOS command

To run a command, you can leverage the `run-cmd` entrypoint with the following options:

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

In practice, this command is very simple to use. Here is an example using `show interfaces description` with a `JSON` format:

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

## Get the result of an EOS command using templates

The `run-template` entrypoint allows the user to provide an [`f-string`](https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python) templated command followed by a list of arguments (key followed by a value) to build a dictionary used as template parameters.

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

Here is `run-template` in action using `show vlan {vlan_id}` with a `JSON` format:

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
