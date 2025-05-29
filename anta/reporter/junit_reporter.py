"""JUnit Report management for ANTA."""

import datetime
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from anta.logger import anta_log_exception
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus, TestResult

logger = logging.getLogger(__name__)


class JUnitReporter:
    """A reporter that generates JUnit XML output."""

    @classmethod
    def _build_device(cls, device_name: str, results: list[TestResult], testsuites: ET.Element) -> ET.Element:
        """Build testsuite for a given device."""
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", f"ANTA Tests on {device_name}")
        testsuite.set("hostname", device_name)
        testsuite.set("timestamp", datetime.datetime.now().isoformat())  # Use current time for the suite

        suite_tests = len(results)
        suite_failures = 0
        suite_errors = 0
        suite_skipped = 0
        suite_time = 0.0

        # Iterate through results for this device to create <testcase> elements
        for result in results:
            testcase = ET.SubElement(testsuite, "testcase")

            testcase.set("name", result.test)
            testcase.set("classname", device_name)  # Use device name as classname

            # TestResult is missing start and end times so for now duration is 0.0 for all tests...
            # TODO: Add duration
            duration = 0.0
            testcase.set("time", f"{duration:.3f}")
            suite_time += duration

            # Add failure, error, or skipped elements based on status
            if result.result == AntaTestStatus.FAILURE:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", "Test Failed")
                # TODO: set type properly
                failure.set("type", "AssertionError")
                failure.text = "\n".join(result.messages)
                suite_failures += 1

            elif result.result == AntaTestStatus.ERROR:
                error = ET.SubElement(testcase, "error")
                error.set("message", "Test Error")
                # TODO: set type properly
                error.set("type", "RuntimeError")  # Or a more specific type
                error.text = "\n".join(result.messages)
                suite_errors += 1

            elif result.result == AntaTestStatus.SKIPPED:
                skipped = ET.SubElement(testcase, "skipped")
                skipped.set("message", "Test Skipped")
                skipped.text = "\n".join(result.messages)
                suite_skipped += 1

            # AntaTestStatus.SUCCESS requires no extra element
            # TODO: deal with UNSET

        # Set attributes for the current test suite
        testsuite.set("tests", str(suite_tests))
        testsuite.set("failures", str(suite_failures))
        testsuite.set("errors", str(suite_errors))
        testsuite.set("skipped", str(suite_skipped))
        testsuite.set("time", f"{suite_time:.3f}")

        return testsuite

    @classmethod
    def generate(cls, results: ResultManager, output_path: Path) -> None:
        """Generate the JUnit XML report and saves it to the output path."""
        # Group results by device (each device becomes a test suite)
        results_by_device: dict[str, list[TestResult]] = {}
        for result in results.get_results():
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
            total_tests += int(testsuite.get("tests"))
            total_failures += int(testsuite.get("failures"))
            total_errors += int(testsuite.get("errors"))
            total_skipped += int(testsuite.get("skipped"))
            total_time += float(testsuite.get("time"))

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
