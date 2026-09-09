# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.junit_reporter.py."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.reporter.junit_reporter import JUnitReporter
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus, TestResult

if TYPE_CHECKING:
    from pathlib import Path


def test_junit_reporter_generate(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the JUnitReporter.generate() class method."""
    junit_filename = tmp_path / "test.xml"

    JUnitReporter.generate(results=result_manager, output_path=junit_filename)
    assert junit_filename.exists()

    root = ET.parse(junit_filename).getroot()  # noqa: S314
    assert root.tag == "testsuites"
    assert root.get("tests") == str(result_manager.get_total_results({AntaTestStatus.SUCCESS, AntaTestStatus.SKIPPED, AntaTestStatus.FAILURE, AntaTestStatus.ERROR}))
    assert root.get("failures") == str(result_manager.get_total_results({AntaTestStatus.FAILURE}))
    assert root.get("errors") == str(result_manager.get_total_results({AntaTestStatus.ERROR}))
    assert root.get("skipped") == str(result_manager.get_total_results({AntaTestStatus.SKIPPED}))

    testsuites = root.findall("testsuite")
    assert {testsuite.get("hostname") for testsuite in testsuites} == {result.name for result in result_manager.results}

    testcases = root.findall("./testsuite/testcase")
    assert len(testcases) == int(root.get("tests", "0"))
    first_result = result_manager.get_results(sort_by=["categories", "test"])[0]
    assert testcases[0].get("classname") == first_result.name
    assert testcases[0].get("name", "").startswith(f"{first_result.test} - {first_result.description}")
    assert testcases[0].find("./failure") is not None
    assert testcases[0].find("./properties/property[@name='description']") is not None


def test_junit_reporter_generate_failure(
    tmp_path: Path,
    result_manager: ResultManager,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the JUnitReporter.generate() class method."""
    junit_filename = tmp_path / "test.xml"

    with patch("xml.etree.ElementTree.ElementTree.write", side_effect=PermissionError(junit_filename)), pytest.raises(OSError, match=r"test\.xml"):
        JUnitReporter.generate(results=result_manager, output_path=junit_filename)

    assert len(caplog.record_tuples) == 1
    assert "Error while writing the JUNIT file '" in caplog.text


def test_junit_reporter_generate_deduplicates_duplicate_testcase_names(tmp_path: Path) -> None:
    """Test that JUnit testcase names remain unique for duplicate ANTA test names."""
    junit_filename = tmp_path / "test.xml"
    result_manager = ResultManager()
    result_manager.add(
        TestResult(
            name="leaf1",
            test="VerifyReachability",
            categories=["connectivity"],
            description="Verifies reachability to BGP neighbors.",
            result=AntaTestStatus.FAILURE,
            messages=["Peer is not reachable"],
        )
    )
    result_manager.results[0].add(description="Destination 192.0.2.1 in VRF default", status=AntaTestStatus.FAILURE)
    result_manager.add(
        TestResult(
            name="leaf1",
            test="VerifyReachability",
            categories=["connectivity"],
            description="Verifies reachability to BGP neighbors.",
            result=AntaTestStatus.SUCCESS,
        )
    )
    result_manager.results[1].add(description="Destination 192.0.2.2 in VRF default", status=AntaTestStatus.SUCCESS)

    JUnitReporter.generate(results=result_manager, output_path=junit_filename)

    testcases = ET.parse(junit_filename).findall("./testsuite/testcase")  # noqa: S314
    testcase_names = [testcase.get("name") for testcase in testcases]
    assert len(testcase_names) == len(set(testcase_names))
    assert all(re.fullmatch(r"VerifyReachability - Verifies reachability to BGP neighbors\. \[[0-9a-f]{16}\]", name or "") for name in testcase_names)
