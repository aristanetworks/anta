# Repository usage

Once you are done with the installation, you can use the the [scripts](../scripts) or the [ANTA](../anta) package.

## How to use the [scripts](scripts)

### How to create an inventory from CVP

The python script [create-devices-inventory-from-cvp.py](../scripts/create-devices-inventory-from-cvp.py) create an inventory text file using CVP.

Run these commands to get an inventory with all devices IP address.

```shell
./create-devices-inventory-from-cvp.py --help
./create-devices-inventory-from-cvp.py -cvp 192.168.0.5 -u arista -o inventory
cat inventory/all.yml
```

Run these commands to get an inventory with the IP address of the devices under the container `Spine`

```shell
./create-devices-inventory-from-cvp.py --help
./create-devices-inventory-from-cvp.py -cvp 192.168.0.5 -u arista -o inventory -c Spine
cat inventory/Spine.yml
```

### How to check devices state

The python script [check-devices.py](../scripts/check-devices.py) uses the python functions defined in the package [ANTA](api/README.md) to test devices:

- Update the devices [inventory](../examples/inventory.yml)
- Update the file [tests.yaml](../examples/tests.yaml) to indicate the tests you would like to run. Some tests require an argument. In that case, provide it using the same YAML file
- Execute the script [check-devices.py](../scripts/check-devices.py)
- Check the tests result in the output file

```shell
vi inventory.yml
vi tests.yaml
./check-devices.py --help
./check-devices.py -i inventory.yml -c tests.yaml --table -u username -p password
```

### How to collect commands output

The python script [collect-eos-commands.py](../scripts/collect-eos-commands.py) runs show commands on devices and collects the output:

- Update the devices [inventory](../examples/inventory.yml)
- Update the [EOS commands list](../examples/eos-commands.yaml) you would like to collect from the devices in text or JSON format
- Run the python script [collect-eos-commands.py](../scripts/collect-eos-commands.py)
- The commands output is saved in the output directory

```shell
vi inventory.yml
vi eos-commands.yaml
./collect-eos-commands.py --help
./collect-eos-commands.py -i inventory.yml -c eos-commands.yaml -o outdir -u username -p password
ls outdir
```

### How to collect the scheduled show tech-support files

The python script [collect-sheduled-show-tech.py](../scripts/collect-sheduled-show-tech.py) collects the scheduled show tech-support files:

- Update the devices [inventory](../examples/inventory.yml)
- Run the python script [collect-sheduled-show-tech.py](../scripts/collect-sheduled-show-tech.py)
- The files are saved in the output directory

```shell
vi inventory.yml
./collect-sheduled-show-tech.py --help
./collect-sheduled-show-tech.py -i inventory.yml -u username -o outdir
ls outdir
```

### How to clear counters

The python script [clear-counters.py](../scripts/clear-counters.py) clears counters:

- Update the devices [inventory](../examples/inventory.yml)
- Run the python script [clear-counters.py](../scripts/clear-counters.py)

```shell
vi inventory.yml
./clear-counters.py --help
./clear-counters.py -i inventory.yml -u username
```

### How to clear the MAC addresses which are blacklisted in EVPN

The python script [evpn-blacklist-recovery.py](../scripts/evpn-blacklist-recovery.py) clears the MAC addresses which are blacklisted in EVPN:

- Update the devices [inventory](../examples/inventory.yml)
- Run the python script [evpn-blacklist-recovery.py](../scripts/evpn-blacklist-recovery.py)

```shell
vi inventory.yml
./evpn-blacklist-recovery.py --help
./evpn-blacklist-recovery.py -i inventory.yml -u username
```

## How to use the [ANTA](../anta/) package

### How to instantiate the class `Server` of `jsonrpclib` for an EOS device

```python
>>> import ssl
>>> from jsonrpclib import Server
>>> ssl._create_default_https_context = ssl._create_unverified_context
>>> USERNAME = "arista"
>>> PASSWORD = "aristatwfn"
>>> ENABLE_PASSWORD = "aristatwfn"
>>> IP = "192.168.0.12"
>>> URL=f'https://{USERNAME}:{PASSWORD}@{IP}/command-api'
>>> switch = Server(URL)
```

### How to import and use the inventory

```python
from anta.inventory import AntaInventory

inventory = AntaInventory(
    inventory_file="inventory.yml",
    username="username",
    password="password",
    enable_password="enable",
    auto_connect=True,
    timeout=1,
)

# print the non reachable devices
devices = inventory.get_inventory(established_only=False)
for device in devices:
    if device.established is False:
        host = str(device.host)
        print(f"Could not connect to device {host}")

# run an EOS commands list on the reachable devices from the inventory
devices = inventory.get_inventory(established_only=True)
for device in devices:
    switch = device.session
    switch.runCmds(
        1, ["show version", "show ip bgp summary"]
    )
```

### How to import and use the tests functions

```python
>>> from anta.tests.system import *
>>> dir()
>>> help(verify_ntp)
```
