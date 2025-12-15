# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the hardware or environment tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import Field

from anta.custom_types import ModuleStatus, Percent, PositiveInteger, PowerSupplyFanStatus, PowerSupplyStatus
from anta.decorators import skip_on_platforms
from anta.input_models.hardware import AdverseDropThresholds, HardwareInventory, PCIeThresholds
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from collections.abc import Callable


class VerifyTransceiversManufacturers(AntaTest):
    """Verifies if all the transceivers come from approved manufacturers.

    Expected Results
    ----------------
    * Success: The test will pass if all transceivers are from approved manufacturers.
    * Failure: The test will fail if some transceivers are from unapproved manufacturers.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTransceiversManufacturers:
          manufacturers:
            - Not Present
            - Arista Networks
            - Arastra, Inc.
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show inventory", revision=2)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyTransceiversManufacturers test."""

        manufacturers: list[str]
        """List of approved transceivers manufacturers."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTransceiversManufacturers."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for port, value in command_output["xcvrSlots"].items():
            # Atomic result
            result = self.result.add(description=f"Port: {port}", status=AntaTestStatus.SUCCESS)

            if not (mfg_name := value["mfgName"]):
                # Cover transceiver issues like 'xcvr-unsupported'
                result.is_failure("Manufacturer name is not available - This may indicate an unsupported or faulty transceiver")
                continue

            if mfg_name not in self.inputs.manufacturers:
                result.is_failure(f"Transceiver is from unapproved manufacturers - Expected: {', '.join(self.inputs.manufacturers)} Actual: {mfg_name}")


class VerifyTemperature(AntaTest):
    """Verifies if the device temperature is within acceptable limits.

    Expected Results
    ----------------
    * Success: The test will pass if the system temperature is `temperatureOk` and if checked, all sensor statuses and temperatures are within operational limits.
    * Failure: The test will fail if the system temperature is not `temperatureOk` or if any checked sensor reports a hardware fault or high temperature.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTemperature:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTemperature test."""

        check_temp_sensors: bool = False
        """If True, also verifies the hardware status and temperature of individual sensors."""
        failure_margin: PositiveInteger = Field(default=5)
        """"Proactive failure margin in °C. The test will fail if the current temperature is above the overheat threshold minus this margin."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTemperature."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output.get("systemStatus", "")

        # Verify system temperature status
        if temperature_status != "temperatureOk":
            self.result.is_failure(f"Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: {temperature_status}")

        # Check all sensors only if check_temp_sensors knob is set.
        if not self.inputs.check_temp_sensors:
            return

        temp_sensors = command_output["tempSensors"]
        for power_supply in command_output["powerSupplySlots"]:
            temp_sensors.extend(power_supply["tempSensors"])

        for card_slot in command_output["cardSlots"]:
            temp_sensors.extend(card_slot["tempSensors"])

        for sensor in temp_sensors:
            # Account for PhyAlaska chips that don't give current temp in 7020TR
            if "PhyAlaska" in (sensor_desc := sensor["description"]):
                self.logger.debug("Sensor: %s Description: %s has been ignored due to PhyAlaska in sensor description", sensor, sensor_desc)
                continue

            # Verify sensor hardware state
            if sensor["hwStatus"] != "ok":
                self.result.is_failure(f"Sensor: {sensor['name']} Description: {sensor_desc} - Invalid hardware status - Expected: ok Actual: {sensor['hwStatus']}")
                continue

            # Verify sensor current temperature
            overheat_threshold = sensor["overheatThreshold"]
            effective_threshold = overheat_threshold - self.inputs.failure_margin
            if (act_temp := sensor["currentTemperature"]) > effective_threshold:
                self.result.is_failure(
                    f"Sensor: {sensor['name']} Description: {sensor_desc} - Temperature is getting high - Expected: <= {effective_threshold:.2f}°C "
                    f"(Overheat: {overheat_threshold:.2f}°C - Margin: {self.inputs.failure_margin}°C) Actual: {act_temp:.2f}°C"
                )


class VerifyTransceiversTemperature(AntaTest):
    """Verifies if all the transceivers are operating at an acceptable temperature.

    Expected Results
    ----------------
    * Success: The test will pass if all transceivers status are OK: 'ok'.
    * Failure: The test will fail if some transceivers are NOT OK.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTransceiversTemperature:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature transceiver", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTransceiversTemperature."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        sensors = command_output.get("tempSensors", "")

        for sensor in sensors:
            if sensor["hwStatus"] != "ok":
                self.result.is_failure(f"Sensor: {sensor['name']} - Invalid hardware state - Expected: ok Actual: {sensor['hwStatus']}")
            if sensor["alertCount"] != 0:
                self.result.is_failure(f"Sensor: {sensor['name']} - Incorrect alert counter - Expected: 0 Actual: {sensor['alertCount']}")


class VerifyEnvironmentSystemCooling(AntaTest):
    """Verifies the device's system cooling status.

    Expected Results
    ----------------
    * Success: The test will pass if the system cooling status is OK: 'coolingOk'.
    * Failure: The test will fail if the system cooling status is NOT OK.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyEnvironmentSystemCooling:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment cooling", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentSystemCooling."""
        command_output = self.instance_commands[0].json_output
        sys_status = command_output.get("systemStatus", "")
        self.result.is_success()
        if sys_status != "coolingOk":
            self.result.is_failure(f"Device system cooling status invalid - Expected: coolingOk Actual: {sys_status}")


