[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/network-test-automation/blob/master/LICENSE)
[![CI](https://github.com/arista-netdevops-community/network-test-automation/actions/workflows/test.yml/badge.svg)](https://github.com/arista-netdevops-community/network-test-automation/actions)

**Table of Contents**
- [About this repository](#about-this-repository)
- [Tests available in the python package anta](#tests-available-in-the-python-package-anta)
- [Requirements](#requirements)
- [Repository usage](#repository-usage)
  - [How to tests devices](#how-to-tests-devices)
  - [How to test devices reachability](#how-to-test-devices-reachability)
  - [How to collect commands output](#how-to-collect-commands-output)
  - [How to collect the scheduled show tech-support files](#how-to-collect-the-scheduled-show-tech-support-files)
  - [How to clear counters](#how-to-clear-counters)
  - [How to clear the MAC addresses which are blacklisted in EVPN](#how-to-clear-the-mac-addresses-which-are-blacklisted-in-evpn)
- [Devices testing demo](#devices-testing-demo)
- [Contribution guide](#contribution-guide)
- [Continuous Integration](#continuous-integration)
- [Credits](#credits)
  
# About this repository

This repository has a [Python package](anta) to automate tests on Arista devices.

- The package name is **anta**, which stands for **Arista Network Test Automation**.
- This package (or some functions of this package) can be imported in Python scripts:
  - To automate NRFU (Network Ready For Use) test on a preproduction network
  - Or to automate tests on a live network (periodically or on demand)  

In addition, this repository has also Python scripts to:

- Test devices
- Test devices reachability
- Collect commands output from devices
- Collect the scheduled show tech-support files from devices
- Clear counters on devices
- Clear the list of MAC addresses which are blacklisted in EVPN

This content uses eAPI (EOS API). You can find examples of EOS automation with eAPI in this [repository](https://github.com/arista-netdevops-community/arista_eos_automation_with_eAPI).

# Tests available in the python package [anta](anta)

The tests are defined in functions in the python package [anta](anta):

- Each function returns `True`, `False` or `None` (when it can not run properly)
- The [overview.md](documentation/overview.md) file has an overview of the functions documentation

# Requirements

Please see the [requirements documentation](documentation/requirements.md) for the requirements and installation procedure.  

# Repository usage  

Once you are done with the installation, you can use the [anta](anta) package and the [scripts](scripts).

## How to tests devices

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

## How to test devices reachability

- Update the devices [inventory](examples/devices.txt) with the devices IP address or hostnames.
- Run the python script [check-devices-reachability.py](scripts/check-devices-reachability.py).
- Check the result in the console.

```shell
vi devices.txt
./check-devices-reachability.py --help
./check-devices-reachability.py -i devices.txt -u username
```

## How to collect commands output

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

## How to collect the scheduled show tech-support files

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostname.
- Run the python script [collect-sheduled-show-tech.py](scripts/collect-sheduled-show-tech.py).
- Check the output in the output directory.

```shell
vi devices-list.text
./collect-sheduled-show-tech.py --help
./collect-sheduled-show-tech.py -i devices.txt -u username -o outdir
ls outdir
```

## How to clear counters

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostnames.
- Run the python script [clear-counters.py](scripts/clear-counters.py).

```shell
vi devices-list.text
./clear-counters.py --help
./clear-counters.py -i devices.txt -u username
```

## How to clear the MAC addresses which are blacklisted in EVPN

- Update the devices [inventory](examples/devices.txt) with your devices IP address or hostnames.
- Run the python script [evpn-blacklist-recovery.py](scripts/evpn-blacklist-recovery.py).

```shell
vi devices-list.text
./evpn-blacklist-recovery.py --help
./evpn-blacklist-recovery.py -i devices.txt -u username
```

# Devices testing demo

To test devices, once you are done with the installation, you simply need to indicate:

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

Thank you to [Angélique Phillipps](https://github.com/aphillipps), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Khelil Sator](https://github.com/ksator), [Matthieu Tache](https://github.com/mtache), [Onur Gashi](https://github.com/onurgashi), [Paul Lavelle](https://github.com/paullavelle) and [Thomas Grimonet](https://github.com/titom73) for their contributions and guidances.
