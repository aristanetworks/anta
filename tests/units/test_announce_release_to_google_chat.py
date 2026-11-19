# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the Google Chat release announcement helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from types import ModuleType


SCRIPT_PATH = Path(__file__).parents[2] / ".github" / "announce_release_to_google_chat.py"


def load_announcement_module() -> ModuleType:
    """Load the GitHub release announcement helper module."""
    spec = importlib.util.spec_from_file_location("announce_release_to_google_chat", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        msg = f"Unable to load {SCRIPT_PATH}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANNOUNCE = load_announcement_module()


def test_build_announcement_uses_curated_highlights() -> None:
    """Curated Highlights from the release body should be preferred."""
    message = ANNOUNCE.build_announcement(
        tag_name="v1.7.0",
        release_url="https://github.com/aristanetworks/anta/releases/tag/v1.7.0",
        release_body="""## Highlights

- Support for expanded results
- Nicer markdown report

## Fixed issues

- A less important fallback item
""",
    )

    assert "🐜 ANTA v1.7.0 is out 🐜" in message
    assert "Support for expanded results" in message
    assert "Nicer markdown report" in message
    assert "A less important fallback item" not in message
    assert "https://anta.arista.com/stable" in message
    assert "pipx upgrade anta" in message


def test_extract_highlights_ignores_generated_release_notes() -> None:
    """Generated release-note sections should not be treated as curated highlights."""
    assert (
        ANNOUNCE.extract_highlights(
            """## Documentation

- Documentation-only change

## New features and enhancements

- Add Python 3.14 support by @anta in #123
- Add markdown report improvements by @anta in #124

## Fixed issues

- Fix a bug by @anta in #125
"""
        )
        == []
    )


def test_require_highlights_fails_without_curated_highlights() -> None:
    """Missing highlights should fail before the release is announced."""
    with pytest.raises(ValueError, match="must contain a non-empty '## Highlights' section"):
        ANNOUNCE.require_highlights(
            """## New features and enhancements

- Add Python 3.14 support by @anta in #123
"""
        )


def test_require_highlights_fails_with_placeholder_highlights() -> None:
    """Placeholder highlights should not pass validation."""
    with pytest.raises(ValueError, match="must contain a non-empty '## Highlights' section"):
        ANNOUNCE.require_highlights(
            """## Highlights

- TODO
- TBD
- Fill this in

## New features and enhancements

- Add Python 3.14 support by @anta in #123
"""
        )


def test_require_highlights_accepts_curated_highlights() -> None:
    """Curated highlights should pass validation."""
    assert ANNOUNCE.require_highlights(
        """## Documentation

- Documentation-only change

## Highlights

- Add Python 3.14 support
- Improve markdown report output
"""
    ) == ["Add Python 3.14 support", "Improve markdown report output"]


def test_build_announcement_fails_for_empty_release_body() -> None:
    """Empty release notes should not produce a low-quality announcement."""
    with pytest.raises(ValueError, match="must contain a non-empty '## Highlights' section"):
        ANNOUNCE.build_announcement(tag_name="v1.7.0", release_url="https://example.com/release", release_body="")


def test_build_announcement_adds_v_prefix_when_missing() -> None:
    """Version formatting should match the manual announcement style."""
    message = ANNOUNCE.build_announcement(tag_name="1.7.0", release_url="https://example.com/release", release_body="## Highlights\n\n- Useful item")

    assert message.startswith("🐜 ANTA v1.7.0 is out 🐜")


def test_load_release_event(tmp_path: Path) -> None:
    """Release metadata should be read from the GitHub event payload."""
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "release": {
                    "tag_name": "v1.7.0",
                    "html_url": "https://github.com/aristanetworks/anta/releases/tag/v1.7.0",
                    "body": "## Highlights\n\n- Useful item",
                }
            }
        ),
        encoding="utf-8",
    )

    assert ANNOUNCE.load_release_event(event_path) == {
        "tag_name": "v1.7.0",
        "release_url": "https://github.com/aristanetworks/anta/releases/tag/v1.7.0",
        "release_body": "## Highlights\n\n- Useful item",
    }


def test_main_dry_run_does_not_require_or_print_webhook_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Dry-run mode should render the message without touching the webhook secret."""
    event_path = tmp_path / "event.json"
    webhook_url = "https://chat.googleapis.com/v1/spaces/secret/messages?key=secret&token=secret"
    event_path.write_text(
        json.dumps({"release": {"tag_name": "v1.7.0", "html_url": "https://example.com/release", "body": "## Highlights\n\n- Useful item"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("ANTA_FIELD_WEBHOOK_URL", webhook_url)

    assert ANNOUNCE.main(["--dry-run"]) == 0

    captured = capsys.readouterr()
    assert "🐜 ANTA v1.7.0 is out 🐜" in captured.out
    assert webhook_url not in captured.out
    assert webhook_url not in captured.err


def test_main_check_validates_highlights(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Check mode should validate highlights without requiring the webhook secret."""
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"release": {"tag_name": "v1.7.0", "html_url": "https://example.com/release", "body": "## Highlights\n\n- Useful item"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.delenv("ANTA_FIELD_WEBHOOK_URL", raising=False)

    assert ANNOUNCE.main(["--check"]) == 0

    captured = capsys.readouterr()
    assert "Release announcement highlights are ready." in captured.out


def test_post_to_google_chat_sends_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """The webhook POST should use a JSON text payload."""
    response = MagicMock()
    response.__enter__.return_value.status = 200
    urlopen = MagicMock(return_value=response)
    monkeypatch.setattr(ANNOUNCE.urllib.request, "urlopen", urlopen)

    ANNOUNCE.post_to_google_chat("https://chat.example.invalid/webhook", "Happy testing! 🐜")

    request = urlopen.call_args.args[0]
    assert request.full_url == "https://chat.example.invalid/webhook"
    assert request.get_method() == "POST"
    assert json.loads(request.data.decode()) == {"text": "Happy testing! 🐜"}
    assert request.headers["Content-type"] == "application/json"


def test_post_to_google_chat_fails_on_non_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-2xx webhook responses should fail the announcement job."""
    response = MagicMock()
    response.__enter__.return_value.status = 500
    monkeypatch.setattr(ANNOUNCE.urllib.request, "urlopen", MagicMock(return_value=response))

    with pytest.raises(RuntimeError, match="Google Chat webhook returned HTTP 500"):
        ANNOUNCE.post_to_google_chat("https://chat.example.invalid/webhook", "Happy testing! 🐜")
