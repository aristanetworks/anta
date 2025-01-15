<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA is a streamlined Python framework designed for efficient interaction with network devices. This section outlines how ANTA incorporates caching mechanisms to collect command outputs from network devices.

## Configuration

The `_init_cache()` method of the [AntaDevice](../api/device.md#anta.device.AntaDevice) abstract class initializes the cache. Child classes can override this method to tweak the cache configuration:

## Cache key design

The cache is initialized per `AntaDevice` and uses the following cache key design:

`<device_name>:<uid>`

The `uid` is an attribute of [AntaCommand](../api/models.md#anta.models.AntaCommand), which is a unique identifier generated from the command, version, revision and output format.

Each UID has its own asyncio lock. This design allows coroutines that need to access the cache for different UIDs to do so concurrently. The locks are managed by the `AntaCache.locks` dictionary.

## Mechanisms

By default, once the cache is initialized, it is used in the `collect()` method of `AntaDevice`. The `collect()` method prioritizes retrieving the output of the command from the cache. If the output is not in the cache, the private `_collect()` method will retrieve and then store it for future access.

## How to disable caching

Caching is enabled by default in ANTA following the previous configuration and mechanisms.

There might be scenarios where caching is not wanted. You can disable caching in multiple ways in ANTA:

1. Caching can be disabled globally, for **ALL** commands on **ALL** devices, using the `--disable-cache` global flag when invoking anta at the [CLI](../cli/overview.md#invoking-anta-cli):

   ```bash
   anta --disable-cache --username arista --password arista nrfu table
   ```

2. Caching can be disabled per device, network or range by setting the `disable_cache` key to `True` when defining the ANTA [Inventory](../usage-inventory-catalog.md#device-inventory) file:

   ```yaml
   anta_inventory:
     hosts:
       - host: 172.20.20.101
         name: DC1-SPINE1
         tags: ["SPINE", "DC1"]
         disable_cache: True # Set this key to True
       - host: 172.20.20.102
         name: DC1-SPINE2
         tags: ["SPINE", "DC1"]
         disable_cache: False # Optional since it's the default

     networks:
       - network: "172.21.21.0/24"
         disable_cache: True

     ranges:
       - start: 172.22.22.10
         end: 172.22.22.19
         disable_cache: True
   ```

   This approach effectively disables caching for **ALL** commands sent to devices targeted by the `disable_cache` key.

3. For tests developers, caching can be disabled for a specific [`AntaCommand`](../api/models.md#anta.models.AntaCommand) or [`AntaTemplate`](../api/models.md#anta.models.AntaTemplate) by setting the `use_cache` attribute to `False`. That means the command output will always be collected on the device and therefore, never use caching.

### Disable caching in a child class of `AntaDevice`

Since caching is implemented at the `AntaDevice` abstract class level, all subclasses will inherit that default behavior. As a result, if you need to disable caching in any custom implementation of `AntaDevice` outside of the ANTA framework, you must initialize `AntaDevice` with `disable_cache` set to `True`:

```python
class AnsibleEOSDevice(AntaDevice):
  """
  Implementation of an AntaDevice using Ansible HttpApi plugin for EOS.
  """
  def __init__(self, name: str, connection: ConnectionBase, tags: set = None) -> None:
      super().__init__(name, tags, disable_cache=True)
```
