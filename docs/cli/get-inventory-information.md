---
anta_title: Retrieving Inventory Information
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The ANTA CLI offers multiple commands to access data from your local inventory.

## List devices in inventory

This command will list all devices available in the inventory. Using the `--tags` option, you can filter this list to only include devices with specific tags (visit [this page](tag-management.md) to learn more about tags). The `--connected` option allows to display only the devices where a connection has been established.

### Command overview

```bash
--8<-- "anta_get_inventory_help.txt"
```

> [!TIP]
> By default, `anta get inventory` only provides information that doesn't rely on a device connection. If you are interested in obtaining connection-dependent details, like the hardware model, use the `--connected` option.

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

To retrieve a comprehensive list of all devices along with their details, execute the following command. It will provide all the data loaded into the ANTA inventory from your [inventory file](../usage-inventory-catalog.md).

```bash
$ anta get inventory --tags SPINE
Current inventory content is:
{
    'DC1-SPINE1': AsyncEOSDevice(
        name='DC1-SPINE1',
        tags={'DC1-SPINE1', 'DC1', 'SPINE'},
        hw_model=None,
        is_online=False,
        established=False,
        disable_cache=False,
        host='172.20.20.101',
        eapi_port=443,
        username='arista',
        enable=False,
        insecure=False
    ),
    'DC1-SPINE2': AsyncEOSDevice(
        name='DC1-SPINE2',
        tags={'DC1', 'SPINE', 'DC1-SPINE2'},
        hw_model=None,
        is_online=False,
        established=False,
        disable_cache=False,
        host='172.20.20.102',
        eapi_port=443,
        username='arista',
        enable=False,
        insecure=False
    ),
    'DC2-SPINE1': AsyncEOSDevice(
        name='DC2-SPINE1',
        tags={'DC2', 'DC2-SPINE1', 'SPINE'},
        hw_model=None,
        is_online=False,
        established=False,
        disable_cache=False,
        host='172.20.20.201',
        eapi_port=443,
        username='arista',
        enable=False,
        insecure=False
    ),
    'DC2-SPINE2': AsyncEOSDevice(
        name='DC2-SPINE2',
        tags={'DC2', 'DC2-SPINE2', 'SPINE'},
        hw_model=None,
        is_online=False,
        established=False,
        disable_cache=False,
        host='172.20.20.202',
        eapi_port=443,
        username='arista',
        enable=False,
        insecure=False
    )
}
```
