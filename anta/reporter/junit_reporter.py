import datetime
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus, TestResult

logger = logging.getLogger(__name__)


class JUnitReporter:
    """A reporter that generates JUnit XML output."""

    def __init__(self, result_manager: ResultManager, output_path: str = "junit_report.xml") -> None:
        """Initialize the JUnitReporter.

        Parameters
        ----------
            result_manager: The ResultManager containing the test results.
            output_path: The path where the JUnit XML report will be saved.
        """
        self.result_manager = result_manager
        self.output_path = Path(output_path)

    def generate(self) -> None:
        """Generate the JUnit XML report and saves it to the output path."""
        # Group results by device (each device becomes a test suite)
        results_by_device: dict[str, list[TestResult]] = {}
        for result in self.result_manager.get_results():
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
        for device_name, results in results_by_device.items():
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

                # Map TestResult attributes to <testcase> attributes
                # Assuming test_case_name is available and represents the test function/class name
                testcase.set("name", result.test)
                testcase.set("classname", device_name)  # Use device name as classname

                # Calculate test execution time in seconds
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

            # Update total counts
            total_tests += suite_tests
            total_failures += suite_failures
            total_errors += suite_errors
            total_skipped += suite_skipped
            total_time += suite_time  # Sum of suite times, or calculate total execution time if available

        # Set attributes for the root testsuites element
        testsuites.set("tests", str(total_tests))
        testsuites.set("failures", str(total_failures))
        testsuites.set("errors", str(total_errors))
        testsuites.set("skipped", str(total_skipped))
        testsuites.set("time", f"{total_time:.3f}")  # Total time for all suites

        # Ensure the output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the XML to the file
        try:
            tree = ET.ElementTree(testsuites)
            ET.indent(tree, space="  ", level=0)
            tree.write(self.output_path, encoding="utf-8", xml_declaration=True)

            logger.info("JUnit report generated successfully at: %s", self.output_path)

        except Exception:
            message = f"Error while writing the JUNIT file '{self.output_path.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise
