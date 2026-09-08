# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for shared structured-assessment steps."""

from __future__ import annotations

from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FactSource, FactSourceKind, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_eos_version
from anta._advisory.findings.models import EosReleaseAssessment, ErrorResult, NotAffectedResult, VersionRelation
from anta._eos.version import EOSVersion, parse_eos_version

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
RULES = (VersionRule(major=4, minor=35, patch_lte=5),)


def _eos_version(value: str) -> EOSVersion:
    """Return a normalized EOS version for assessment tests."""
    return parse_eos_version(value).unwrap()


def test_assess_eos_scope_returns_affected_context() -> None:
    """Retain affected EOS context without producing a terminal result."""
    version = EosVersionFact.available(_eos_version("4.35.5M"), SOURCE)

    result = assess_eos_scope("CVE-test", version, RULES)

    assert isinstance(result, EosReleaseAssessment)
    assert result.relation is VersionRelation.AFFECTED


def test_assess_eos_scope_returns_not_affected() -> None:
    """Close the assessment when EOS is outside the affected matrix."""
    version = EosVersionFact.available(_eos_version("4.35.6M"), SOURCE)

    result = assess_eos_scope("CVE-test", version, RULES)

    assert isinstance(result, NotAffectedResult)


def test_assess_eos_scope_returns_input_errors() -> None:
    """Preserve missing and invalid EOS version problems."""
    missing = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    malformed = EosVersionFact.unavailable(FactProblemKind.INVALID, SOURCE)

    missing_result = assess_eos_scope("CVE-test", missing, RULES)
    malformed_result = assess_eos_scope("CVE-test", malformed, RULES)

    assert isinstance(missing_result, ErrorResult)
    assert missing_result.problems == (missing,)
    assert isinstance(malformed_result, ErrorResult)
    assert malformed_result.problems[0].problem is FactProblemKind.INVALID


def test_assess_eos_version_retains_non_terminal_relations() -> None:
    """Interpret affected and outside-scope versions without ending the assessment."""
    affected = EosVersionFact.available(_eos_version("4.35.5M"), SOURCE)
    outside = EosVersionFact.available(_eos_version("4.35.6M"), SOURCE)

    affected_result = assess_eos_version(affected, RULES)
    outside_result = assess_eos_version(outside, RULES)

    assert not isinstance(affected_result, UnavailableFact)
    assert affected_result.relation is VersionRelation.AFFECTED
    assert not isinstance(outside_result, UnavailableFact)
    assert outside_result.relation is VersionRelation.OUTSIDE_SCOPE


def test_assess_eos_version_retains_input_problems() -> None:
    """Return typed unavailable facts for missing and invalid versions."""
    missing = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    invalid = EosVersionFact.unavailable(FactProblemKind.INVALID, SOURCE)

    missing_result = assess_eos_version(missing, RULES)
    invalid_result = assess_eos_version(invalid, RULES)

    assert missing_result is missing
    assert isinstance(invalid_result, UnavailableFact)
    assert invalid_result.problem is FactProblemKind.INVALID
