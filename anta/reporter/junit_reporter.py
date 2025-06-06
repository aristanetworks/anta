# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""JUnit Report management for ANTA."""

# pylint: disable = too-few-public-methods
import datetime
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from anta.logger import anta_log_exception
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus, TestResult

logger = logging.getLogger(__name__)


@dataclass
class TestSuite:
    """TODO."""

    element: ET.Element
    name: str
    hostname: str
    timestamp: str
    suite_tests: int = 0
    suite_failures: int = 0
    suite_errors: int = 0
    suite_skipped: int = 0
    suite_time: float = 0.0


class JUnitReporter:
    """A reporter that generates JUnit XML output."""

    @classmethod
    def _build_device(cls, device_name: str, results: list[TestResult], testsuites: ET.Element) -> TestSuite:
        """Build testsuite for a given device."""
        testsuite = TestSuite(
            element=ET.SubElement(testsuites, "testsuite"),
            name=f"ANTA Tests on {device_name}",
            hostname=device_name,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            suite_tests=len(results),
        )

        # Iterate through results for this device to create <testcase> elements
        for result in results:
            testcase = ET.SubElement(testsuite.element, "testcase")

            testcase.set("name", result.test)
            testcase.set("classname", device_name)  # Use device name as classname

            # TestResult is missing start and end times so for now duration is 0.0 for all tests...
            # TODO: Add duration
            duration = 0.0
            testcase.set("time", f"{duration:.3f}")
            testsuite.suite_time += duration

            # Add failure, error, or skipped elements based on status
            if result.result == AntaTestStatus.FAILURE:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", "Test Failed")
                # TODO: set type properly
                failure.set("type", "AssertionError")
                failure.text = "\n".join(result.messages)
                testsuite.suite_failures += 1

            elif result.result == AntaTestStatus.ERROR:
                error = ET.SubElement(testcase, "error")
                error.set("message", "Test Error")
                # TODO: set type properly
                error.set("type", "RuntimeError")  # Or a more specific type
                error.text = "\n".join(result.messages)
                testsuite.suite_failures += 1

            elif result.result == AntaTestStatus.SKIPPED:
                skipped = ET.SubElement(testcase, "skipped")
                skipped.set("message", "Test Skipped")
                skipped.text = "\n".join(result.messages)
                testsuite.suite_skipped += 1

            # AntaTestStatus.SUCCESS requires no extra element
            # TODO: deal with UNSET

        # Set attributes for the current test suite
        testsuite.element.set("tests", str(testsuite.suite_tests))
        testsuite.element.set("failures", str(testsuite.suite_failures))
        testsuite.element.set("errors", str(testsuite.suite_errors))
        testsuite.element.set("skipped", str(testsuite.suite_skipped))
        testsuite.element.set("time", f"{testsuite.suite_time:.3f}")

        return testsuite

    @classmethod
    def generate(cls, results: ResultManager, output_path: Path) -> None:
        """Generate the JUnit XML report and saves it to the output path."""
        # Group results by device (each device becomes a test suite)
        results_by_device: dict[str, list[TestResult]] = {}
        for result in results.get_results(sort_by=["categories", "test"]):
            device_name = result.name
            if device_name not in results_by_device:
                results_by_device[device_name] = []
            results_by_device[device_name].append(result)

        # Create the root <testsuites> element
        testsuites = ET.Element("testsuites")

        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        total_time = 0.0

        # Iterate through devices to create <testsuite> elements
        for device_name, device_results in results_by_device.items():
            testsuite = cls._build_device(device_name, device_results, testsuites)

            # Update total counts
            # TODO: cleanup mess
            total_tests += testsuite.suite_tests
            total_failures += testsuite.suite_failures
            total_errors += testsuite.suite_errors
            total_skipped += testsuite.suite_skipped
            total_time += testsuite.suite_time

        # Set attributes for the root testsuites element
        testsuites.set("tests", str(total_tests))
        testsuites.set("failures", str(total_failures))
        testsuites.set("errors", str(total_errors))
        testsuites.set("skipped", str(total_skipped))
        testsuites.set("time", f"{total_time:.3f}")  # Total time for all suites

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the XML to the file
        try:
            tree = ET.ElementTree(testsuites)
            ET.indent(tree, space="  ", level=0)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)

            logger.info("JUnit report generated successfully at: %s", output_path)

        except Exception as exc:
            message = f"Error while writing the JUNIT file '{output_path.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise
