# Get Inventory Information

ANTA CLI provides a set of entrypoints to get data from your local inventory.

## Get all configured tags

Since most commands in anta support tags filtering, this command helps you list all available tags configured in your inventory.

### Command overview

```bash
anta get tags --help
Usage: anta get tags [OPTIONS]

  Get list of configured tags in user inventory.

Options:
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --help                          Show this message and exit.
```

### Example

Let's consider the following inventory:

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

To get the list of all configured tags in your CLI, run the following command:

```bash
$ anta get tags
Tags found:
[
  "all",
  "fabric",
  "leaf",
  "spine"
]
None

* note that tag all has been added by anta
```

!!! tip Default tag
    As you can see, the tag `all` has been added even if not explicitely configued in your inventory. This tag is the default tag added to all your devices to run commands against your inventory when you do not provide any specific tag.

## List devices in inventory

### Command overview

To get a list of all devices available in your inventory with ANTA, use the following command

```bash
anta get inventory --help
Usage: anta get inventory [OPTIONS]

  Show inventory loaded in ANTA.

Options:
  -t, --tags TEXT                 List of tags using comma as separator:
                                  tag1,tag2,tag3
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --connected / --not-connected   Display inventory after connection has been
                                  created
  --help                          Show this message and exit.
```

It will give you all information loaded in ANTA inventory from your [inventory file](../../usage-inventory-catalog/).

!!! tip Offline information only
    By default only information not based on device connection is available. If you want to get information based on connection such as hardware model, you should use the `--connected` option.

### Example

Considering the following inventory file:

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

You can get ANTA inventory with the command:

```bash
$ anta --username ansible --password ansible get inventory --tags spine
Current inventory content is:
[
  {
    "name": "spine01",
    "host": "192.168.0.10",
    "username": "ansible",
    "password": "ansible",
    "port": "443",
    "enable_password": "None",
    "session": "<aioeapi.device.Device object at 0x7fa98d0a2d30>",
    "hw_model": "unset",
    "tags": "['fabric', 'spine', 'all']",
    "timeout": "10.0",
    "established": "False",
    "is_online": "False"
  },
  {
    "name": "spine02",
    "host": "192.168.0.11",
    "username": "ansible",
    "password": "ansible",
    "port": "443",
    "enable_password": "None",
    "session": "<aioeapi.device.Device object at 0x7fa98d0a2ac0>",
    "hw_model": "unset",
    "tags": "['fabric', 'spine', 'all']",
    "timeout": "10.0",
    "established": "False",
    "is_online": "False"
  }
]
None
```
