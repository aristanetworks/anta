---
anta_title: Create an Inventory from CloudVision
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

In large setups, it might be beneficial to construct your inventory based on CloudVision. The `from-cvp` entrypoint of the `get` command enables the user to create an ANTA inventory from CloudVision.

!!! info
    The current implementation only works with on-premises CloudVision instances, not with CloudVision as a Service (CVaaS).

## Command overview

```bash
Usage: anta get from-cvp [OPTIONS]

  Build ANTA inventory from CloudVision.

  NOTE: Only username/password authentication is supported for on-premises CloudVision instances.
  Token authentication for both on-premises and CloudVision as a Service (CVaaS) is not supported.

Options:
  -o, --output FILE     Path to save inventory file  [env var: ANTA_INVENTORY;
                        required]
  --overwrite           Do not prompt when overriding current inventory  [env
                        var: ANTA_GET_FROM_CVP_OVERWRITE]
  -host, --host TEXT    CloudVision instance FQDN or IP  [required]
  -u, --username TEXT   CloudVision username  [required]
  -p, --password TEXT   CloudVision password  [required]
  -c, --container TEXT  CloudVision container where devices are configured
  --ignore-cert         By default connection to CV will use HTTPS
                        certificate, set this flag to disable it  [env var:
                        ANTA_GET_FROM_CVP_IGNORE_CERT]
  --help                Show this message and exit.
```

The output is an inventory where the name of the container is added as a tag for each host:

```yaml
anta_inventory:
  hosts:
  - host: 192.168.0.13
    name: leaf2
    tags:
    - pod1
  - host: 192.168.0.15
    name: leaf4
    tags:
    - pod2
```

> [!WARNING]
> The current implementation only considers devices directly attached to a specific container when using the `--cvp-container` option.

## Creating an inventory from multiple containers

If you need to create an inventory from multiple containers, you can use a bash command and then manually concatenate files to create a single inventory file:

```bash
$ for container in pod01 pod02 spines; do anta get from-cvp -ip <cvp-ip> -u cvpadmin -p cvpadmin -c $container -d test-inventory; done

[12:25:35] INFO     Getting auth token from cvp.as73.inetsix.net for user tom
[12:25:36] INFO     Creating inventory folder /home/tom/Projects/arista/network-test-automation/test-inventory
           WARNING  Using the new api_token parameter. This will override usage of the cvaas_token parameter if both are provided. This is because api_token and cvaas_token parameters
                    are for the same use case and api_token is more generic
           INFO     Connected to CVP cvp.as73.inetsix.net


[12:25:37] INFO     Getting auth token from cvp.as73.inetsix.net for user tom
[12:25:38] WARNING  Using the new api_token parameter. This will override usage of the cvaas_token parameter if both are provided. This is because api_token and cvaas_token parameters
                    are for the same use case and api_token is more generic
           INFO     Connected to CVP cvp.as73.inetsix.net


[12:25:38] INFO     Getting auth token from cvp.as73.inetsix.net for user tom
[12:25:39] WARNING  Using the new api_token parameter. This will override usage of the cvaas_token parameter if both are provided. This is because api_token and cvaas_token parameters
                    are for the same use case and api_token is more generic
           INFO     Connected to CVP cvp.as73.inetsix.net

           INFO     Inventory file has been created in /home/tom/Projects/arista/network-test-automation/test-inventory/inventory-spines.yml
```
