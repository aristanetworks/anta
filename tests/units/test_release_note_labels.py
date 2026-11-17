# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Exercise the privileged release-note labeler against a stateful GitHub API fake."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
import yaml

if TYPE_CHECKING:
    from types import ModuleType
    from urllib.request import Request

ROOT = Path(__file__).parents[2].resolve()
SCRIPT = ROOT / ".github" / "release_note_labels.py"


@dataclass
class GitHub:
    """Model label state independently of the labeler's request ordering."""

    title: str = "fix(anta, anta.tests)!: Preserve escaped values: another colon"
    head_sha: str = "expected-head-sha"
    merged: bool = True
    attached: list[str] = field(default_factory=lambda: ["rn: doc", "bug", "needs rn: review"])
    existing: set[str] = field(default_factory=lambda: {"rn: doc", "bug", "needs rn: review"})
    requests: list[tuple[str, str, object]] = field(default_factory=list)
    failures: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    creation_race: bool = False

    def open(self, request: Request, *, timeout: int) -> BytesIO:  # noqa: C901
        """Accept REST requests, returning data or realistic HTTP errors."""
        assert timeout == 30
        assert request.get_header("Authorization") == "Bearer test-token"
        url = urlsplit(request.full_url)
        assert url.netloc == "api.github.com"
        assert url.path.startswith("/repos/aristanetworks/anta/")
        path = url.path.removeprefix("/repos/aristanetworks/anta/")
        method = request.get_method()
        data = request.data
        body: object | None = None
        if data:
            assert isinstance(data, bytes)
            body = json.loads(data)
        self.requests.append((method, path, body))
        failures = self.failures.get((method, path), [])
        if failures:
            self.fail(request.full_url, failures.pop(0))

        result: object = None
        if method == "GET" and path == "pulls/1910":
            result = {"merged": self.merged, "title": self.title, "head": {"sha": self.head_sha, "repo": None}}
        elif method == "GET" and path == "issues/1910/labels":
            page = int(parse_qs(url.query)["page"][0])
            result = [{"name": name} for name in self.attached[(page - 1) * 100 : page * 100]]
        elif method == "GET" and path.startswith("labels/"):
            name = unquote(path.removeprefix("labels/"))
            canonical_name = next((existing for existing in self.existing if existing.casefold() == name.casefold()), None)
            if canonical_name is None:
                self.fail(request.full_url, 404)
            result = {"name": canonical_name}
        elif method == "POST" and path == "labels":
            assert isinstance(body, dict)
            name = body["name"]
            if self.creation_race:
                self.existing.add(name)
                self.fail(request.full_url, 422)
            self.existing.add(name)
            result = {"name": name}
        elif method == "POST" and path == "issues/1910/labels":
            assert isinstance(body, dict)
            labels = body["labels"]
            assert isinstance(labels, list)
            self.attached.extend(name for name in labels if name not in self.attached)
            result = [{"name": name} for name in self.attached]
        elif method == "DELETE" and path.startswith("issues/1910/labels/"):
            self.attached.remove(unquote(path.removeprefix("issues/1910/labels/")))
            return BytesIO()
        else:
            message = f"Unexpected request: {method} {request.full_url}"
            raise AssertionError(message)
        return BytesIO(json.dumps(result).encode())

    @staticmethod
    def fail(url: str, status: int) -> None:
        """Return diagnostics representative of GitHub's REST API."""
        messages = {403: "Resource not accessible by integration", 404: "Not Found", 422: "Validation Failed", 500: "Internal Server Error"}
        raise HTTPError(url, status, messages[status], Message(), BytesIO(json.dumps({"message": messages[status]}).encode()))


@pytest.fixture(name="labeler")
def labeler_fixture(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the exact trusted workflow helper without executing its CLI."""
    spec = importlib.util.spec_from_file_location("release_note_labels", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("GITHUB_REPOSITORY", "aristanetworks/anta")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("PR_HEAD_SHA", "expected-head-sha")
    monkeypatch.delenv("GITHUB_API_URL", raising=False)
    return module


@pytest.fixture(name="github")
def github_fixture(monkeypatch: pytest.MonkeyPatch, labeler: ModuleType) -> GitHub:
    """Replace only HTTP transport; exercise the real API serialization."""
    remote = GitHub()
    monkeypatch.setattr(labeler, "urlopen", remote.open)
    return remote


def test_refresh_and_idempotence(labeler: ModuleType, github: GitHub) -> None:
    """Preserve non-release labels and the established comma/scope mapping."""
    labeler.label_pull_request(1910)
    expected = {"bug", "needs rn: review", "rn: fix(anta|anta.tests)!"}
    assert set(github.attached) == expected
    github.requests.clear()
    labeler.label_pull_request(1910)
    assert set(github.attached) == expected
    assert all(method == "GET" for method, _, _ in github.requests)


def test_current_title_wins(labeler: ModuleType, github: GitHub) -> None:
    """An old request refreshes the latest title, including repeated edits."""
    labeler.label_pull_request(1910)
    github.title = "doc: Revised after the request was uploaded"
    labeler.label_pull_request(1910)
    assert set(github.attached) == {"rn: doc", "bug", "needs rn: review"}


def test_existing_canonical_label_is_preserved(labeler: ModuleType, github: GitHub) -> None:
    """A case-insensitive lookup must not cause the desired label's removal."""
    github.title = "fix: Keep the existing label"
    github.attached = ["rn: FIX", "bug"]
    github.existing = set(github.attached)
    labeler.label_pull_request(1910)
    assert github.attached == ["rn: FIX", "bug"]
    assert all(method == "GET" for method, _, _ in github.requests)


@pytest.mark.parametrize("merged", [False, None])
def test_unmerged_hint_cannot_write(labeler: ModuleType, github: GitHub, merged: bool | None) -> None:
    """Even a modified producer cannot authorize writes to an unmerged PR."""
    github.merged = merged  # type: ignore[assignment]
    labeler.label_pull_request(1910)
    assert github.attached == ["rn: doc", "bug", "needs rn: review"]
    assert len(github.requests) == 1


def test_paginates_labels(labeler: ModuleType, github: GitHub) -> None:
    """Find multiple stale release labels beyond a full first page."""
    unrelated = [f"unrelated-{index}" for index in range(100)]
    github.attached = [*unrelated, "rn: doc", "rn: feat"]
    labeler.label_pull_request(1910)
    assert set(github.attached) == {*unrelated, "rn: fix(anta|anta.tests)!"}


@pytest.mark.parametrize("expected_head_sha", ["another-pr-head-sha", ""])
def test_request_cannot_redirect_to_another_commit(labeler: ModuleType, github: GitHub, monkeypatch: pytest.MonkeyPatch, expected_head_sha: str) -> None:
    """A numeric hint cannot authorize writes for an unrelated run's commit."""
    monkeypatch.setenv("PR_HEAD_SHA", expected_head_sha)
    with pytest.raises(ValueError, match="head commit does not match the triggering workflow run"):
        labeler.label_pull_request(1910)
    assert github.attached == ["rn: doc", "bug", "needs rn: review"]
    assert len(github.requests) == 1


def test_creation_race(labeler: ModuleType, github: GitHub) -> None:
    """Different PR jobs may create the same repository label concurrently."""
    github.creation_race = True
    labeler.label_pull_request(1910)
    assert "rn: fix(anta|anta.tests)!" in github.attached
    assert "rn: doc" not in github.attached


@pytest.mark.parametrize(
    ("operation", "status", "message"),
    [
        (("GET", "labels/rn%3A%20fix%28anta%7Canta.tests%29%21"), 500, "Internal Server Error"),
        (("POST", "labels"), 403, "Resource not accessible by integration"),
        (("POST", "labels"), 422, "Validation Failed"),
        (("POST", "issues/1910/labels"), 403, "Resource not accessible by integration"),
    ],
)
def test_failed_add_preserves_old_labels(
    labeler: ModuleType, github: GitHub, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], operation: tuple[str, str], status: int, message: str
) -> None:
    """Report the failing endpoint and reason without removing existing labels."""
    github.failures[operation] = [status]
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "label", "1910"])
    assert labeler.main() == 1
    assert github.attached == ["rn: doc", "bug", "needs rn: review"]
    diagnostic = capsys.readouterr().err
    assert f"{operation[0]} {operation[1]} failed (HTTP {status})" in diagnostic
    assert message in diagnostic
    assert "test-token" not in diagnostic


def test_retry_after_failed_delete(labeler: ModuleType, github: GitHub) -> None:
    """A partial update leaves the desired label attached and converges on retry."""
    github.failures[("DELETE", "issues/1910/labels/rn%3A%20doc")] = [403]
    with pytest.raises(labeler.GitHubAPIError, match="HTTP 403"):
        labeler.label_pull_request(1910)
    assert {"rn: doc", "rn: fix(anta|anta.tests)!"} <= set(github.attached)
    labeler.label_pull_request(1910)
    assert set(github.attached) == {"rn: fix(anta|anta.tests)!", "bug", "needs rn: review"}


@pytest.mark.parametrize("title", [": missing prefix", f"{'x' * 47}: too long"])
def test_invalid_label_fails_before_mutation(labeler: ModuleType, github: GitHub, title: str) -> None:
    """Explain invalid title-derived labels while preserving prior state."""
    github.title = title
    with pytest.raises(ValueError, match="invalid release-note label"):
        labeler.label_pull_request(1910)
    assert github.attached == ["rn: doc", "bug", "needs rn: review"]


def test_title_is_data(labeler: ModuleType, github: GitHub, tmp_path: Path) -> None:
    """Shell metacharacters in a PR title are JSON data and never executed."""
    marker = tmp_path / "executed"
    github.title = f"fix: $(touch {marker})"
    labeler.label_pull_request(1910)
    assert "rn: fix" in github.attached
    assert not marker.exists()
    github.title = "fix/$(echo owned): metacharacters in the prefix"
    labeler.label_pull_request(1910)
    assert "rn: fix/$(echoowned)" in github.attached


@pytest.mark.parametrize(
    "payload",
    [
        "null",
        "[]",
        "{}",
        '{"number": true}',
        '{"number": 0}',
        '{"number": -1}',
        '{"number": 1.0}',
        '{"number": "1910"}',
        '{"number": 1910, "title": "feat: forged"}',
        "not json",
    ],
)
def test_rejects_untrusted_requests(labeler: ModuleType, tmp_path: Path, payload: str) -> None:
    """No booleans, strings, extra metadata, or invalid JSON reach job outputs."""
    request = tmp_path / "request.json"
    request.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match=r"positive integer|Expecting value"):
        labeler.read_request(request)


def test_request_limits_and_diagnostics(labeler: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Accept the producer's number and explain missing or oversized artifacts."""
    request = tmp_path / "request.json"
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "read-request", str(request)])
    assert labeler.main() == 1
    assert "Release-note labeling failed:" in capsys.readouterr().err
    request.write_text(json.dumps({"number": 1910}), encoding="utf-8")
    assert labeler.main() == 0
    assert capsys.readouterr().out == "1910\n"
    request.write_text(" " * 129, encoding="utf-8")
    assert labeler.main() == 1
    assert "request exceeds 128 bytes" in capsys.readouterr().err


def test_network_failure_diagnostic(labeler: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """A transport failure gives the maintainer an actionable reason."""

    def fail_connection(*_args: object, **_kwargs: object) -> None:
        message = "connection timed out"
        raise URLError(message)

    monkeypatch.setattr(labeler, "urlopen", fail_connection)
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "label", "1910"])
    assert labeler.main() == 1
    assert "connection timed out" in capsys.readouterr().err


def test_workflow_trust_boundary() -> None:
    """Pin trusted checkouts and isolate artifact read permissions from writes."""
    workflows = ROOT / ".github" / "workflows"
    producer = yaml.safe_load((workflows / "pull-request-rn-label-request.yml").read_text(encoding="utf-8"))
    consumer = yaml.safe_load((workflows / "pull-request-rn-labeler.yml").read_text(encoding="utf-8"))
    # PyYAML uses YAML 1.1, where the GitHub Actions key `on` parses as True.
    assert producer[True]["pull_request"]["types"] == ["closed", "edited"]
    assert producer["permissions"] == {}
    assert not any("actions/checkout@" in step.get("uses", "") for step in producer["jobs"]["request"]["steps"])
    assert consumer[True]["workflow_run"]["workflows"] == [producer["name"]]
    reader, writer = consumer["jobs"]["read_request"], consumer["jobs"]["label"]
    assert reader["permissions"] == {"actions": "read", "contents": "read"}
    assert writer["permissions"] == {"contents": "read", "pull-requests": "write"}
    assert writer["concurrency"]["group"] == "release-note-labels-${{ needs.read_request.outputs.number }}"
    assert writer["concurrency"]["cancel-in-progress"] is False
    apply_labels = next(step for step in writer["steps"] if step.get("name") == "Label the current merged PR")
    assert apply_labels["env"]["PR_HEAD_SHA"] == "${{ github.event.workflow_run.head_sha }}"
    for job in (reader, writer):
        checkout = next(step for step in job["steps"] if "actions/checkout@" in step.get("uses", ""))
        assert checkout["with"]["ref"] == "${{ github.sha }}"
        assert checkout["with"]["persist-credentials"] is False
    download = next(step for step in reader["steps"] if "actions/download-artifact@" in step.get("uses", ""))
    assert download["with"]["run-id"] == "${{ github.event.workflow_run.id }}"
    assert download["with"]["path"].startswith("${{ runner.temp }}/")
