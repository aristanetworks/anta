"""
Test functions to flag field notices
"""

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest


class VerifyFieldNotice44Resolution(AntaTest):
    """
    Verifies the device is using an Aboot version that fix the bug discussed
    in the field notice 44 (Aboot manages system settings prior to EOS initialization).

    https://www.arista.com/en/support/advisories-notices/field-notice/8756-field-notice-44
    """

    name = "VerifyFieldNotice44Resolution"
    description = (
        "Verifies the device is using an Aboot version that fix the bug discussed in the field notice 44 (Aboot manages system settings prior to EOS initialization)"
    )
    categories = ["field notices", "software"]
    commands = [AntaCommand(command="show version detail")]

    # TODO maybe implement ONLY ON PLATFORMS instead
    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyFieldNotice44Resolution validation"""

        command_output = self.instance_commands[0].json_output

        devices = [
            "DCS-7010T-48",
            "DCS-7010T-48-DC",
            "DCS-7050TX-48",
            "DCS-7050TX-64",
            "DCS-7050TX-72",
            "DCS-7050TX-72Q",
            "DCS-7050TX-96",
            "DCS-7050TX2-128",
            "DCS-7050SX-64",
            "DCS-7050SX-72",
            "DCS-7050SX-72Q",
            "DCS-7050SX2-72Q",
            "DCS-7050SX-96",
            "DCS-7050SX2-128",
            "DCS-7050QX-32S",
            "DCS-7050QX2-32S",
            "DCS-7050SX3-48YC12",
            "DCS-7050CX3-32S",
            "DCS-7060CX-32S",
            "DCS-7060CX2-32S",
            "DCS-7060SX2-48YC6",
            "DCS-7160-48YC6",
            "DCS-7160-48TC6",
            "DCS-7160-32CQ",
            "DCS-7280SE-64",
            "DCS-7280SE-68",
            "DCS-7280SE-72",
            "DCS-7150SC-24-CLD",
            "DCS-7150SC-64-CLD",
            "DCS-7020TR-48",
            "DCS-7020TRA-48",
            "DCS-7020SR-24C2",
            "DCS-7020SRG-24C2",
            "DCS-7280TR-48C6",
            "DCS-7280TRA-48C6",
            "DCS-7280SR-48C6",
            "DCS-7280SRA-48C6",
            "DCS-7280SRAM-48C6",
            "DCS-7280SR2K-48C6-M",
            "DCS-7280SR2-48YC6",
            "DCS-7280SR2A-48YC6",
            "DCS-7280SRM-40CX2",
            "DCS-7280QR-C36",
            "DCS-7280QRA-C36S",
        ]
        variants = ["-SSD-F", "-SSD-R", "-M-F", "-M-R", "-F", "-R"]

        model = command_output["modelName"]
        # TODO this list could be a regex
        for variant in variants:
            model = model.replace(variant, "")
        if model not in devices:
            self.result.is_skipped("device is not impacted by FN044")
            return

        for component in command_output["details"]["components"]:
            if component["name"] == "Aboot":
                aboot_version = component["version"].split("-")[2]
        self.result.is_success()
        if aboot_version.startswith("4.0.") and int(aboot_version.split(".")[2]) < 7:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
        elif aboot_version.startswith("4.1.") and int(aboot_version.split(".")[2]) < 1:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
        elif aboot_version.startswith("6.0.") and int(aboot_version.split(".")[2]) < 9:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
        elif aboot_version.startswith("6.1.") and int(aboot_version.split(".")[2]) < 7:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")


class VerifyFieldNotice72Resolution(AntaTest):
    """
    Checks if the device is potentially exposed to Field Notice 72, and if the issue has been mitigated.

    https://www.arista.com/en/support/advisories-notices/field-notice/17410-field-notice-0072
    """

    name = "VerifyFieldNotice72Resolution"
    description = "Verifies if the device has exposeure to FN72, and if the issue has been mitigated"
    categories = ["field notices", "software"]
    commands = [AntaCommand(command="show version detail")]

    # TODO maybe implement ONLY ON PLATFORMS instead
    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyFieldNotice72Resolution validation"""

        command_output = self.instance_commands[0].json_output

        devices = ["DCS-7280SR3-48YC8", "DCS-7280SR3K-48YC8"]
        variants = ["-SSD-F", "-SSD-R", "-M-F", "-M-R", "-F", "-R"]
        model = command_output["modelName"]

        for variant in variants:
            model = model.replace(variant, "")
        if model not in devices:
            self.result.is_skipped("Platform is not impacted by FN072")
            return

        serial = command_output["serialNumber"]
        number = int(serial[3:7])

        if "JPE" not in serial and "JAS" not in serial:
            self.result.is_skipped("Device not exposed")
            return

        if model == "DCS-7280SR3-48YC8" and "JPE" in serial and number >= 2131:
            self.result.is_skipped("Device not exposed")
            return

        if model == "DCS-7280SR3-48YC8" and "JAS" in serial and number >= 2041:
            self.result.is_skipped("Device not exposed")
            return

        if model == "DCS-7280SR3K-48YC8" and "JPE" in serial and number >= 2134:
            self.result.is_skipped("Device not exposed")
            return

        if model == "DCS-7280SR3K-48YC8" and "JAS" in serial and number >= 2041:
            self.result.is_skipped("Device not exposed")
            return

        # Because each of the if checks above will return if taken, we only run the long
        # check if we get this far
        for entry in command_output["details"]["components"]:
            if entry["name"] == "FixedSystemvrm1":
                if int(entry["version"]) < 7:
                    self.result.is_failure("Device is exposed to FN72")
                else:
                    self.result.is_success("FN72 is mitigated")
                return
        # We should never hit this point
        self.result.is_error("Error in running test - FixedSystemvrm1 not found")
        return
