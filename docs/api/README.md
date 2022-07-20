<!-- markdownlint-disable -->

# API Overview

## Modules

- [`inventory`](./inventory.md#module-inventory): Inventory Module for ANTA.
- [`inventory.exceptions`](./inventory.exceptions.md#module-inventoryexceptions): Manage Exception in Inventory module.
- [`inventory.models`](./inventory.models.md#module-inventorymodels): Models related to inventory management.
- [`result_manager`](./result_manager.md#module-result_manager): Result Manager Module for ANTA.
- [`result_manager.models`](./result_manager.models.md#module-result_managermodels): Models related to anta.result_manager module.
- [`result_manager.report`](./result_manager.report.md#module-result_managerreport): Report management for ANTA.
- [`tests`](./tests.md#module-tests): Module that defines various functions to test EOS devices.

## Classes

- [`inventory.AntaInventory`](./inventory.md#class-antainventory): Inventory Abstraction for ANTA framework.
- [`exceptions.InventoryIncorrectSchema`](./inventory.exceptions.md#class-inventoryincorrectschema): Error when user data does not follow ANTA schema.
- [`exceptions.InventoryRootKeyErrors`](./inventory.exceptions.md#class-inventoryrootkeyerrors): Error raised when inventory root key is not found.
- [`exceptions.InventoryUnknownFormat`](./inventory.exceptions.md#class-inventoryunknownformat): Error when inventory format output is not a supported one.
- [`models.AntaInventoryHost`](./inventory.models.md#class-antainventoryhost): Host definition for user's inventory.
- [`models.AntaInventoryInput`](./inventory.models.md#class-antainventoryinput): User's inventory model.
- [`models.AntaInventoryNetwork`](./inventory.models.md#class-antainventorynetwork): Network definition for user's inventory.
- [`models.AntaInventoryRange`](./inventory.models.md#class-antainventoryrange): IP Range definition for user's inventory.
- [`models.InventoryDevice`](./inventory.models.md#class-inventorydevice): Inventory model exposed by Inventory class.
- [`models.InventoryDevices`](./inventory.models.md#class-inventorydevices): Inventory model to list all InventoryDevice entries.
- [`result_manager.ResultManager`](./result_manager.md#class-resultmanager): ResultManager Helper to manage Test Results and generate reports.
- [`models.ListResult`](./result_manager.models.md#class-listresult): List result for all tests on all devices.
- [`models.TestResult`](./result_manager.models.md#class-testresult): Describe result of a test from a single device.
- [`report.Colors`](./result_manager.report.md#class-colors): Manage colors for output.
- [`report.TableReport`](./result_manager.report.md#class-tablereport): TableReport Generate a Table based on tabulate and TestResult.

## Functions

- [`tests.verify_adverse_drops`](./tests.md#function-verify_adverse_drops): Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.
- [`tests.verify_agent_logs`](./tests.md#function-verify_agent_logs): Verifies there is no agent crash reported on the device.
- [`tests.verify_bfd`](./tests.md#function-verify_bfd): Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).
- [`tests.verify_bgp_evpn_count`](./tests.md#function-verify_bgp_evpn_count): Verifies all EVPN BGP sessions are established (default VRF)
- [`tests.verify_bgp_evpn_state`](./tests.md#function-verify_bgp_evpn_state): Verifies all EVPN BGP sessions are established (default VRF).
- [`tests.verify_bgp_ipv4_unicast_count`](./tests.md#function-verify_bgp_ipv4_unicast_count): Verifies all IPv4 unicast BGP sessions are established
- [`tests.verify_bgp_ipv4_unicast_state`](./tests.md#function-verify_bgp_ipv4_unicast_state): Verifies all IPv4 unicast BGP sessions are established (for all VRF)
- [`tests.verify_bgp_ipv6_unicast_state`](./tests.md#function-verify_bgp_ipv6_unicast_state): Verifies all IPv6 unicast BGP sessions are established (for all VRF)
- [`tests.verify_bgp_rtc_count`](./tests.md#function-verify_bgp_rtc_count): Verifies all RTC BGP sessions are established (default VRF)
- [`tests.verify_bgp_rtc_state`](./tests.md#function-verify_bgp_rtc_state): Verifies all RTC BGP sessions are established (default VRF).
- [`tests.verify_coredump`](./tests.md#function-verify_coredump): Verifies there is no core file.
- [`tests.verify_cpu_utilization`](./tests.md#function-verify_cpu_utilization): Verifies the CPU utilization is less than 75%.
- [`tests.verify_environment_cooling`](./tests.md#function-verify_environment_cooling): Verifies the fans status is OK.
- [`tests.verify_environment_power`](./tests.md#function-verify_environment_power): Verifies the power supplies status is OK.
- [`tests.verify_eos_extensions`](./tests.md#function-verify_eos_extensions): Verifies all EOS extensions installed on the device are enabled for boot persistence.
- [`tests.verify_eos_version`](./tests.md#function-verify_eos_version): Verifies the device is running one of the allowed EOS version.
- [`tests.verify_field_notice_44_resolution`](./tests.md#function-verify_field_notice_44_resolution): Verifies the device is using an Aboot version that fix the bug discussed
- [`tests.verify_filesystem_utilization`](./tests.md#function-verify_filesystem_utilization): Verifies each partition on the disk is used less than 75%.
- [`tests.verify_igmp_snooping_global`](./tests.md#function-verify_igmp_snooping_global): Verifies the IGMP snooping global configuration.
- [`tests.verify_igmp_snooping_vlans`](./tests.md#function-verify_igmp_snooping_vlans): Verifies the IGMP snooping configuration for some VLANs.
- [`tests.verify_illegal_lacp`](./tests.md#function-verify_illegal_lacp): Verifies there is no illegal LACP packets received.
- [`tests.verify_interface_discards`](./tests.md#function-verify_interface_discards): Verifies interfaces packet discard counters are equal to zero.
- [`tests.verify_interface_errdisabled`](./tests.md#function-verify_interface_errdisabled): Verifies there is no interface in error disable state.
- [`tests.verify_interface_errors`](./tests.md#function-verify_interface_errors): Verifies interfaces error counters are equal to zero.
- [`tests.verify_interface_utilization`](./tests.md#function-verify_interface_utilization): Verifies interfaces utilization is below 75%.
- [`tests.verify_interfaces_status`](./tests.md#function-verify_interfaces_status): Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.
- [`tests.verify_loopback_count`](./tests.md#function-verify_loopback_count): Verifies the number of loopback interfaces on the device is the one we expect.
- [`tests.verify_memory_utilization`](./tests.md#function-verify_memory_utilization): Verifies the memory utilization is less than 75%.
- [`tests.verify_mlag_config_sanity`](./tests.md#function-verify_mlag_config_sanity): Verifies there is no MLAG config-sanity warnings.
- [`tests.verify_mlag_interfaces`](./tests.md#function-verify_mlag_interfaces): Verifies there is no inactive or active-partial MLAG interfaces.
- [`tests.verify_mlag_status`](./tests.md#function-verify_mlag_status): Verifies the MLAG status:
- [`tests.verify_ntp`](./tests.md#function-verify_ntp): Verifies NTP is synchronised.
- [`tests.verify_ospf_count`](./tests.md#function-verify_ospf_count): Verifies the number of OSPF neighbors in FULL state is the one we expect.
- [`tests.verify_ospf_state`](./tests.md#function-verify_ospf_state): Verifies all OSPF neighbors are in FULL state.
- [`tests.verify_portchannels`](./tests.md#function-verify_portchannels): Verifies there is no inactive port in port channels.
- [`tests.verify_reload_cause`](./tests.md#function-verify_reload_cause): Verifies the last reload of the device was requested by a user.
- [`tests.verify_routing_protocol_model`](./tests.md#function-verify_routing_protocol_model): Verifies the configured routing protocol model is the one we expect.
- [`tests.verify_routing_table_size`](./tests.md#function-verify_routing_table_size): Verifies the size of the IP routing table (default VRF).
- [`tests.verify_running_config_diffs`](./tests.md#function-verify_running_config_diffs): Verifies there is no difference between the running-config and the startup-config.
- [`tests.verify_spanning_tree_blocked_ports`](./tests.md#function-verify_spanning_tree_blocked_ports): Verifies there is no spanning-tree blocked ports.
- [`tests.verify_storm_control_drops`](./tests.md#function-verify_storm_control_drops): Verifies the device did not drop packets due its to storm-control configuration.
- [`tests.verify_svi`](./tests.md#function-verify_svi): Verifies there is no interface vlan down.
- [`tests.verify_syslog`](./tests.md#function-verify_syslog): Verifies the device had no syslog message with a severity of warning (or a more severe message)
- [`tests.verify_system_temperature`](./tests.md#function-verify_system_temperature): Verifies the device temperature is currently OK
- [`tests.verify_tcam_profile`](./tests.md#function-verify_tcam_profile): Verifies the configured TCAM profile is the expected one.
- [`tests.verify_terminattr_version`](./tests.md#function-verify_terminattr_version): Verifies the device is running one of the allowed TerminAttr version.
- [`tests.verify_transceiver_temperature`](./tests.md#function-verify_transceiver_temperature): Verifies the transceivers temperature is currently OK
- [`tests.verify_transceivers_manufacturers`](./tests.md#function-verify_transceivers_manufacturers): Verifies the device is only using transceivers from supported manufacturers.
- [`tests.verify_unified_forwarding_table_mode`](./tests.md#function-verify_unified_forwarding_table_mode): Verifies the device is using the expected Unified Forwarding Table mode.
- [`tests.verify_uptime`](./tests.md#function-verify_uptime): Verifies the device uptime is higher than a value.
- [`tests.verify_vxlan`](./tests.md#function-verify_vxlan): Verifies the interface vxlan 1 status is up/up.
- [`tests.verify_vxlan_config_sanity`](./tests.md#function-verify_vxlan_config_sanity): Verifies there is no VXLAN config-sanity warnings.
- [`tests.verify_zerotouch`](./tests.md#function-verify_zerotouch): Verifies ZeroTouch is disabled.


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
