# Devices testing demo

To test devices, once you are done with the installation, you simply need:

- A text file with your devices hostname or IP address. Here's an [example](examples/devices.txt).
- A YAML file with the tests you would like to run. Some tests require an argument. Here's an [example](examples/tests.yaml).

Then you can run the Python script [check-devices.py](scripts/check-devices.py):

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

Then you can check the tests result in the output file:

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
