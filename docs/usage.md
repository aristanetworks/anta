# Repository usage

Once you are done with the installation, you can use the [ANTA](api/README.md) package and the [scripts](../scripts).


## How to use the [ANTA](api/README.md) package

Have a quick look to the package documentation:

- The [overview.md](api/README.md) file is an overview of the package documentation
- The [tests.md](api/tests.md) file is a detailled documentation of the package

Instantiate the class `Server` of `jsonrpclib` for an EOS device:

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

Here's how we can import and use the functions of the [ANTA](api/README.md) package:

```python
>>> from anta.tests import *
>>> dir()
>>> help(verify_eos_version)
>>> help(verify_bgp_evpn_state)
>>> help(verify_interface_discards)
```

```python
>>> verify_eos_version(switch, ENABLE_PASSWORD, ["4.22.1F"])
>>> verify_bgp_ipv4_unicast_state(switch, ENABLE_PASSWORD)
>>> exit()
```

## How to use the [scripts](scripts)

### How to create an inventory from CVP

The python script [create-devices-inventory-from-cvp.py](../scripts/create-devices-inventory-from-cvp.py) create an inventory text file using CVP.

Run these commands to get an inventory with all devices IP address.

```shell
./create-devices-inventory-from-cvp.py --help
./create-devices-inventory-from-cvp.py -cvp 192.168.0.5 -u arista -o inventory
cat inventory/all.text
```

Run these commands to get an inventory with the IP address of the devices under the container `Spine`

```shell
./create-devices-inventory-from-cvp.py --help
./create-devices-inventory-from-cvp.py -cvp 192.168.0.5 -u arista -o inventory -c Spine
cat inventory/Spine.text
```

### How to check devices state

The python script [check-devices.py](../scripts/check-devices.py) uses the python functions defined in the package [ANTA](api/README.md) to test devices:

- Update the devices [inventory](../examples/devices.txt) with the devices IP address or hostname
- Update the file [tests.yaml](../examples/tests.yaml) to indicate the tests you would like to run. Some tests require an argument. In that case, provide it using the same YAML file
- Execute the script [check-devices.py](../scripts/check-devices.py)
- Check the tests result in the output file

```shell
vi devices.txt
vi tests.yaml
./check-devices.py --help
./check-devices.py -i devices.txt -t tests.yaml -o output.txt -u username
cat output.txt
```

### How to test devices reachability

The python script [check-devices-reachability.py](../scripts/check-devices-reachability.py) checks the devices reachability using eAPI:

- Update the devices [inventory](../examples/devices.txt) with the devices IP address or hostname
- Run the python script [check-devices-reachability.py](../scripts/check-devices-reachability.py)
- Check the result in the console

```shell
vi devices.txt
./check-devices-reachability.py --help
./check-devices-reachability.py -i devices.txt -u username
```

### How to collect commands output

The python script [collect-eos-commands.py](../scripts/collect-eos-commands.py) runs show commands on devices and collects the output:

- Update the devices [inventory](../examples/devices.txt) with the devices IP address or hostname
- Update the [EOS commands list](../examples/eos-commands.yaml) you would like to collect from the devices in text or JSON format
- Run the python script [collect-eos-commands.py](../scripts/collect-eos-commands.py)
- The commands output is saved in the output directory

```shell
vi devices-list.text
vi eos-commands.yaml
./collect-eos-commands.py --help
./collect-eos-commands.py -i devices.txt -c eos-commands.yaml -o outdir -u username
ls outdir
```

### How to collect the scheduled show tech-support files

The python script [collect-sheduled-show-tech.py](../scripts/collect-sheduled-show-tech.py) collects the scheduled show tech-support files:

- Update the devices [inventory](../examples/devices.txt) with the devices IP address or hostname
- Run the python script [collect-sheduled-show-tech.py](../scripts/collect-sheduled-show-tech.py)
- The files are saved in the output directory

```shell
vi devices-list.text
./collect-sheduled-show-tech.py --help
./collect-sheduled-show-tech.py -i devices.txt -u username -o outdir
ls outdir
```

### How to clear counters

The python script [clear-counters.py](../scripts/clear-counters.py) clears counters:

- Update the devices [inventory](../examples/devices.txt) with the devices IP address or hostname
- Run the python script [clear-counters.py](../scripts/clear-counters.py)

```shell
vi devices-list.text
./clear-counters.py --help
./clear-counters.py -i devices.txt -u username
```

### How to clear the MAC addresses which are blacklisted in EVPN

The python script [evpn-blacklist-recovery.py](../scripts/evpn-blacklist-recovery.py) clears the MAC addresses which are blacklisted in EVPN:

- Update the devices [inventory](../examples/devices.txt) with the devices IP address or hostname
- Run the python script [evpn-blacklist-recovery.py](../scripts/evpn-blacklist-recovery.py)

```shell
vi devices-list.text
./evpn-blacklist-recovery.py --help
./evpn-blacklist-recovery.py -i devices.txt -u username
```
