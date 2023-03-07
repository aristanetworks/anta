# Create inventory from CloudVision

In large setup, it can be useful to create your inventory based on CloudVision inventory.

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

Output is an inventory with name of the container added as a tag for the host

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
