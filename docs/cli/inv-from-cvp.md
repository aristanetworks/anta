# Create inventory from CloudVision

In a large setup, it can be useful to create your inventory based on CloudVision inventory.

```bash
$ anta get from-cvp
Usage: anta get from-cvp [OPTIONS]

  Build ANTA inventory from Cloudvision

Options:
  -ip, --cvp-ip TEXT              CVP IP Address
  -u, --cvp-username TEXT         CVP Username
  -p, --cvp-password TEXT         CVP Password / token
  -c, --cvp-container TEXT        Container where devices are configured
  -d, --inventory-directory PATH  Path to save inventory file
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --help                          Show this message and exit.
```

Output is an inventory with the name of the container added as a tag for the host:

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

!!! warning Container lookup is not recursive
    Current implementation only takes devices directly attached to a specific container when using cli with `--cvp-container` option.

If you want to build an inventory based on multiple containers, you can use a bash command as shown below and then manually concatenate files to create a single inventory file.

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