[![License](https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](https://github.com/arista-netdevops-community/network_tests_automation/blob/master/LICENSE)
[![CI](https://github.com/arista-netdevops-community/network_tests_automation/actions/workflows/test.yml/badge.svg)](https://github.com/arista-netdevops-community/network_tests_automation/actions)

# Network tests automation

- [Network tests automation](#network-tests-automation)
  - [About this repository](#about-this-repository)
  - [Requirements](#requirements)
    - [Requirements on your laptop](#requirements-on-your-laptop)
    - [Requirements on the switches](#requirements-on-the-switches)
    - [Quick test](#quick-test)
  - [List of available tests](#list-of-available-tests)
  - [Repository usage](#repository-usage)
    - [To test devices reachability](#to-test-devices-reachability)
    - [To run tests on devices](#to-run-tests-on-devices)
    - [To collect commands output from EOS devices](#to-collect-commands-output-from-eos-devices)
    - [To clear counters on EOS devices](#to-clear-counters-on-eos-devices)
    - [To clear on devices the list of MAC addresses which are blacklisted in EVPN](#to-clear-on-devices-the-list-of-mac-addresses-which-are-blacklisted-in-evpn)
    - [Demo](#demo)
  - [Repository structure](#repository-structure)
    - [devices.txt file](#devicestxt-file)
    - [eos-commands.yaml file](#eos-commandsyaml-file)
    - [tests.yaml file](#testsyaml-file)
    - [tests_eos directory](#tests_eos-directory)
    - [generate_functions_documentation.py file](#generate_functions_documentationpy-file)
    - [documentation directory](#documentation-directory)
    - [check-devices-reachability.py file](#check-devices-reachabilitypy-file)
    - [clear_counters.py file](#clear_counterspy-file)
    - [collect-eos-commands.py file](#collect-eos-commandspy-file)
    - [check-devices.py file](#check-devicespy-file)
    - [evpn-blacklist-recovery.py file](#evpn-blacklist-recoverypy-file)
    - [unit_test.py file](#unit_testpy-file)
    - [mock_data directory](#mock_data-directory)
  - [Contribution guide](#contribution-guide)
  - [Credits](#credits)
## About this repository

This repository has automation content to test Arista devices.

To run these tests, once you are done with the requirements described below, you simply need to indicate your devices name in a text file and to indicate the tests you would like to run in a YAML file. Here's an [example](tests.yaml).

This repository has also content to:
* Collect commands output on devices.
* Clear counters on devices.
* Test the devices reachability.
* Clear the list of MAC addresses which are blacklisted in EVPN

This repository uses Python scripts and eAPI (EOS API). You can find examples of EOS automation with eAPI in this [repository](https://github.com/arista-netdevops-community/arista_eos_automation_with_eAPI).

## Requirements

### Requirements on your laptop

Python 3 (at least 3.3) and some packages that are not part of the standard Python library.

```shell
lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 18.04.4 LTS
Release:        18.04
Codename:       bionic
```

```shell
python -V
Python 3.9.6
```

The required packages are in the [requirements.txt](requirements.txt) file.
Clone the repository and install the requirements:

```shell
pip install -r requirements.txt
```

Verify

```shell
pip list | grep 'jsonrpclib-pelix\|PyYAML\|colorama\|prettytable'
colorama                   0.3.7
jsonrpclib-pelix           0.4.2
prettytable                2.5.0
PyYAML                     5.4.1
```

### Requirements on the switches

* Enable eAPI:

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
```
switch1#sh run int ma1
interface Management1
   description oob_management
   vrf MGMT
   ip address 10.73.1.105/24
switch1#
```

Now the swicth accepts HTTPS requests on port 443 in the MGMT VRF containing a list of CLI commands.

* Verify:

```text
switch1(config)#sh management http-server
SSL Profile:        none
FIPS Mode:          No
QoS DSCP:           0
Log Level:          none
CSP Frame Ancestor: None
TLS Protocols:      1.0 1.1 1.2
   VRF        Server Status      Enabled Services
---------- --------------------- ----------------
   MGMT       HTTPS: port 443    http-commands

```

```text
switch1>show management api http-commands
Enabled:            Yes
HTTPS server:       running, set to use port 443
HTTP server:        shutdown, set to use port 80
Local HTTP server:  shutdown, no authentication, set to use port 8080
Unix Socket server: shutdown, no authentication
VRFs:               MGMT
Hits:               83
Last hit:           2631 seconds ago
Bytes in:           11348
Bytes out:          335951
Requests:           53
Commands:           64
Duration:           9.242 seconds
SSL Profile:        none
FIPS Mode:          No
QoS DSCP:           0
Log Level:          none
CSP Frame Ancestor: None
TLS Protocols:      1.0 1.1 1.2
   User          Requests       Bytes in       Bytes out    Last hit
------------- -------------- -------------- --------------- ------------------
   arista        2              305            1235         639908 seconds ago
   ansible       51             11043          334716       2631 seconds ago

URLs
-------------------------------------
Management1 : https://10.73.1.105:443

switch1>
```
### Quick test

Run this python script to validate the requirements and the device reachability.
Use your device credentials and IP address.

```python
from jsonrpclib import Server
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
username = "arista"
password = "arista"
ip = "10.100.164.145"
url = "https://" + username + ":" + password + "@" + ip + "/command-api"
switch = Server(url)
result=switch.runCmds(1,['show version'], 'text')
print(result[0]['output'])
```
## List of available tests

The tests are defined in the python module [functions.py](tests/functions.py) in the python package [tests_eos](tests_eos).
Each function returns `True` or `False` (or `None` when it can not run properly).

The [documentation](documentation) directory has the tests documentation:
* [overview.md](documentation/overview.md) file
* [tests_eos.functions.md](documentation/tests_eos.functions.md) file

We indicate the tests we would like to run in a YAML file. Some tests require an input. Here's an [example](tests.yaml).

## Repository usage

* Clone this repository.
* Install the requirements (see above)

### To test devices reachability

* Update the devices inventory [devices.txt](devices.txt) with the devices IP address or hostnames.
* Run the python script [check-devices-reachability.py](check-devices-reachability.py).
* Check the result in the console.

```shell
vi devices.txt
./check-devices-reachability.py --help
./check-devices-reachability.py -i devices.txt -u username
```
### To run tests on devices

* Update the devices inventory [devices.txt](devices.txt) with the devices IP address or hostnames.
* Update the file [tests.yaml](tests.yaml) to indicate the tests you would like to run. Some tests require an input. In that case, provide it using the same YAML file.
* Run the python script [check-devices.py](check-devices.py).
* Check the result in the output file.

```shell
vi devices.txt
vi tests.yaml
./check-devices.py --help
./check-devices.py -i devices.txt -t tests.yaml -o output.txt -u username
cat output.txt
```

### To collect commands output from EOS devices

* Update the devices inventory [devices.txt](devices.txt) with your devices IP address or hostnames.
* Update the EOS commands list [eos-commands.yaml](eos-commands.yaml) you would like to collect from the devices in text or JSON format.
* Run the python script [collect-eos-commands.py](collect-eos-commands.py).
* Check the output in the output directory.


```shell
vi devices-list.text
vi eos-commands.yaml
./collect-eos-commands.py --help
./collect-eos-commands.py -i devices.txt -c eos-commands.yaml -o outdir -u username
ls outdir
```

### To clear counters on EOS devices

* Update the devices inventory [devices.txt](devices.txt) with your devices IP address or hostnames.
* Run the python script [clear_counters.py](clear_counters.py).

```shell
vi devices-list.text
./clear_counters.py --help
./clear_counters.py -i devices.txt -u username
```
### To clear on devices the list of MAC addresses which are blacklisted in EVPN

* Update the devices inventory [devices.txt](devices.txt) with your devices IP address or hostnames.
* Run the python script [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py).

```shell
vi devices-list.text
./evpn-blacklist-recovery.py --help
./evpn-blacklist-recovery.py -i devices.txt -u username
```
### Demo

```
./check-devices.py -u ansible -i devices.txt -o output.txt -t tests.yaml
Device password:
Enable password (if any):
Testing devices .... please be patient ...
Can not connect to device 2.2.2.2
Running tests on device 10.73.1.101 ...
Running tests on device 10.73.1.102 ...
Running tests on device 10.73.1.106 ...
Test results are saved on output.txt
```
```
$ cat output.txt
Thu Feb 10 21:01:59 2022
devices inventory file was devices.txt
devices username was ansible
list of unreachable devices is
2.2.2.2
tests file was tests.yaml

***** Results *****

+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  01.01  |  01.02  |  01.03  |  01.04  |  02.01  |  02.02  |  02.03  |  02.04  |  02.05  |  02.06  |  02.07  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Fail  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Pass  |   Fail  |   Pass  |   Pass  |   Pass  |
|  10.73.1.102  |   Fail  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |
|  10.73.1.106  |   Fail  |   Pass  |   Pass  |   Pass  |   Pass  |   Skip  |   Pass  |   Pass  |   Pass  |   Pass  |   Pass  |
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
|  10.73.1.101  |   Skip  |   Fail  |   Fail  |   Skip  |   Pass  |   Pass  |   Pass  |   Fail  |   Skip  |   Pass  |   Pass  |
|  10.73.1.102  |   Skip  |   Fail  |   Fail  |   Skip  |   Pass  |   Pass  |   Pass  |   Fail  |   Skip  |   Pass  |   Pass  |
|  10.73.1.106  |   Skip  |   Fail  |   Pass  |   Fail  |   Pass  |   Pass  |   Pass  |   Fail  |   Skip  |   Pass  |   Pass  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+---------+
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+
|    devices    |  16.03  |  16.04  |  16.05  |  16.06  |  16.07  |  17.01  |  18.01  |  18.02  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+
|  10.73.1.101  |   Pass  |   Skip  |   Fail  |   Skip  |   Fail  |   Fail  |   Skip  |   Pass  |
|  10.73.1.102  |   Pass  |   Skip  |   Fail  |   Skip  |   Fail  |   Fail  |   Skip  |   Pass  |
|  10.73.1.106  |   Pass  |   Skip  |   Pass  |   Skip  |   Fail  |   Pass  |   Skip  |   Pass  |
+---------------+---------+---------+---------+---------+---------+---------+---------+---------+

***** Tests *****

01.01    {"name": "verify_eos_version", "versions": ["4.25.4M", "4.26.1F"]}
01.02    {"name": "verify_terminattr_version", "versions": ["v1.13.6", "v1.8.0"]}
01.03    {"name": "verify_eos_extensions"}
01.04    {"name": "verify_field_notice_44_resolution"}
02.01    {"name": "verify_uptime", "min": 86400}
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
14.02    {"name": "verify_routing_table_size", "min": 2, "max": 20}
15.01    {"name": "verify_bfd"}
16.01    {"name": "verify_bgp_ipv4_unicast_state"}
16.02    {"name": "verify_bgp_ipv6_unicast_state"}
16.03    {"name": "verify_bgp_evpn_state"}
16.04    {"name": "verify_bgp_rtc_state"}
16.05    {"name": "verify_bgp_evpn_count", "number": 2}
16.06    {"name": "verify_bgp_rtc_count", "number": 2}
16.07    {"name": "verify_bgp_ipv4_unicast_count", "number": 2}
17.01    {"name": "verify_ospf", "number": 3}
18.01    {"name": "verify_igmp_snooping_vlans", "configuration": "disabled", "vlans": [10, 12]}
18.02    {"name": "verify_igmp_snooping_global", "configuration": "enabled"}
```


## Repository structure

### [devices.txt](devices.txt) file

The file [devices.txt](devices.txt) is the devices inventory.

The devices inventory is a text file with the devices IP address or hostnames (if resolvable with DNS or your hosts file). This file has one device per ligne.

### [eos-commands.yaml](eos-commands.yaml) file

The file [eos-commands.yaml](eos-commands.yaml) is a YAML file used to indicated the list of commands output we would like to collect from EOS devices in text or json format.

### [tests.yaml](tests.yaml) file

The file [tests.yaml](tests.yaml) is a YAML file used to indicated the tests we would like to run. It is also used to indicated the parameters used by the tests.
Each test has an identifier which is then used in the tests report.
The tests are defined in the directory [tests_eos](tests_eos).

### [tests_eos](tests_eos) directory

The directory [tests_eos](tests_eos) is a python package.

The python functions to test EOS devices are defined the python module [functions.py](tests_eos/functions.py) in the python package [tests_eos](tests_eos).

### [generate_functions_documentation.py](generate_functions_documentation.py) file

The script [generate_functions_documentation.py](generate_functions_documentation.py) is used to generate the functions documentation in markdown format.
It requires the installation of the package `lazydocs` that is indicated in the file [requirements-dev.txt](requirements-dev.txt)

The functions to test EOS devices are coded in the python module [functions.py](tests_eos/functions.py) in the python package [tests_eos](tests_eos).
These functions have docstrings.
The docstrings are used by the script [generate_functions_documentation.py](generate_functions_documentation.py) to generate the functions documentation in markdown format in the directory [documentation](documentation).

Please refer to the [contribution guide](CONTRIBUTING.md) to get instructions.

### [documentation](documentation) directory

The [documentation](documentation) directory has the tests documentation in markdown format:
* [overview.md](documentation/overview.md) file
* [tests_eos.functions.md](documentation/tests_eos.functions.md) file

### [check-devices-reachability.py](check-devices-reachability.py) file

The python script [check-devices-reachability.py](check-devices-reachability.py) is used to test devices reachability with eAPI.

The python script [check-devices-reachability.py](check-devices-reachability.py) takes as input a text file with the devices IP address or hostnames (when resolvable), and tests devices reachability with eAPI and prints the unreachable devices on the console.

### [clear_counters.py](clear_counters.py) file

The python script [clear_counters.py](clear_counters.py) is used to clear counters on EOS devices.

It takes as input a text file with the devices IP address or hostnames (when resolvable) and clears counters on these devices.

### [collect-eos-commands.py](collect-eos-commands.py) file

The python script [collect-eos-commands.py](collect-eos-commands.py) is used to collect commands output from EOS devices.

The python script [collect-eos-commands.py](collect-eos-commands.py):
* Takes as input:
  * A text file with the devices IP address or hostnames (when resolvable).
  * A YAML file with the list of EOS commands we would like to collect in text or JSON format.
* Collects the EOS commands from the devices, and saves the result in files.

### [check-devices.py](check-devices.py) file

The python script [check-devices.py](check-devices.py) is used to run tests on devices.

The python script [check-devices.py](check-devices.py):
* Imports the python functions defined in the directory [tests_eos](tests_eos).
  * These functions defined the tests.
* Takes as input:
  * A text file with the devices IP address or hostnames (when resolvable).
  * A YAML file with the list of the tests we would like to use and their parameters.
* Runs the tests, and prints the result on the console and saves the result in a file.

### [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py) file

The python script [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py) is used to clear on EOS devices the list of MAC addresses which are blacklisted in EVPN.

The python script [evpn-blacklist-recovery.py](evpn-blacklist-recovery.py) takes as input a text file with the devices IP address or hostnames (when resolvable) and run the command `clear bgp evpn host-flap` on the EOS devices.
### [unit_test.py](unit_test.py) file

The python script [unit_test.py](unit_test.py) is used to test the functions defined in the directory [test_eos](test_eos) without using actual EOS devices.
It requires the installation of the package `pytest` that is indicated in the file [requirements-dev.txt](requirements-dev.txt)

### [mock_data](mock_data) directory

The [mock_data](mock_data) directory has data used by the python script [unit_test.py](unit_test.py) to test the functions defined in the directory [test_eos](test_eos) without using actual EOS devices.

## Contribution guide

Contributions are welcome.
The contribution guide is [CONTRIBUTING.md](CONTRIBUTING.md)

## Credits

Thank you to [Paul Lavelle](https://github.com/paullavelle), [Colin MacGiollaEáin](https://github.com/colinmacgiolla), [Matthieu Tache](https://github.com/mtache), [Angélique Phillipps](https://github.com/aphillipps), [Thomas Grimonet](https://github.com/titom73), [Onur Gashi](https://github.com/onurgashi) and [Khelil Sator](https://github.com/ksator) for their contributions and guidances.
