[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/network-test-automation/blob/master/LICENSE)
[![CI](https://github.com/arista-netdevops-community/network-test-automation/actions/workflows/test.yml/badge.svg)](https://github.com/arista-netdevops-community/network-test-automation/actions)

**Table of Contents**
- [About this repository](#about-this-repository)
- [List of tests available in the python package anta](#list-of-tests-available-in-the-python-package-anta)
- [Requirements](#requirements)
  - [Requirements on your laptop](#requirements-on-your-laptop)
    - [Use the `pip install` command with the git url](#use-the-pip-install-command-with-the-git-url)
    - [Clone the repository and use the `pip install .` command](#clone-the-repository-and-use-the-pip-install--command)
    - [Clone the repository and use `setup.py`](#clone-the-repository-and-use-setuppy)
    - [Clone the repository and use the `pip install -r requirements.txt` command](#clone-the-repository-and-use-the-pip-install--r-requirementstxt-command)
  - [Requirements on the switches](#requirements-on-the-switches)
  - [Quick check](#quick-check)
- [Repository usage](#repository-usage)
  - [Tests devices](#tests-devices)
  - [Test devices reachability](#test-devices-reachability)
  - [Collect commands output](#collect-commands-output)
  - [Collect the scheduled show tech-support files](#collect-the-scheduled-show-tech-support-files)
  - [Clear counters](#clear-counters)
  - [Clear the list of MAC addresses which are blacklisted in EVPN](#clear-the-list-of-mac-addresses-which-are-blacklisted-in-evpn)
- [Devices testing demo](#devices-testing-demo)
- [Contribution guide](#contribution-guide)
- [Continuous Integration](#continuous-integration)
- [Credits](#credits)
  
# About this repository

This repository has a [python package](anta) to automate tests on Arista devices.

- This package (or some functions of this package) can be imported in Python scripts to automate NRFU (Network Ready For Use) test or to automate tests on a production network (periodically or on demand).  
- The package name is **anta**, which stands for **Arista Network Test Automation**.

In addition, this repository has also Python scripts to:

- [Test devices](#tests-devices)
- [Test devices reachability](#test-devices-reachability)
- [Collect commands output from devices](#collect-commands-output)
- [Collect the scheduled show tech-support files from devices](#collect-the-scheduled-show-tech-support-files)
- [Clear counters on devices](#clear-counters)
- [Clear the list of MAC addresses which are blacklisted in EVPN](#clear-the-list-of-mac-addresses-which-are-blacklisted-in-evpn)

This content uses eAPI (EOS API). You can find examples of EOS automation with eAPI in this [repository](https://github.com/arista-netdevops-community/arista_eos_automation_with_eAPI).

# List of tests available in the python package [anta](anta)

The tests are defined in functions in the python module [tests.py](anta/tests.py) in the python package [anta](anta).  
 Each function returns `True` or `False` (or `None` when it can not run properly).

The [documentation](documentation) directory has the tests documentation:

- [overview.md](documentation/overview.md) file
- [tests.md](documentation/tests.md) file

These two files are generated using the python package [lazydocs](https://github.com/ml-tooling/lazydocs) and the docstrings in the python package [anta](anta).  


# Requirements

## Requirements on your laptop

Python 3 (at least 3.3) and some packages that are not part of the standard Python library.

```shell
python -V
```

There are several ways to install the requirements.

### Use the `pip install` command with the git url  

```shell
sudo pip install git+https://github.com/arista-netdevops-community/network-test-automation.git
```

This will install the package [anta](anta) and its dependencies.

To update, run this command:

```shell
sudo pip install -U git+https://github.com/arista-netdevops-community/network-test-automation.git
```

### Clone the repository and use the `pip install .` command

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
pip install .
```
### Clone the repository and use `setup.py`

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
```

Build the package:

```shell
python setup.py build
```

Install the package:

```shell
python setup.py install
```

### Clone the repository and use the `pip install -r requirements.txt` command

```shell
git clone https://github.com/arista-netdevops-community/network-test-automation.git
cd network-test-automation
pip install -r requirements.txt
```

## Requirements on the switches

```text
switch1#sh run int ma1
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
switch1#
```

- Enable eAPI on the MGMT vrf:

```text
switch1#configure
switch1(config)#management api http-commands
switch1(config-mgmt-api-http-cmds)#protocol https port 443
switch1(config-mgmt-api-http-cmds)#no shutdown
switch1(config-mgmt-api-http-cmds)#vrf MGMT
switch1(config-mgmt-api-http-cmds-vrf-MGMT)#no shutdown
switch1(config-mgmt-api-http-cmds-vrf-MGMT)#exit
switch1(config-mgmt-api-http-cmds)#exit
switch1(config)#
```

Now the swicth accepts on port 443 in the MGMT VRF HTTPS requests containing a list of CLI commands.

- Verify:

```text
switch1#sh management http-server
```

```text
switch1#show management api http-commands
```

## Quick check

Run this python script to validate the device reachability using eAPI.
Use your device credentials and IP address.

```python
import ssl
from jsonrpclib import Server
ssl._create_default_https_context = ssl._create_unverified_context
USERNAME = "arista"
PASSWORD = "arista"
IP = "10.100.164.145"
URL=f'https://{USERNAME}:{PASSWORD}@{IP}/command-api'
switch = Server(url)
result=switch.runCmds(1,['show version'], 'text')
print(result[0]['output'])
```

# Repository usage

## Tests devices

- Update the devices [inventory](examples/devices.txt) with the devices IP address or hostnames.
- Update the file [tests.yaml](examples/tests.yaml) to indicate the tests you would like to run. Some tests require an argument. In that case, provide it using the same YAML file.
- Run the python script [check-devices.py](scripts/check-devices.py).
  - This script imports the python functions defined in the directory [anta](anta).
  - These functions defined the tests.
- Check the result in the output file.

```shell
vi devices.txt
vi tests.yaml
./check-devices.py --help
./check-devices.py -i devices.txt -t tests.yaml -o output.txt -u username
cat output.txt
```

## Test devices reachability

- Update the devices [inventory](examples/devices.txt) with the devices IP address or hostnames.
- Run the python script [check-devices-reachability.py](scripts/check-devices-reachability.py).
- Check the result in the console.

```shell
vi devices.txt
./check-devices-reachability.py --help
./check-devices-reachability.py -i devices.txt -u username
```

## Collect commands output

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostnames.
- Update the EOS commands list [eos-commands.yaml](examples/eos-commands.yaml) you would like to collect from the devices in text or JSON format.
- Run the python script [collect-eos-commands.py](scripts/collect-eos-commands.py).
- Check the output in the output directory.

```shell
vi devices-list.text
vi eos-commands.yaml
./collect-eos-commands.py --help
./collect-eos-commands.py -i devices.txt -c eos-commands.yaml -o outdir -u username
ls outdir
```

## Collect the scheduled show tech-support files

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostname.
- Run the python script [collect-sheduled-show-tech.py](scripts/collect-sheduled-show-tech.py).
- Check the output in the output directory.

```shell
vi devices-list.text
./collect-sheduled-show-tech.py --help
./collect-sheduled-show-tech.py -i devices.txt -u username -o outdir
ls outdir
```

## Clear counters

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostnames.
- Run the python script [clear-counters.py](scripts/clear-counters.py).

```shell
vi devices-list.text
./clear-counters.py --help
./clear-counters.py -i devices.txt -u username
```

## Clear the list of MAC addresses which are blacklisted in EVPN

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostnames.
- Run the python script [evpn-blacklist-recovery.py](scripts/evpn-blacklist-recovery.py).

```shell
vi devices-list.text
./evpn-blacklist-recovery.py --help
./evpn-blacklist-recovery.py -i devices.txt -u username
```

# Devices testing demo

To test devices, once you are done with the requirements described above, you simply need to indicate:

- Your devices name or IP address in a text file. Here's an [example](examples/devices.txt).
- The tests you would like to run in a YAML file. Some tests require an argument. In that case, provide it using the same YAML file. Here's an [example](examples/tests.yaml).  

```text
./check-devices.py --help
usage: check-devices.py [-h] -i INVENTORY_FILE -u USERNAME -t TEST_CATALOG -o OUTPUT_FILE

EOS devices health checks

optional arguments:
  -h, --help         show this help message and exit
  -i INVENTORY_FILE  Text file containing a list of switches, one per line
  -u USERNAME        Devices username
  -t TEST_CATALOG    Text file containing the tests
  -o OUTPUT_FILE     Output file
```

```text
./check-devices.py -u arista -i devices.txt -o output.txt -t tests.yaml
Device password:
Enable password (if any):
Testing devices .... please be patient ...
Can not connect to device 2.2.2.2
Running tests on device 10.73.1.101 ...
Running tests on device 10.73.1.102 ...
Running tests on device 10.73.1.106 ...
Test results are saved on output.txt
```

```text
$ cat output.txt
Mon Apr 11 19:12:58 2022
devices inventory file was devices.txt
devices username was arista
list of unreachable devices is
2.2.2.2
tests file was tests.yaml

***** Results *****

+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  01.01  |  01.02  |  01.03  |  01.04  |  02.01  |  02.02  |  02.03  |  02.04  |  02.05  |  02.06  |  02.07  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Fail  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Pass  |   Fail  |   Fail  |   Pass  |   Pass  |
|  10.73.1.102  |   Fail  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Pass  |   Pass  |   Fail  |   Pass  |   Pass  |
|  10.73.1.106  |   Fail  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Pass  |   Pass  |   Fail  |   Pass  |   Pass  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  02.08  |  03.01  |  03.02  |  03.03  |  03.04  |  03.05  |  04.01  |  04.02  |  05.01  |  05.02  |  06.01  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Pass  |   Skip  |   Fail  |   Pass  |   Fail  |   Skip  |   Pass  |   Fail  |   Skip  |   Skip  |   Skip  |
|  10.73.1.102  |   Pass  |   Skip  |   Fail  |   Pass  |   Fail  |   Skip  |   Pass  |   Fail  |   Skip  |   Skip  |   Skip  |
|  10.73.1.106  |   Pass  |   Skip  |   Fail  |   Pass  |   Fail  |   Skip  |   Pass  |   Fail  |   Skip  |   Skip  |   Skip  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  07.01  |  08.01  |  08.02  |  08.03  |  08.04  |  08.05  |  08.06  |  09.01  |  09.02  |  09.03  |  09.04  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Skip  |   Skip  |   Skip  |   Skip  |
|  10.73.1.102  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Skip  |   Skip  |   Skip  |   Skip  |
|  10.73.1.106  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Fail  |   Pass  |   Pass  |   Fail  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  09.05  |  10.01  |  11.01  |  11.02  |  12.01  |  13.01  |  14.01  |  14.02  |  15.01  |  16.01  |  16.02  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Skip  |   Fail  |   Fail  |   Skip  |   Pass  |   Pass  |   Pass  |   Fail  |   Pass  |   Pass  |   Fail  |
|  10.73.1.102  |   Skip  |   Fail  |   Fail  |   Skip  |   Pass  |   Pass  |   Pass  |   Fail  |   Pass  |   Pass  |   Fail  |
|  10.73.1.106  |   Skip  |   Fail  |   Pass  |   Fail  |   Pass  |   Pass  |   Pass  |   Fail  |   Pass  |   Pass  |   Fail  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  16.03  |  16.04  |  16.05  |  16.06  |  16.07  |  17.01  |  17.02  |  18.01  |  18.02  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Pass  |   Pass  |   Fail  |   Skip  |   Skip  |   Pass  |   Fail  |   Skip  |   Pass  |
|  10.73.1.102  |   Pass  |   Pass  |   Fail  |   Skip  |   Skip  |   Pass  |   Fail  |   Skip  |   Pass  |
|  10.73.1.106  |   Pass  |   Pass  |   Pass  |   Skip  |   Skip  |   Pass  |   Fail  |   Skip  |   Pass  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+

***** Tests *****

01.01    {"name": "verify_eos_version", "versions": ["4.25.4M", "4.26.1F"]}
01.02    {"name": "verify_terminattr_version", "versions": ["v1.13.6", "v1.8.0"]}
01.03    {"name": "verify_eos_extensions"}
01.04    {"name": "verify_field_notice_44_resolution"}
02.01    {"name": "verify_uptime", "minimum": 86400}
02.02    {"name": "verify_reload_cause"}
02.03    {"name": "verify_coredump"}
02.04    {"name": "verify_agent_logs"}
02.05    {"name": "verify_syslog"}
02.06    {"name": "verify_cpu_utilization"}
02.07    {"name": "verify_memory_utilization"}
02.08    {"name": "verify_filesystem_utilization"}
03.01    {"name": "verify_transceivers_manufacturers", "manufacturers": ["Not Present", "Arista Networks", "Arastra, Inc."]}
03.02    {"name": "verify_system_temperature"}
03.03    {"name": "verify_transceiver_temperature"}
03.04    {"name": "verify_environment_cooling"}
03.05    {"name": "verify_environment_power"}
04.01    {"name": "verify_zerotouch"}
04.02    {"name": "verify_running_config_diffs"}
05.01    {"name": "verify_unified_forwarding_table_mode", "mode": 3}
05.02    {"name": "verify_tcam_profile", "profile": "vxlan-routing"}
06.01    {"name": "verify_adverse_drops"}
07.01    {"name": "verify_ntp"}
08.01    {"name": "verify_interface_utilization"}
08.02    {"name": "verify_interface_errors"}
08.03    {"name": "verify_interface_discards"}
08.04    {"name": "verify_interface_errdisabled"}
08.05    {"name": "verify_interfaces_status", "minimum": 4}
08.06    {"name": "verify_storm_control_drops"}
09.01    {"name": "verify_portchannels"}
09.02    {"name": "verify_illegal_lacp"}
09.03    {"name": "verify_mlag_status"}
09.04    {"name": "verify_mlag_interfaces"}
09.05    {"name": "verify_mlag_config_sanity"}
10.01    {"name": "verify_loopback_count", "number": 3}
11.01    {"name": "verify_vxlan"}
11.02    {"name": "verify_vxlan_config_sanity"}
12.01    {"name": "verify_svi"}
13.01    {"name": "verify_spanning_tree_blocked_ports"}
14.01    {"name": "verify_routing_protocol_model", "model": "multi-agent"}
14.02    {"name": "verify_routing_table_size", "minimum": 2, "maximum": 20}
15.01    {"name": "verify_bfd"}
16.01    {"name": "verify_bgp_ipv4_unicast_state"}
16.02    {"name": "verify_bgp_ipv4_unicast_count", "number": 2, "vrf": "default"}
16.03    {"name": "verify_bgp_ipv6_unicast_state"}
16.04    {"name": "verify_bgp_evpn_state"}
16.05    {"name": "verify_bgp_evpn_count", "number": 2}
16.06    {"name": "verify_bgp_rtc_state"}
16.07    {"name": "verify_bgp_rtc_count", "number": 2}
17.01    {"name": "verify_ospf_state"}
17.02    {"name": "verify_ospf_count", "number": 3}
18.01    {"name": "verify_igmp_snooping_vlans", "configuration": "disabled", "vlans": [10, 12]}
18.02    {"name": "verify_igmp_snooping_global", "configuration": "enabled"}
```

# Contribution guide

Contributions are welcome.
Please refer to the [contribution guide](CONTRIBUTING.md)

# Continuous Integration

GitHub actions is used to test git pushes and pull requests.
The workflows are defined in this [directory](.github/workflows).
We can view the result [here](https://github.com/arista-netdevops-community/network-test-automation/actions).

# Credits

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi) and [Paul Lavelle](https://github.com/paullavelle), [Thomas Grimonet](https://github.com/titom73) 
for their contributions and guidances.
