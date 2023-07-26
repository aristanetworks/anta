# Create an Inventory from Ansible inventory

In large setups, it might be beneficial to construct your inventory based on your Ansible inventory. The `from-ansible` entrypoint of the `get` command enables the user to create an ANTA inventory from Ansible.

### Command overview

```bash
anta get from-ansible --help
Usage: anta get from-ansible [OPTIONS]

  Build ANTA inventory from an ansible inventory YAML file

Options:
  -g, --ansible-group TEXT        Ansible group to filter
  -i, --ansible-inventory FILENAME
                                  Path to your ansible inventory file to read
  -o, --output FILENAME           Path to save inventory file
  -d, --inventory-directory PATH  Directory to save inventory file
  --help                          Show this message and exit.
```

The output is an inventory where the name of the container is added as a tag for each host:

```yaml
anta_inventory:
  hosts:
  - host: 10.73.252.41
    name: srv-pod01
  - host: 10.73.252.42
    name: srv-pod02
  - host: 10.73.252.43
    name: srv-pod03
```

!!! warning
    The current implementation only considers devices directly attached to a specific Ansible group and does not support inheritence when using the `--ansible-group` option.

`host` value is coming from the `ansible_host` key in your inventory while `name` is the name you defined for your host. Below is an ansible inventory example used to generate previous inventory:

```yaml
---
tooling:
  children:
    endpoints:
      hosts:
        srv-pod01:
          ansible_httpapi_port: 9023
          ansible_port: 9023
          ansible_host: 10.73.252.41
          type: endpoint
        srv-pod02:
          ansible_httpapi_port: 9024
          ansible_port: 9024
          ansible_host: 10.73.252.42
          type: endpoint
        srv-pod03:
          ansible_httpapi_port: 9025
          ansible_port: 9025
          ansible_host: 10.73.252.43
          type: endpoint
```
