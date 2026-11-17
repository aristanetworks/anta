# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Refresh release-note labels using trusted code and current GitHub PR metadata.

The artifact is an untrusted candidate PR number. Its current API head commit
must match the triggering run's trusted head SHA. Only merged PRs in
GITHUB_REPOSITORY are labeled, using their current API title.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GitHubAPIError(RuntimeError):
    """A GitHub API failure with the operation, status, and server diagnostic."""

    def __init__(self, method: str, path: str, error: HTTPError) -> None:
        self.status = error.code
        try:
            diagnostic = json.load(error)
        except (ValueError, UnicodeError):
            diagnostic = {"message": str(error.reason)}
        super().__init__(f"{method} {path} failed (HTTP {error.code}): {diagnostic}")


def github_api(method: str, path: str, data: dict | None = None) -> dict | list | None:
    """Call the current repository's REST API without invoking a shell."""
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    repository = os.environ["GITHUB_REPOSITORY"]
    request = Request(
        f"{api_url}/repos/{repository}/{path}",
        method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read()
    except HTTPError as error:
        raise GitHubAPIError(method, path, error) from error
    return json.loads(body) if body else None


def read_request(path: Path) -> int:
    """Accept only a small JSON object containing a positive integer PR number."""
    if path.stat().st_size > 128:
        raise ValueError("PR-number request exceeds 128 bytes")
    request = json.loads(path.read_text(encoding="utf-8"))
    # Booleans are rejected because Python treats bool as a subclass of int.
    # pylint: disable-next=unidiomatic-typecheck
    if not isinstance(request, dict) or set(request) != {"number"} or type(request["number"]) is not int or request["number"] <= 0:
        raise ValueError("Expected a JSON object containing only a positive integer 'number'")
    return request["number"]


def ensure_label(name: str) -> str:
    """Return the API's canonical label name, creating it if necessary."""
    path = f"labels/{quote(name, safe='')}"
    try:
        return github_api("GET", path)["name"]
    except GitHubAPIError as error:
        if error.status != 404:
            raise
        try:
            return github_api("POST", "labels", {"name": name, "color": "ededed"})["name"]
        except GitHubAPIError as create_error:
            if create_error.status != 422:
                raise
            # A 422 can mean either a creation race or invalid input. Confirm the
            # label really exists; preserve the original failure if it does not.
            try:
                return github_api("GET", path)["name"]
            except GitHubAPIError:
                raise create_error from None


def label_pull_request(number: int) -> None:
    """Refresh only rn: labels on a merged PR, preserving other labels."""
    if number <= 0:
        raise ValueError("PR number must be a positive integer")
    pull_request = github_api("GET", f"pulls/{number}")
    if not pull_request["merged"]:
        print(f"Skipping PR #{number}: it has not been merged.")
        return
    expected_head_sha = os.environ.get("PR_HEAD_SHA")
    if not expected_head_sha or pull_request["head"]["sha"] != expected_head_sha:
        raise ValueError(f"PR #{number} head commit does not match the triggering workflow run; refusing to update labels")

    prefix = pull_request["title"].split(":", 1)[0].replace(" ", "").replace(",", "|")
    desired_label = f"rn: {prefix}"
    if not prefix or len(desired_label) > 50:
        raise ValueError(f"PR #{number} title produces an invalid release-note label (expected 1-50 characters): {desired_label!r}")

    # Paginate independently of the PR response so stale rn: labels cannot hide
    # behind the first page of unrelated labels.
    old_labels = set()
    page = 1
    while True:
        labels = github_api("GET", f"issues/{number}/labels?per_page=100&page={page}")
        old_labels.update(label["name"] for label in labels)
        if len(labels) < 100:
            break
        page += 1

    # Add first: a permission or creation failure must not erase the old label.
    if desired_label not in old_labels:
        # GitHub label lookups are case-insensitive. Use the stored name so an
        # existing differently-cased label is not subsequently removed as stale.
        desired_label = ensure_label(desired_label)
        if desired_label not in old_labels:
            github_api("POST", f"issues/{number}/labels", {"labels": [desired_label]})

    for name in sorted(old_labels):
        if name.startswith("rn: ") and name != desired_label:
            github_api("DELETE", f"issues/{number}/labels/{quote(name, safe='')}")
    print(f"PR #{number}: release-note label is {desired_label!r}.")


def main() -> int:
    """Run one trusted stage of the release-note label handoff."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    reader = commands.add_parser("read-request", help="Validate an untrusted PR-number artifact")
    reader.add_argument("path", type=Path)
    labeler = commands.add_parser("label", help="Refresh a merged PR's release-note labels")
    labeler.add_argument("number", type=int)
    args = parser.parse_args()
    try:
        if args.command == "read-request":
            print(read_request(args.path))
        else:
            label_pull_request(args.number)
    except (OSError, ValueError, RuntimeError, URLError) as error:
        print(f"Release-note labeling failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
