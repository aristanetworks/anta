# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.experimental.reporter.junit_reporter.py."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.experimental.reporter.junit_reporter import JUnitReporter
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


@pytest.mark.parametrize("include_catalog", [False, True])
def test_junit_reporter_generate_catalog_path(tmp_path: Path, result_manager: ResultManager, include_catalog: bool) -> None:
    """Include the catalog filename on every device suite only when provided."""
    junit_filename = tmp_path / "test.xml"
    catalog_path = tmp_path / "catalog.yml" if include_catalog else None

    JUnitReporter.generate(results=result_manager, output_path=junit_filename, catalog_path=catalog_path)

    testsuites = ET.parse(junit_filename).findall("testsuite")  # noqa: S314
    assert testsuites
    expected_filename = str(catalog_path) if include_catalog else None
    assert all(testsuite.get("filename") == expected_filename for testsuite in testsuites)


def test_junit_reporter_generate_without_description(tmp_path: Path) -> None:
    """Keep the test name intact when its description is empty."""
    junit_filename = tmp_path / "test.xml"
    result_manager = ResultManager()
    result_manager.add(
        TestResult(
            name="leaf1",
            test="VerifyUptime",
            categories=["system"],
            description="",
            result=AntaTestStatus.SUCCESS,
        )
    )

    JUnitReporter.generate(results=result_manager, output_path=junit_filename)

    root = ET.parse(junit_filename).getroot()  # noqa: S314
    assert root.get("tests") == "1"
    testcase = root.find("./testsuite/testcase")
    assert testcase is not None
    assert testcase.get("classname") == "leaf1"
    assert testcase.get("name") == "VerifyUptime"
    description = testcase.find("./properties/property[@name='description']")
    assert description is not None
    assert description.text is None


@pytest.mark.parametrize(
    ("status", "outcome_tag"),
    [
        (AntaTestStatus.SUCCESS, None),
        (AntaTestStatus.FAILURE, "failure"),
        (AntaTestStatus.ERROR, "error"),
        (AntaTestStatus.SKIPPED, "skipped"),
    ],
)
def test_junit_reporter_escapes_invalid_xml_characters(tmp_path: Path, status: AntaTestStatus, outcome_tag: str | None) -> None:
    """Round-trip all result-derived XML values without losing diagnostic characters."""
    invalid = "\x00\x08\x0b\x0c\x0e\x1f\ud800\udfff\ufffe\uffff"
    escaped = r"\x00\x08\x0b\x0c\x0e\x1f\ud800\udfff\ufffe\uffff"
    valid = ' & < > " é 😀\t\n\ud7ff\ue000\ufffd\U00010000\U0010ffff'
    result = TestResult(
        name=f"leaf{invalid}{valid}",
        test=f"VerifyUptime{invalid}{valid}",
        categories=["system"],
        description=f"Description{invalid}{valid}",
        result=status,
        messages=[f"Diagnostic{invalid}{valid}", "Second message"],
    )
    result_manager = ResultManager()
    result_manager.add(result)
    junit_filename = tmp_path / "test.xml"

    JUnitReporter.generate(results=result_manager, output_path=junit_filename, catalog_path=tmp_path / f"catalog{invalid}.yaml")

    root = ET.parse(junit_filename).getroot()  # noqa: S314
    testsuite = root.find("testsuite")
    assert testsuite is not None
    assert testsuite.get("hostname") == f"leaf{escaped}{valid}"
    assert testsuite.get("name") == f"ANTA Tests on leaf{escaped}{valid}"
    assert testsuite.get("filename") == str(tmp_path / f"catalog{escaped}.yaml")
    testcase = testsuite.find("testcase")
    assert testcase is not None
    assert testcase.get("classname") == f"leaf{escaped}{valid}"
    assert testcase.get("name") == f"VerifyUptime{escaped}{valid} - Description{escaped}{valid}"
    description = testcase.find("./properties/property[@name='description']")
    assert description is not None
    assert description.text == f"Description{escaped}{valid}"
    if outcome_tag is not None:
        outcome = testcase.find(outcome_tag)
        assert outcome is not None
        assert outcome.text == f"Diagnostic{escaped}{valid}\nSecond message"
    else:
        assert all(testcase.find(tag) is None for tag in ("failure", "error", "skipped"))
    assert result.name == f"leaf{invalid}{valid}"
    assert result.description == f"Description{invalid}{valid}"
    assert result.messages == [f"Diagnostic{invalid}{valid}", "Second message"]


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
