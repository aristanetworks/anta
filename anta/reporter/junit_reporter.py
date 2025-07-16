# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""JUnit Report management for ANTA."""

from __future__ import annotations

# pylint: disable = too-few-public-methods
import datetime
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING

from anta.logger import anta_log_exception
from anta.result_manager.models import AntaTestStatus, TestResult

if TYPE_CHECKING:
    from pathlib import Path

    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


@dataclass
class TestSuite:
    """Dataclass to track TestSuite information."""

    element: ET.Element
    name: str
    hostname: str
    timestamp: str
    filename: str | None
    suite_tests: int = 0
    suite_failures: int = 0
    suite_errors: int = 0
    suite_skipped: int = 0
    suite_time: float = 0.0


class JUnitReporter:
    """A reporter that generates JUnit XML output.

    Note
    ----
      There are things to be added there as required:
      * tracking assertions per test
    """

    @classmethod
    def _add_test_to_testsuite(cls, result: TestResult, testsuite: TestSuite) -> None:
        """Build testcase for a given TestResult and add it to the testsuite root element.

        Not handling the UNSET teststatus because this is not present in JUnit specification

        TODO: Add duration, file and line.
        For file and line we could consider augmenting TestResult to keep track of the class used for the test,
        instead of just the string of the name.

        Parameters
        ----------
        result:
            The TestResult.
        testsuite:
            The testsuite element to attach the test to.
        """
        testcase = ET.SubElement(testsuite.element, "testcase")
        testcase.set("name", result.test)
        testcase.set("classname", result.name)

        # Add properties
        properties = ET.SubElement(testcase, "properties")
        description = ET.SubElement(properties, "property")
        description.set("name", "description")
        description.text = result.description

        # TestResult is missing start and end times so for now duration is 0.0 for all tests...
        duration = 0.0
        testcase.set("time", f"{duration:.3f}")
        testsuite.suite_time += duration

        # Add failure, error, skipped or success elements based on status
        if result.result == AntaTestStatus.FAILURE:
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", "Test Failed")
            failure.set("type", "AssertionError")
            failure.text = "\n".join(result.messages)
            testsuite.suite_failures += 1

        elif result.result == AntaTestStatus.ERROR:
            error = ET.SubElement(testcase, "error")
            error.set("message", "Test Error")
            error.set("type", "RuntimeError")
            error.text = "\n".join(result.messages)
            testsuite.suite_errors += 1

        elif result.result == AntaTestStatus.SKIPPED:
            skipped = ET.SubElement(testcase, "skipped")
            skipped.set("message", "Test Skipped")
            skipped.text = "\n".join(result.messages)
            testsuite.suite_skipped += 1

        # AntaTestStatus.SUCCESS requires no extra element
        # AntaTestStatus.UNSET is not considered by JUnit so skipping silently for now

    @classmethod
    def _build_testsuite(cls, device_name: str, results: list[TestResult], testsuites: ET.Element, catalog_path: Path | None = None) -> None:
        """Build testsuite for a given device and add it to the testsuites root element.

        Parameters
        ----------
        device_name:
            The device name.
        results:
            The list of TestResult for this device.
        testsuites:
            The root element of the JUnit report to attach the testuite to.
        catalog_path:
            The path to the catalog where the test was defined.
        """
        testsuite = TestSuite(
            element=ET.SubElement(testsuites, "testsuite"),
            name=f"ANTA Tests on {device_name}",
            hostname=device_name,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            filename=str(catalog_path) if catalog_path else None,
            suite_tests=len(results),
        )

        # Iterate through results for this device to create <testcase> elements
        for result in results:
            JUnitReporter._add_test_to_testsuite(result, testsuite)

        # Set attributes for the current test suite
        testsuite.element.set("tests", str(testsuite.suite_tests))
        testsuite.element.set("failures", str(testsuite.suite_failures))
        testsuite.element.set("errors", str(testsuite.suite_errors))
        testsuite.element.set("skipped", str(testsuite.suite_skipped))
        testsuite.element.set("time", f"{testsuite.suite_time:.3f}")

        if testsuite.filename is not None:
            testsuite.element.set("filename", testsuite.filename)

    @classmethod
    def generate(cls, results: ResultManager, output_path: Path, catalog_path: Path | None = None) -> None:
        """Generate the JUnit XML report and saves it to the output path.

        Parameters
        ----------
        results:
            The ResultManager containing the test results to create the report for.
        output_path:
            The Path where the report should be saved.
        catalog_path:
            The catalog where the test was defined.
        """
        # Group results by device (each device becomes a test suite)
        results_by_device: dict[str, list[TestResult]] = {}
        for result in results.get_results(sort_by=["categories", "test"]):
            device_name = result.name
            if device_name not in results_by_device:
                results_by_device[device_name] = []
            results_by_device[device_name].append(result)

        # Create the root <testsuites> element
        testsuites = ET.Element("testsuites")

        # Iterate through devices to create <testsuite> elements
        for device_name, device_results in results_by_device.items():
            cls._build_testsuite(device_name, device_results, testsuites, catalog_path)

        # Set attributes for the root testsuites element
        testsuites.set("tests", str(results.get_total_results({AntaTestStatus.SUCCESS, AntaTestStatus.SKIPPED, AntaTestStatus.FAILURE, AntaTestStatus.ERROR})))
        testsuites.set("failures", str(results.get_total_results({AntaTestStatus.FAILURE})))
        testsuites.set("errors", str(results.get_total_results({AntaTestStatus.ERROR})))
        testsuites.set("skipped", str(results.get_total_results({AntaTestStatus.SKIPPED})))

        total_time = 0.0
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