class VerifyEnvironmentCooling(AntaTest):
    """Verifies the status of power supply fans and all fan trays.

    Expected Results
    ----------------
    * Success: The test will pass if all fans have a status within the accepted states and if a speed limit is provided,
     their speed is within that limit.
    * Failure: The test will fail if any fan status is not in the accepted states or if any fan configured speed exceeds
     the speed limit, if provided.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyEnvironmentCooling:
          states:
            - ok
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment cooling", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEnvironmentCooling test."""

        states: list[PowerSupplyFanStatus]
        """List of accepted states of fan status."""
        configured_fan_speed_limit: PositiveInteger | None = None
        """The upper limit for the configured fan speed."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentCooling."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        # First go through power supplies fans
        for power_supply in command_output.get("powerSupplySlots", []):
            for fan in power_supply.get("fans", []):
                # Verify the fan status
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(
                        f"Power Slot: {power_supply['label']} Fan: {fan['label']} - Invalid state - Expected: {', '.join(self.inputs.states)} Actual: {state}"
                    )
                # Verify the configured fan speed
                elif self.inputs.configured_fan_speed_limit and fan["configuredSpeed"] > self.inputs.configured_fan_speed_limit:
                    self.result.is_failure(
                        f"Power Slot: {power_supply['label']} Fan: {fan['label']} - High fan speed - Expected: <= {self.inputs.configured_fan_speed_limit} "
                        f"Actual: {fan['configuredSpeed']}"
                    )
        # Then go through fan trays
        for fan_tray in command_output.get("fanTraySlots", []):
            for fan in fan_tray.get("fans", []):
                # Verify the fan status
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(
                        f"Fan Tray: {fan_tray['label']} Fan: {fan['label']} - Invalid state - Expected: {', '.join(self.inputs.states)} Actual: {state}"
                    )
                # Verify the configured fan speed
                elif self.inputs.configured_fan_speed_limit and fan["configuredSpeed"] > self.inputs.configured_fan_speed_limit:
                    self.result.is_failure(
                        f"Fan Tray: {fan_tray['label']} Fan: {fan['label']} - High fan speed - Expected: <= {self.inputs.configured_fan_speed_limit} "
                        f"Actual: {fan['configuredSpeed']}"
                    )


class VerifyEnvironmentPower(AntaTest):
    """Verifies the power supplies state and input voltage.

    Expected Results
    ----------------
    * Success: The test will pass if all power supplies are in an accepted state and their input voltage is greater than or equal to `min_input_voltage`
    (if provided).
    * Failure: The test will fail if any power supply is in an unaccepted state or its input voltage is less than `min_input_voltage` (if provided).

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyEnvironmentPower:
          states:
            - ok
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment power", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEnvironmentPower test."""

        states: list[PowerSupplyStatus]
        """List of accepted states for power supplies."""
        min_input_voltage: PositiveInteger | None = None
        """Optional minimum input voltage (Volts) to verify."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentPower."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        power_supplies = command_output.get("powerSupplies", "{}")
        for power_supply, value in dict(power_supplies).items():
            if (state := value["state"]) not in self.inputs.states:
                self.result.is_failure(f"Power Slot: {power_supply} - Invalid power supplies state - Expected: {', '.join(self.inputs.states)} Actual: {state}")

            # Verify if the power supply voltage is greater than the minimum input voltage
            if self.inputs.min_input_voltage and value["inputVoltage"] < self.inputs.min_input_voltage:
                self.result.is_failure(
                    f"Power Supply: {power_supply} - Input voltage mismatch - Expected: >= {self.inputs.min_input_voltage} Actual: {value['inputVoltage']}"
                )


class VerifyAdverseDrops(AntaTest):
    """Verifies there are no adverse drops exceeding defined thresholds.

    Compatible with Arista 7280R, 7500R, 7800R and 7700R series platforms supporting hardware counters.

    !!! note
        The `ReassemblyErrors` counter on a FAP can increment as a direct symptom of `FCS errors` on one of its ingress
        interfaces. This test can be configured to not fail on `ReassemblyErrors` if this correlation is found, treating
        them as an expected side effect of the initial FCS errors.

    Expected Results
    ----------------
    * Success: The test will pass if all adverse drop counters are within their defined thresholds.
    * Failure: The test will fail if any adverse drop counter exceeds its threshold.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyAdverseDrops:
          thresholds:  # Optional
            minute: 3
            ten_minute: 20
            hour: 100
            day: 500
            week: 1000
          always_fail_on_reassembly_errors: false
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show hardware counter drop rates", revision=1),
        AntaCommand(command="show platform fap mapping", revision=5),
        AntaCommand(command="show interfaces counters errors", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyAdverseDrops test."""

        thresholds: AdverseDropThresholds = Field(default_factory=AdverseDropThresholds)
        """Adverse drop counter thresholds."""
        always_fail_on_reassembly_errors: bool = True
        """If False, the test will not fail on `ReassemblyErrors` if the same FAP reports FCS errors on one of its interfaces."""

    def _get_faps_with_errors(self, arad_mappings_output: list[dict[str, Any]], interfaces_with_errors: set[str]) -> dict[str, set[str]]:
        """Build a mapping of FAP names to a set of their interfaces that have reported FCS errors."""
        faps_with_errors = defaultdict(set)
        for fap in arad_mappings_output:
            for port_mapping in fap["portMappings"].values():
                interface_name = port_mapping["interface"]
                if interface_name.startswith("Ethernet") and interface_name in interfaces_with_errors:
                    faps_with_errors[fap["fapName"]].add(interface_name)
        return dict(faps_with_errors)

    def _get_interfaces_with_errors(self, interface_error_counters_output: dict[str, dict[str, int]]) -> set[str]:
        """Parse interface counters to find all interfaces with non-zero FCS errors."""
        return {intf_name for intf_name, counters in interface_error_counters_output.items() if counters["fcsErrors"] > 0}

    def _verify_drop_event_thresholds(self, fap_name: str, drop_event: dict[str, Any]) -> None:
        """Check the drop event against each threshold defined in the input."""
        # Iterate over the fields of the Pydantic Input model
        for field_name, field_info in AdverseDropThresholds.model_fields.items():
            # Get the eAPI key from the Field alias (e.g., "dropInLastMinute")
            eapi_key = field_info.alias

            if eapi_key not in drop_event:
                continue

            actual_value = drop_event[eapi_key]
            threshold_value = getattr(self.inputs.thresholds, field_name)

            if actual_value > threshold_value:
                counter_name = drop_event["counterName"]
                failure_msg_prefix = f"FAP: {fap_name} Counter: {counter_name}"

                # Get the human-readable period from the Field description
                human_readable_period = field_info.description
                self.result.is_failure(
                    f"{failure_msg_prefix} - {human_readable_period} rate above threshold - Expected: <= {threshold_value} Actual: {actual_value}"
                )

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAdverseDrops."""
        self.result.is_success()

        # Extract JSON output from the commands
        show_hardware_counter_drop_rates_output = self.instance_commands[0].json_output
        show_platform_fap_mapping_output = self.instance_commands[1].json_output
        show_interfaces_counters_errors_output = self.instance_commands[2].json_output

        # Pre-build mappings for efficient lookups later
        interfaces_with_errors = self._get_interfaces_with_errors(show_interfaces_counters_errors_output["interfaceErrorCounters"])
        faps_with_errors = self._get_faps_with_errors(show_platform_fap_mapping_output["aradMappings"], interfaces_with_errors)

        for fap_name, fap_data in show_hardware_counter_drop_rates_output["dropEvents"].items():
            for drop_event in fap_data["dropEvent"]:
                # Skip events that are not 'Adverse' or have a zero drop count, as they are not relevant
                if drop_event["counterType"] != "Adverse" or drop_event["dropCount"] == 0:
                    continue

                # Special handling for 'ReassemblyErrors': log a warning message instead of failing under specific conditions
                if drop_event["counterName"] == "ReassemblyErrors" and not self.inputs.always_fail_on_reassembly_errors and fap_name in faps_with_errors:
                    fap_interfaces_with_errors = ", ".join(sorted(faps_with_errors[fap_name]))
                    self.logger.warning(
                        "%s on %s had reassembly errors but interfaces on the same FAP had FCS errors: %s", fap_name, self.device.name, fap_interfaces_with_errors
                    )
                    continue

                # Verify each threshold
                self._verify_drop_event_thresholds(fap_name, drop_event)


class VerifySupervisorRedundancy(AntaTest):
    """Verifies the redundancy protocol configured on the active supervisor.

    Expected Results
    ----------------
    * Success: The test will pass if the expected redundancy protocol is configured and operational, and if switchover is ready.
    * Failure: The test will fail if the expected redundancy protocol is not configured, not operational, or if switchover is not ready.
    * Skipped: The test will be skipped if the peer supervisor card is not inserted.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifySupervisorRedundancy:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show redundancy status", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySupervisorRedundancy test."""

        redundancy_proto: Literal["sso", "rpr", "simplex"] = "sso"
        """Configured redundancy protocol."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySupervisorRedundancy."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Verify peer supervisor card insertion
        if command_output["peerState"] == "notInserted":
            self.result.is_skipped("Peer supervisor card not inserted")
            return

        # Verify that the expected redundancy protocol is configured
        if (act_proto := command_output["configuredProtocol"]) != self.inputs.redundancy_proto:
            self.result.is_failure(f"Configured redundancy protocol mismatch - Expected {self.inputs.redundancy_proto} Actual: {act_proto}")

        # Verify that the expected redundancy protocol configured and operational
        elif (act_proto := command_output["operationalProtocol"]) != self.inputs.redundancy_proto:
            self.result.is_failure(f"Operational redundancy protocol mismatch - Expected {self.inputs.redundancy_proto} Actual: {act_proto}")

        # Verify that the expected redundancy protocol configured, operational and switchover ready
        elif not command_output["switchoverReady"]:
            self.result.is_failure(f"Redundancy protocol switchover status mismatch - Expected: True Actual: {command_output['switchoverReady']}")


class VerifyPCIeErrors(AntaTest):
    """Verifies PCIe device error counters.

    Expected Results
    ----------------
    * Success: The test will pass if the correctable, non-fatal, and fatal error counts for all PCIe devices are below their defined thresholds.
    * Failure: The test will fail if any PCIe device has a correctable, non-fatal, or fatal error count above its defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyPCIeErrors:
          thresholds:  # Optional
            correctable_errors: 10000
            non_fatal_errors: 30
            fatal_errors: 30
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show pci", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyPCIeErrors test."""

        thresholds: PCIeThresholds = Field(default_factory=PCIeThresholds)

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPCIeErrors."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for pci_id, id_details in command_output["pciIds"].items():
            for field_name, field_info in PCIeThresholds.model_fields.items():
                actual_value = id_details[field_info.alias]
                threshold_value = getattr(self.inputs.thresholds, field_name)
                if actual_value > threshold_value:
                    self.result.is_failure(
                        f"PCI Name: {id_details['name']} PCI ID: {pci_id} - {field_info.description} above threshold - "
                        f"Expected: <= {threshold_value} Actual: {actual_value}"
                    )


class VerifyAbsenceOfLinecards(AntaTest):
    """Verifies that specific linecards are not present in the device inventory.

    This is useful for confirming that hardware has been successfully decommissioned.

    Expected Results
    ----------------
    * Success: The test will pass if all provided linecard serial numbers are found.
    * Failure: The test will fail if any of the provided linecard serial numbers are found.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyAbsenceOfLinecards:
          serial_numbers:
            - VJM24220VJ1
            - VJM24230VJ2
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show inventory", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyAbsenceOfLinecards test."""

        serial_numbers: list[str]
        """A list of linecard serial numbers that should NOT be in the device."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAbsenceOfLinecards."""
        self.result.is_success()
        inventory = self.instance_commands[0].json_output
        installed_serials = {details["serialNum"] for details in inventory["cardSlots"].values()}

        # Find which of the decommissioned cards are still present
        found_serials = set(self.inputs.serial_numbers).intersection(installed_serials)
        if found_serials:
            self.result.is_failure(f"Decommissioned linecards found in inventory: {', '.join(sorted(found_serials))}")


class VerifyChassisHealth(AntaTest):
    """Verifies the health of the hardware chassis components.

    Compatible with Arista 7280R, 7500R, 7800R and 7700R series platforms.

    Expected Results
    ----------------
    * Success:  The test will pass if all linecards and fabric cards are initialized and the number of fabric interrupts does not exceed the specified threshold.
    * Failure: The test will fail if any linecards or fabric card is not initialized, or if the count of fabric interrupts is over the threshold.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyChassisHealth:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show platform sand health", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyChassisHealth test."""

        max_fabric_interrupts: int = 0
        """The maximum number of allowed fabric interrupts."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyChassisHealth."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Verify all line cards for initialization
        if linecards_not_initialized := command_output["linecardsNotInitialized"]:
            for card in linecards_not_initialized:
                self.result.is_failure(f"Linecard: {card} - Not initialized")

        # Verify all fabric cards for initialization
        if fabric_cards_not_initialized := command_output["fabricCardsNotInitialized"]:
            for card in fabric_cards_not_initialized:
                self.result.is_failure(f"Fabric card: {card} - Not initialized")

        # Verify fabric interrupts
        for fabric, fabric_details in command_output["fabricInterruptOccurrences"].items():
            if (interrupt_count := fabric_details["count"]) > self.inputs.max_fabric_interrupts:
                self.result.is_failure(
                    f"Fabric: {fabric} - Fabric interrupts above threshold - Expected: <= {self.inputs.max_fabric_interrupts} Actual: {interrupt_count}"
                )


class VerifyInventory(AntaTest):
    """Verifies the physical hardware inventory of the device.

    By default, this test checks that all slots for the following component types
    are populated: **power supply**, **fan tray**, **fabric card**,
    **line card** and **supervisor**.

    For more granular checks, specific `requirements` can be provided.

    Expected Results
    ----------------
    * Success: The test will pass if the device inventory meets the requirements.
    * Failure: The test will fail if any component does not meet the requirements.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyInventory:
          # Verify at least 2 power supplies are installed
          # Strictly check that all fabric card slots are filled
          # Other components types (fan trays, line cards, supervisors) are ignored
          requirements:
            power_supplies: 2
            fabric_cards: all
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show inventory", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInventory test."""

        requirements: HardwareInventory | None = None
        """Specifies the required hardware inventory. If not provided, all supported components are checked."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInventory."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        inventory = self._build_inventory(command_output)

        if self.inputs.requirements is None:
            self._verify_all_slots_populated(inventory)
        else:
            self._verify_specific_requirements(inventory)

    def _verify_all_slots_populated(self, inventory: dict[str, dict[str, Any]]) -> None:
        """Verify that all available slots for all component types are populated."""
        for component_data in inventory.values():
            self._report_failures(component_data)

    def _verify_specific_requirements(self, inventory: dict[str, dict[str, Any]]) -> None:
        """Verify that the inventory meets the user-defined requirements."""
        for component_type in HardwareInventory.model_fields:
            requirement = getattr(self.inputs.requirements, component_type)

            if requirement is None:
                # Requirement for this component type is not specified so we skip it
                continue

            component_data = inventory[component_type]

            if requirement == "all":
                # All available slots for this component type must be inserted
                self._report_failures(component_data)
                continue

            if isinstance(requirement, int) and (installed_count := component_data["installed"]) < requirement:
                # Check if the number of installed units meets the minimum requirement
                self.result.is_failure(f"{component_type.replace('_', ' ').title()} - Count mismatch - Expected: >= {requirement} Actual: {installed_count}")

    def _report_failures(self, component_data: dict[str, Any]) -> None:
        """Report failures for a given component type based on its state."""
        for slot in component_data.get("not_inserted", []):
            self.result.is_failure(f"{slot} - Not inserted")
        for slot in component_data.get("unidentified", []):
            self.result.is_failure(f"{slot} - Unidentified component")

    def _build_inventory(self, inventory_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Build a structured dictionary of the device hardware inventory."""
        inventory: dict[str, dict[str, Any]] = {
            "power_supplies": self._create_inventory_entry(),
            "fan_trays": self._create_inventory_entry(),
            "fabric_cards": self._create_inventory_entry(),
            "supervisors": self._create_inventory_entry(),
            "line_cards": self._create_inventory_entry(),
        }

        # Update inventory for each component type
        self._update_inventory_component(
            inventory=inventory,
            slots_data=inventory_data.get("powerSupplySlots", {}),
            slot_prefix="Power Supply Slot",
            name_key="name",
            component_type="power_supplies",
        )
        self._update_inventory_component(
            inventory=inventory,
            slots_data=inventory_data.get("fanTraySlots", {}),
            slot_prefix="Fan Tray Slot",
            name_key="name",
            component_type="fan_trays",
        )
        self._update_inventory_component(
            inventory=inventory,
            slots_data=inventory_data.get("cardSlots", {}),
            slot_prefix="Card Slot",
            name_key="modelName",
            component_type_getter=self._get_card_component_type,
        )

        return inventory

    def _update_inventory_component(
        self,
        inventory: dict[str, Any],
        slots_data: dict[str, dict[str, Any]],
        slot_prefix: str,
        name_key: str,
        component_type: str | None = None,
        component_type_getter: Callable[[str], str | None] | None = None,
    ) -> None:
        """Update the main inventory dictionary for a specific component type.

        This method updates the inventory dictionary by reference.
        """
        for slot, details in slots_data.items():
            current_component_type = component_type or (component_type_getter(slot) if component_type_getter else None)
            if not current_component_type:
                continue

            inventory_entry = inventory[current_component_type]
            slot_name = f"{slot_prefix}: {slot}"
            component_name = details.get(name_key)

            if not component_name:
                inventory_entry["unidentified"].append(slot_name)
            elif "Not Inserted" in component_name:
                inventory_entry["not_inserted"].append(slot_name)
            else:
                inventory_entry["installed"] += 1

    def _create_inventory_entry(self) -> dict[str, Any]:
        """Create a standard entry for a component type in the inventory."""
        return {"installed": 0, "not_inserted": [], "unidentified": []}

    def _get_card_component_type(self, card_slot_name: str) -> str | None:
        """Get the component type of a hardware card based on its slot name."""
        if card_slot_name.startswith("Fabric"):
            return "fabric_cards"
        if card_slot_name.startswith("Supervisor"):
            return "supervisors"
        if card_slot_name.startswith("Linecard"):
            return "line_cards"
        return None


class VerifyHardwareCapacityUtilization(AntaTest):
    """Verifies hardware capacity utilization.

    !!! warning
        When `strict_mode: true`, some EOS features max out hardware tables by design, which will cause failures in this mode.

    Expected Results
    ----------------
    * Success: The test will pass if all checked hardware tables are below their defined capacity utilization thresholds.
    * Failure: The test will fail if any of the checked hardware tables are above their capacity utilization threshold.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyHardwareCapacityUtilization:
          capacity_utilization_threshold: 90
          strict_mode: true
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show hardware capacity alert threshold", revision=1),
        AntaTemplate(template="show hardware capacity utilization percent exceed {capacity_utilization_threshold}", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyHardwareCapacityUtilization test."""

        capacity_utilization_threshold: Percent = 90
        """Fails the test if the utilization of any checked hardware table exceeds this threshold."""
        strict_mode: bool = False
        """If True, check all tables. If False (default), only check tables with a configured threshold alert."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for the capacity utilization threshold."""
        return [template.render(capacity_utilization_threshold=int(self.inputs.capacity_utilization_threshold))]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyHardwareCapacityUtilization."""
        self.result.is_success()
        alert_output = self.instance_commands[0].json_output
        utilization_output = self.instance_commands[1].json_output

        # If "tables" is empty, no thresholds were exceeded, which is a success condition
        if not (tables_exceeding_threshold := utilization_output.get("tables")):
            return

        # In strict mode, fail for any table exceeding the threshold
        if self.inputs.strict_mode:
            for table_entry in tables_exceeding_threshold:
                self.result.is_failure(self._build_failure_message(table_entry))
            return

        # Otherwise, only fail for tables that are also configured for alerting
        alert_tables = set(alert_output["thresholds"])

        for table_entry in tables_exceeding_threshold:
            table = table_entry["table"]
            feature = table_entry["feature"]
            combined_table_name = f"{table}-{feature}" if feature else table

            if combined_table_name in alert_tables:
                self.result.is_failure(self._build_failure_message(table_entry))

    def _build_failure_message(self, entry: dict[str, Any]) -> str:
        """Build the failure message from a table entry."""
        prefix_msg = f"Table: {entry['table']}"
        if chip := entry["chip"]:
            prefix_msg += f" Chip: {chip}"
        if feature := entry["feature"]:
            prefix_msg += f" Feature: {feature}"

        return f"{prefix_msg} - Capacity above threshold - Expected: < {self.inputs.capacity_utilization_threshold}% Actual: {entry['usedPercent']}%"


class VerifyModuleStatus(AntaTest):
    """Verifies the operational status and power stability of all modules in a modular chassis.

    !!! warning
        It is **crucial** to set the `supervisor_mode` input correctly to match the hardware chassis.
        Running this test in the wrong mode will result in a failure. Inventory and catalog tags can be used
        to run the test in different modes on different hardware chassis.

    Expected Results
    ----------------
    * Success: The test will pass if:
        - A dual-supervisor system has one `active` and one `standby` supervisor.
        - A single-supervisor system has one `active` supervisor.
        - All other modules are in the expected state.
        - All module risers report stable power.
    * Failure: The test will fail if any of the above conditions are not met.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyModuleStatus:
          # To accept 'ok' or 'poweredOff' statuses for linecards
          module_statuses:
            - ok
            - poweredOff
          # To test a single-supervisor chassis
          supervisor_mode: single
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show module", revision=1),
        AntaCommand(command="show module power", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyModuleStatus test."""

        module_statuses: list[ModuleStatus] = Field(default=["ok"])
        """List of accepted statuses for modules other than supervisors (linecards, switch cards, etc.)."""
        supervisor_mode: Literal["single", "dual"] = Field(default="dual")
        """Expected supervisor configuration."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyModuleStatus."""
        self.result.is_success()
        modules_details = self.instance_commands[0].json_output["modules"]
        modules_power_details = self.instance_commands[1].json_output["modules"]

        if self.inputs.supervisor_mode == "dual":
            # Dual-supervisor validation logic
            supervisor_slots = {"1", "2"}
            if not supervisor_slots.issubset(modules_details):
                self.result.is_failure("Dual-Supervisor Mode - Standby supervisor is missing")
                return

            sup_statuses = {modules_details["1"]["status"], modules_details["2"]["status"]}
            expected_statuses = {"active", "standby"}

            if sup_statuses != expected_statuses:
                self.result.is_failure(
                    f"Dual-Supervisor Mode - Incorrect statuses - Expected: {'/'.join(sorted(expected_statuses))} Actual: {'/'.join(sorted(sup_statuses))}"
                )

        else:
            # Single-supervisor validation logic
            supervisor_slots = {"1"}
            if "1" not in modules_details:
                self.result.is_failure("Single-Supervisor Mode - Active supervisor is missing")
                return

            if (sup1_status := modules_details["1"]["status"]) != "active":
                self.result.is_failure(f"Single-Supervisor Mode - Incorrect status - Expected: active Actual: {sup1_status}")

        self._check_module_cards(modules_details, supervisor_slots)
        self._check_module_power(modules_power_details)

    def _check_module_cards(self, modules_details: dict[str, Any], supervisor_slots: set[str]) -> None:
        """Validate the status of all non-supervisor modules."""
        prefix = "Single-Supervisor Mode" if self.inputs.supervisor_mode == "single" else "Dual-Supervisor Mode"
        for slot, module_data in modules_details.items():
            if slot in supervisor_slots:
                continue

            module_status = module_data["status"]
            if module_status not in self.inputs.module_statuses:
                self.result.is_failure(
                    f"{prefix} - Module: {slot} Model: {module_data['modelName']} - Invalid status - "
                    f"Expected: {', '.join(self.inputs.module_statuses)} Actual: {module_status}"
                )

    def _check_module_power(self, modules_power_details: dict[str, Any]) -> None:
        """Validate that all module risers report stable power."""
        prefix = "Single-Supervisor Mode" if self.inputs.supervisor_mode == "single" else "Dual-Supervisor Mode"
        for slot, module_data in modules_power_details.items():
            for riser_slot, riser_data in module_data["risers"].items():
                if not riser_data["powerGood"]:
                    self.result.is_failure(f"{prefix} - Module: {slot} Riser {riser_slot} - Power is not stable")
