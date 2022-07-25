<!-- markdownlint-disable -->

# API Overview

## Modules

- [`inventory`](./inventory.md#module-inventory): Inventory Module for ANTA.
- [`inventory.exceptions`](./inventory.exceptions.md#module-inventoryexceptions): Manage Exception in Inventory module.
- [`inventory.models`](./inventory.models.md#module-inventorymodels): Models related to inventory management.
- [`loader`](./loader.md#module-loader): Loader that parses a YAML test catalog and imports corresponding Python functions
- [`result_manager`](./result_manager.md#module-result_manager): Result Manager Module for ANTA.
- [`result_manager.models`](./result_manager.models.md#module-result_managermodels): Models related to anta.result_manager module.
- [`result_manager.report`](./result_manager.report.md#module-result_managerreport): Report management for ANTA.
- [`tests`](./tests.md#module-tests)
- [`tests.configuration`](./tests.configuration.md#module-testsconfiguration): Test functions related to the device configuration
- [`tests.hardware`](./tests.hardware.md#module-testshardware): Test functions related to the hardware or environement
- [`tests.interfaces`](./tests.interfaces.md#module-testsinterfaces): Test functions related to the device interfaces
- [`tests.mlag`](./tests.mlag.md#module-testsmlag): Test functions related to Multi-Chassis LAG
- [`tests.multicast`](./tests.multicast.md#module-testsmulticast): Test functions related to multicast
- [`tests.profiles`](./tests.profiles.md#module-testsprofiles): Test functions related to ASIC profiles
- [`tests.routing`](./tests.routing.md#module-testsrouting)
- [`tests.routing.bgp`](./tests.routing.bgp.md#module-testsroutingbgp): BGP test functions
- [`tests.routing.generic`](./tests.routing.generic.md#module-testsroutinggeneric): Generic routing test functions
- [`tests.routing.ospf`](./tests.routing.ospf.md#module-testsroutingospf): OSPF test functions
- [`tests.software`](./tests.software.md#module-testssoftware): Test functions related to the EOS software
- [`tests.system`](./tests.system.md#module-testssystem): Test functions related to system-level features and protocols
- [`tests.vxlan`](./tests.vxlan.md#module-testsvxlan): Test functions related to VXLAN

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
- [`result_manager.ResultManager`](./result_manager.md#class-resultmanager): Helper to manage Test Results and generate reports.
- [`models.ListResult`](./result_manager.models.md#class-listresult): List result for all tests on all devices.
- [`models.TestResult`](./result_manager.models.md#class-testresult): Describe result of a test from a single device.
- [`report.Colors`](./result_manager.report.md#class-colors): Manage colors for output.
- [`report.TableReport`](./result_manager.report.md#class-tablereport): TableReport Generate a Table based on tabulate and TestResult.

## Functions

- [`loader.parse_catalog`](./loader.md#function-parse_catalog)
- [`configuration.verify_running_config_diffs`](./tests.configuration.md#function-verify_running_config_diffs): Verifies there is no difference between the running-config and the startup-config.
- [`configuration.verify_zerotouch`](./tests.configuration.md#function-verify_zerotouch): Verifies ZeroTouch is disabled.
- [`hardware.verify_adverse_drops`](./tests.hardware.md#function-verify_adverse_drops): Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.
- [`hardware.verify_environment_cooling`](./tests.hardware.md#function-verify_environment_cooling): Verifies the fans status is OK.
- [`hardware.verify_environment_power`](./tests.hardware.md#function-verify_environment_power): Verifies the power supplies status is OK.
- [`hardware.verify_system_temperature`](./tests.hardware.md#function-verify_system_temperature): Verifies the device temperature is currently OK
- [`hardware.verify_transceiver_temperature`](./tests.hardware.md#function-verify_transceiver_temperature): Verifies the transceivers temperature is currently OK
- [`hardware.verify_transceivers_manufacturers`](./tests.hardware.md#function-verify_transceivers_manufacturers): Verifies the device is only using transceivers from supported manufacturers.
- [`interfaces.verify_illegal_lacp`](./tests.interfaces.md#function-verify_illegal_lacp): Verifies there is no illegal LACP packets received.
- [`interfaces.verify_interface_discards`](./tests.interfaces.md#function-verify_interface_discards): Verifies interfaces packet discard counters are equal to zero.
- [`interfaces.verify_interface_errdisabled`](./tests.interfaces.md#function-verify_interface_errdisabled): Verifies there is no interface in error disable state.
- [`interfaces.verify_interface_errors`](./tests.interfaces.md#function-verify_interface_errors): Verifies interfaces error counters are equal to zero.
- [`interfaces.verify_interface_utilization`](./tests.interfaces.md#function-verify_interface_utilization): Verifies interfaces utilization is below 75%.
- [`interfaces.verify_interfaces_status`](./tests.interfaces.md#function-verify_interfaces_status): Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.
- [`interfaces.verify_loopback_count`](./tests.interfaces.md#function-verify_loopback_count): Verifies the number of loopback interfaces on the device is the one we expect.
- [`interfaces.verify_portchannels`](./tests.interfaces.md#function-verify_portchannels): Verifies there is no inactive port in port channels.
- [`interfaces.verify_spanning_tree_blocked_ports`](./tests.interfaces.md#function-verify_spanning_tree_blocked_ports): Verifies there is no spanning-tree blocked ports.
- [`interfaces.verify_storm_control_drops`](./tests.interfaces.md#function-verify_storm_control_drops): Verifies the device did not drop packets due its to storm-control configuration.
- [`interfaces.verify_svi`](./tests.interfaces.md#function-verify_svi): Verifies there is no interface vlan down.
- [`mlag.verify_mlag_config_sanity`](./tests.mlag.md#function-verify_mlag_config_sanity): Verifies there is no MLAG config-sanity inconsistencies.
- [`mlag.verify_mlag_interfaces`](./tests.mlag.md#function-verify_mlag_interfaces): Verifies there is no inactive or active-partial MLAG interfaces.
- [`mlag.verify_mlag_status`](./tests.mlag.md#function-verify_mlag_status): Verifies the MLAG status:
- [`multicast.verify_igmp_snooping_global`](./tests.multicast.md#function-verify_igmp_snooping_global): Verifies the IGMP snooping global configuration.
- [`multicast.verify_igmp_snooping_vlans`](./tests.multicast.md#function-verify_igmp_snooping_vlans): Verifies the IGMP snooping configuration for some VLANs.
- [`profiles.verify_tcam_profile`](./tests.profiles.md#function-verify_tcam_profile): Verifies the configured TCAM profile is the expected one.
- [`profiles.verify_unified_forwarding_table_mode`](./tests.profiles.md#function-verify_unified_forwarding_table_mode): Verifies the device is using the expected Unified Forwarding Table mode.
- [`bgp.verify_bgp_evpn_count`](./tests.routing.bgp.md#function-verify_bgp_evpn_count): Verifies all EVPN BGP sessions are established (default VRF)
- [`bgp.verify_bgp_evpn_state`](./tests.routing.bgp.md#function-verify_bgp_evpn_state): Verifies all EVPN BGP sessions are established (default VRF).
- [`bgp.verify_bgp_ipv4_unicast_count`](./tests.routing.bgp.md#function-verify_bgp_ipv4_unicast_count): Verifies all IPv4 unicast BGP sessions are established
- [`bgp.verify_bgp_ipv4_unicast_state`](./tests.routing.bgp.md#function-verify_bgp_ipv4_unicast_state): Verifies all IPv4 unicast BGP sessions are established (for all VRF)
- [`bgp.verify_bgp_ipv6_unicast_state`](./tests.routing.bgp.md#function-verify_bgp_ipv6_unicast_state): Verifies all IPv6 unicast BGP sessions are established (for all VRF)
- [`bgp.verify_bgp_rtc_count`](./tests.routing.bgp.md#function-verify_bgp_rtc_count): Verifies all RTC BGP sessions are established (default VRF)
- [`bgp.verify_bgp_rtc_state`](./tests.routing.bgp.md#function-verify_bgp_rtc_state): Verifies all RTC BGP sessions are established (default VRF).
- [`generic.verify_bfd`](./tests.routing.generic.md#function-verify_bfd): Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).
- [`generic.verify_routing_protocol_model`](./tests.routing.generic.md#function-verify_routing_protocol_model): Verifies the configured routing protocol model is the one we expect.
- [`generic.verify_routing_table_size`](./tests.routing.generic.md#function-verify_routing_table_size): Verifies the size of the IP routing table (default VRF).
- [`ospf.verify_ospf_count`](./tests.routing.ospf.md#function-verify_ospf_count): Verifies the number of OSPF neighbors in FULL state is the one we expect.
- [`ospf.verify_ospf_state`](./tests.routing.ospf.md#function-verify_ospf_state): Verifies all OSPF neighbors are in FULL state.
- [`software.verify_eos_extensions`](./tests.software.md#function-verify_eos_extensions): Verifies all EOS extensions installed on the device are enabled for boot persistence.
- [`software.verify_eos_version`](./tests.software.md#function-verify_eos_version): Verifies the device is running one of the allowed EOS version.
- [`software.verify_field_notice_44_resolution`](./tests.software.md#function-verify_field_notice_44_resolution): Verifies the device is using an Aboot version that fix the bug discussed
- [`software.verify_terminattr_version`](./tests.software.md#function-verify_terminattr_version): Verifies the device is running one of the allowed TerminAttr version.
- [`system.verify_agent_logs`](./tests.system.md#function-verify_agent_logs): Verifies there is no agent crash reported on the device.
- [`system.verify_coredump`](./tests.system.md#function-verify_coredump): Verifies there is no core file.
- [`system.verify_cpu_utilization`](./tests.system.md#function-verify_cpu_utilization): Verifies the CPU utilization is less than 75%.
- [`system.verify_filesystem_utilization`](./tests.system.md#function-verify_filesystem_utilization): Verifies each partition on the disk is used less than 75%.
- [`system.verify_memory_utilization`](./tests.system.md#function-verify_memory_utilization): Verifies the memory utilization is less than 75%.
- [`system.verify_ntp`](./tests.system.md#function-verify_ntp): Verifies NTP is synchronised.
- [`system.verify_reload_cause`](./tests.system.md#function-verify_reload_cause): Verifies the last reload of the device was requested by a user.
- [`system.verify_syslog`](./tests.system.md#function-verify_syslog): Verifies the device had no syslog message with a severity of warning (or a more severe message)
- [`system.verify_uptime`](./tests.system.md#function-verify_uptime): Verifies the device uptime is higher than a value.
- [`vxlan.verify_vxlan`](./tests.vxlan.md#function-verify_vxlan): Verifies the interface vxlan 1 status is up/up.
- [`vxlan.verify_vxlan_config_sanity`](./tests.vxlan.md#function-verify_vxlan_config_sanity): Verifies there is no VXLAN config-sanity warnings.


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
