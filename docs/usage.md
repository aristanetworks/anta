# Repository usage


!!! warning "Scripts are now deprecated"
    Please note with [anta cli availability](../usage-anta-cli/), scripts described on this page are now deprecated and will be removed in later release of this project.



Once you are done with the installation, you can use the the [scripts](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts) or the [ANTA](https://github.com/arista-netdevops-community/network-test-automation/blob/master/anta) package.

## How to use the scripts

### How to create an inventory from CVP

The python script [create-devices-inventory-from-cvp.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/create-devices-inventory-from-cvp.py) create an inventory text file using CVP.

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

!!! info
    Please visit this [dedicated section](./usage-check-devices.md) for __check-devices.py__ script

### How to collect commands output

!!! info
    Please visit this [dedicated section](./usage-inventory-catalog.md) for how to use inventory file.

The python script [collect-eos-commands.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/collect-eos-commands.py) runs show commands on devices and collects the output:

- Update the devices [inventory](https://github.com/arista-netdevops-community/network-test-automation/blob/master/examples/inventory.yml)
- Update the [EOS commands list](https://github.com/arista-netdevops-community/network-test-automation/blob/master/examples/eos-commands.yaml) you would like to collect from the devices in text or JSON format
- Run the python script [collect-eos-commands.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/collect-eos-commands.py)
- The commands output is saved in the output directory

```shell
vi inventory.yml
vi eos-commands.yaml
./collect-eos-commands.py --help
./collect-eos-commands.py -i inventory.yml -c eos-commands.yaml -o outdir -u username -p password
ls outdir
```

### How to collect the scheduled show tech-support files

!!! info
    Please visit this [dedicated section](./usage-inventory-catalog.md) for how to use inventory file.

The python script [collect-sheduled-show-tech.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/collect-sheduled-show-tech.py) collects the scheduled show tech-support files:

- Update the devices [inventory](https://github.com/arista-netdevops-community/network-test-automation/blob/master/examples/inventory.yml)
- Run the python script [collect-sheduled-show-tech.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/collect-sheduled-show-tech.py)
- The files are saved in the output directory

```shell
vi inventory.yml
./collect-sheduled-show-tech.py --help
./collect-sheduled-show-tech.py -i inventory.yml -u username -o outdir
ls outdir
```

### How to clear counters

The python script [clear-counters.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/clear-counters.py) clears counters:

!!! info
    Please visit this [dedicated section](./usage-inventory-catalog.md) for how to use inventory file.

- Update the devices [inventory](https://github.com/arista-netdevops-community/network-test-automation/blob/master/examples/inventory.yml)
- Run the python script [clear-counters.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/clear-counters.py)

```shell
vi inventory.yml
./clear-counters.py --help
./clear-counters.py -i inventory.yml -u username
```

### How to clear the MAC addresses which are blacklisted in EVPN

The python script [evpn-blacklist-recovery.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/evpn-blacklist-recovery.py) clears the MAC addresses which are blacklisted in EVPN:

!!! info
    Please visit this [dedicated section](./usage-inventory-catalog.md) for how to use inventory file.

- Update the devices [inventory](https://github.com/arista-netdevops-community/network-test-automation/blob/master/examples/inventory.yml)
- Run the python script [evpn-blacklist-recovery.py](https://github.com/arista-netdevops-community/network-test-automation/blob/master/scripts/evpn-blacklist-recovery.py)

```shell
vi inventory.yml
./evpn-blacklist-recovery.py --help
./evpn-blacklist-recovery.py -i inventory.yml -u username
```
