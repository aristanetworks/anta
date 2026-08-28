# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for advisory remediation text helpers."""

from anta._advisory.remediation import FixedRelease, evidence_remediation, mitigated_remediation, no_remediation, upgrade_remediation


def test_upgrade_remediation_lists_every_published_train_without_url() -> None:
    """Verify upgrade guidance includes each train without duplicating the advisory URL."""
    remediation = upgrade_remediation((FixedRelease("4.36.3F", "4.36"), FixedRelease("4.35.6M", "4.35"), FixedRelease("4.34.8M", "4.34")))

    assert "EOS 4.36.3F or later in the 4.36 train" in remediation
    assert "EOS 4.35.6M or later in the 4.35 train" in remediation
    assert "EOS 4.34.8M or later in the 4.34 train" in remediation
    assert "Refer to the advisory" in remediation
    assert "http" not in remediation


def test_inconclusive_remediation_without_published_fix() -> None:
    """Verify unresolved advisories explain that no remediated release is published."""
    remediation = upgrade_remediation((), inconclusive=True)

    assert "when one is published" in remediation
    assert "unresolved condition" in remediation


def test_other_remediation_forms() -> None:
    """Verify empty, evidence, and mitigated remediation forms."""
    assert no_remediation() == ""
    assert evidence_remediation("'show version' output") == "Collect or correct 'show version' output and rerun the test."
    assert "Maintain the verified control until upgrading" in mitigated_remediation("the verified control", ())
