# ANTA Documentation

This website provides generic documentation related to the Arista Network Test Automation framework (ANTA)

<img src="./imgs/anta-nrfu-table-output.png" class="img_center"></img>

# Arista Network Test Automation (ANTA) Framework

This repository is a Python package to automate tests on Arista devices.

- The package name is [ANTA](https://github.com/arista-netdevops-community/anta/blob/master/anta/), which stands for **Arista Network Test Automation**.
- This package provides a set of tests to validate the state of your network.
- This package can be imported in Python scripts:
  - To automate NRFU (Network Ready For Use) test on a preproduction network
  - To automate tests on a live network (periodically or on demand)

This repository comes with a [cli](cli/overview.md) to run __Arista Network Test Automation__ (ANTA) framework using your preferred shell:

```bash
# Install ANTA
pip install anta

# Run ANTA cli
$ anta
Usage: anta [OPTIONS] COMMAND [ARGS]...

  Arista Network Test CLI

Options:
  --username TEXT         Username to connect to EOS  [env var: ANTA_USERNAME]
  --password TEXT         Password to connect to EOS  [env var: ANTA_PASSWORD]
  --timeout INTEGER       Connection timeout (default 5)  [env var: ANTA_TIMEOUT]
  --enable-password TEXT  Enable password if required to connect  [env var: ANTA_ENABLE_PASSWORD]
  -i, --inventory PATH    Path to your inventory file  [env var: ANTA_INVENTORY]
  --timeout INTEGER       Connection timeout (default 5)  [env var: ANTA_TIMEOUT]
  --help                  Show this message and exit.

Commands:
  exec  Execute commands to inventory devices
  get   Get data from/to ANTA
  nrfu  Run NRFU against inventory devices
```

In addition, previous [scripts](./usage-check-devices/) are now marked as __deprecated__ and will be removed in a future release:

- `check-devices.py` is an easy to use script to test your network with ANTA.
- `collect-eos-commands.py` to collect commands output from devices
- `collect-sheduled-show-tech.py` to collect the scheduled show tech-support files from devices
- `clear-counters.py` to clear counters on devices
- `evpn-blacklist-recovery.py` to clear the list of MAC addresses which are blacklisted in EVPN
- `create-devices-inventory-from-cvp.py`: Build inventory for scripts from Arista Cloudvision (CVP)

> Most of these scripts use eAPI (EOS API). You can find examples of EOS automation with eAPI in this [repository](https://github.com/arista-netdevops-community/arista_eos_automation_with_eAPI).
