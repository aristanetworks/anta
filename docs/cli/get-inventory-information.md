# Retrieving Inventory Information

The ANTA CLI offers multiple entry points to access data from your local inventory.

## Obtaining all configured tags

As most of ANTA's commands accommodate tag filtering, this particular command is useful for enumerating all tags configured in your inventory. Running the `anta get tags` command will return a list of all tags that have been configured in your inventory.

### Command overview

```bash
anta get tags --help
Usage: anta get tags [OPTIONS]

  Get list of configured tags in user inventory.

Options:
  --help  Show this message and exit.
```

### Example

Let's consider the following inventory:

```yaml
---
anta_inventory:
  hosts:
    - host: 172.20.20.101
      name: DC1-SPINE1
      tags: ["SPINE", "DC1"]
    
    - host: 172.20.20.102
      name: DC1-SPINE2
      tags: ["SPINE", "DC1"]
    
    - host: 172.20.20.111
      name: DC1-LEAF1A
      tags: ["LEAF", "DC1"]
    
    - host: 172.20.20.112
      name: DC1-LEAF1B
      tags: ["LEAF", "DC1"]

    - host: 172.20.20.121
      name: DC1-BL1
      tags: ["BL", "DC1"]

    - host: 172.20.20.122
      name: DC1-BL2
      tags: ["BL", "DC1"]

    - host: 172.20.20.201
      name: DC2-SPINE1
      tags: ["SPINE", "DC2"]

    - host: 172.20.20.202
      name: DC2-SPINE2
      tags: ["SPINE", "DC2"]

    - host: 172.20.20.211
      name: DC2-LEAF1A
      tags: ["LEAF", "DC2"]

    - host: 172.20.20.212
      name: DC2-LEAF1B
      tags: ["LEAF", "DC2"]

    - host: 172.20.20.221
      name: DC2-BL1
      tags: ["BL", "DC2"]
      
    - host: 172.20.20.222
      name: DC2-BL2
      tags: ["BL", "DC2"]
```

To get the list of all configured tags in your CLI, run the following command:

```bash
anta get tags
Tags found:
[
  "BL",
  "DC1",
  "DC2",
  "LEAF",
  "SPINE",
  "all"
]

* note that tag all has been added by anta
```

!!! note Default all tag
    Even if you haven't explicitly configured the `all` tag in your inventory, it's automatically added. This default tag allows you to execute commands on all devices in your inventory when you don't specify any particular tag.

## List devices in inventory

This command will list all devices available in your inventory. Using the `--tags` option, you can filter this list to only include devices with specific tags. The `--connected` option allows you to display only the devices where a connection has been established.

### Command overview

```bash
anta get inventory --help
Usage: anta get inventory [OPTIONS]

  Show inventory loaded in ANTA.

Options:
  -t, --tags TEXT                List of tags using comma as separator:
                                 tag1,tag2,tag3
  --connected / --not-connected  Display inventory after connection has been
                                 created
  --help                         Show this message and exit.
```


!!! tip Offline information only
    In its default mode, `anta get inventory` provides only information that doesn't rely on a device connection. If you're interested in obtaining connection-dependent details, like the hardware model, please use the `--connected` option.

### Example

Let's consider the following inventory:

```yaml
---
anta_inventory:
  hosts:
    - host: 172.20.20.101
      name: DC1-SPINE1
      tags: ["SPINE", "DC1"]
    
    - host: 172.20.20.102
      name: DC1-SPINE2
      tags: ["SPINE", "DC1"]
    
    - host: 172.20.20.111
      name: DC1-LEAF1A
      tags: ["LEAF", "DC1"]
    
    - host: 172.20.20.112
      name: DC1-LEAF1B
      tags: ["LEAF", "DC1"]

    - host: 172.20.20.121
      name: DC1-BL1
      tags: ["BL", "DC1"]

    - host: 172.20.20.122
      name: DC1-BL2
      tags: ["BL", "DC1"]

    - host: 172.20.20.201
      name: DC2-SPINE1
      tags: ["SPINE", "DC2"]

    - host: 172.20.20.202
      name: DC2-SPINE2
      tags: ["SPINE", "DC2"]

    - host: 172.20.20.211
      name: DC2-LEAF1A
      tags: ["LEAF", "DC2"]

    - host: 172.20.20.212
      name: DC2-LEAF1B
      tags: ["LEAF", "DC2"]

    - host: 172.20.20.221
      name: DC2-BL1
      tags: ["BL", "DC2"]
      
    - host: 172.20.20.222
      name: DC2-BL2
      tags: ["BL", "DC2"]
```

To retrieve a comprehensive list of all devices along with their details, execute the following command. It will provide all the data loaded into the ANTA inventory from your [inventory file](../../usage-inventory-catalog/).

```bash
anta get inventory --tags SPINE
Current inventory content is:
{
    'DC1-SPINE1': AsyncEOSDevice(
        name='DC1-SPINE1',
        tags=['SPINE', 'DC1', 'all'],
        hw_model=None,
        is_online=False,
        established=False,
        host='172.20.20.101',
        eapi_port=443,
        username='arista',
        password='arista',
        enable_password='arista',
        insecure=False
    ),
    'DC1-SPINE2': AsyncEOSDevice(
        name='DC1-SPINE2',
        tags=['SPINE', 'DC1', 'all'],
        hw_model=None,
        is_online=False,
        established=False,
        host='172.20.20.102',
        eapi_port=443,
        username='arista',
        password='arista',
        enable_password='arista',
        insecure=False
    ),
    'DC2-SPINE1': AsyncEOSDevice(
        name='DC2-SPINE1',
        tags=['SPINE', 'DC2', 'all'],
        hw_model=None,
        is_online=False,
        established=False,
        host='172.20.20.201',
        eapi_port=443,
        username='arista',
        password='arista',
        enable_password='arista',
        insecure=False
    ),
    'DC2-SPINE2': AsyncEOSDevice(
        name='DC2-SPINE2',
        tags=['SPINE', 'DC2', 'all'],
        hw_model=None,
        is_online=False,
        established=False,
        host='172.20.20.202',
        eapi_port=443,
        username='arista',
        password='arista',
        enable_password='arista',
        insecure=False
    )
}
```
