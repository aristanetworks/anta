#!/usr/bin/env python
# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Order deployed documentation versions and remove superseded prereleases."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

LOGGER = logging.getLogger(__name__)
MAIN_VERSION = "main"

VersionEntry = dict[str, Any]


class VersionMetadataError(ValueError):
    """Raised when deployed documentation metadata is unsafe or malformed."""


def _parse_version(identifier: str) -> Version | None:
    """Parse a deployed version, treating ``main`` as a special version."""
    if identifier == MAIN_VERSION:
        return None

    try:
        return Version(identifier.removeprefix("v"))
    except InvalidVersion as error:
        msg = f"Invalid deployed documentation version: {identifier!r}"
        raise VersionMetadataError(msg) from error


def _validate_entries(entries: object) -> list[tuple[VersionEntry, Version | None]]:
    """Validate and parse entries from ``versions.json``."""
    if not isinstance(entries, list):
        msg = "versions.json must contain a list"
        raise VersionMetadataError(msg)

    validated: list[tuple[VersionEntry, Version | None]] = []
    seen_versions: set[str] = set()

    for entry in entries:
        if not isinstance(entry, dict):
            msg = "Each versions.json entry must be an object"
            raise VersionMetadataError(msg)

        version = entry.get("version")
        title = entry.get("title")
        aliases = entry.get("aliases")
        if not isinstance(version, str) or not isinstance(title, str) or not isinstance(aliases, list) or not all(isinstance(alias, str) for alias in aliases):
            msg = "Each versions.json entry must contain string version/title fields and a list of string aliases"
            raise VersionMetadataError(msg)
        if version in seen_versions:
            msg = f"Duplicate deployed documentation version: {version!r}"
            raise VersionMetadataError(msg)

        seen_versions.add(version)
        validated.append((entry, _parse_version(version)))

    return validated


# The pinned Zensical-compatible Mike fork always rewrites versions.json using
# a hard-coded reverse LooseVersion sort in mike.versions.Versions.__iter__.
# It provides no CLI or configuration hook to append, position, or otherwise
# order versions. Keep this post-processing workaround until Mike exposes a
# supported ordering mechanism.
def order_and_filter_versions(entries: object, final_version: str | None = None) -> tuple[list[VersionEntry], list[VersionEntry]]:
    """Order version entries and select same-base prereleases for removal."""
    validated = _validate_entries(entries)
    removed: list[VersionEntry] = []

    if final_version is not None:
        parsed_final = _parse_version(final_version)
        if parsed_final is None or parsed_final.is_prerelease:
            msg = f"Cleanup requires a final PEP 440 release version, got {final_version!r}"
            raise VersionMetadataError(msg)
        if final_version not in {entry["version"] for entry, _ in validated}:
            msg = f"Final documentation version {final_version!r} is not deployed"
            raise VersionMetadataError(msg)

        retained: list[tuple[VersionEntry, Version | None]] = []
        for entry, parsed_version in validated:
            if parsed_version is not None and parsed_version.is_prerelease and parsed_version.base_version == parsed_final.base_version:
                removed.append(entry)
            else:
                retained.append((entry, parsed_version))
        validated = retained

    main_entries = [entry for entry, parsed_version in validated if parsed_version is None]
    finals = sorted(
        ((entry, parsed_version) for entry, parsed_version in validated if parsed_version is not None and not parsed_version.is_prerelease),
        key=lambda item: item[1],
        reverse=True,
    )
    prereleases = sorted(
        ((entry, parsed_version) for entry, parsed_version in validated if parsed_version is not None and parsed_version.is_prerelease),
        key=lambda item: item[1],
        reverse=True,
    )
    return [*main_entries, *(entry for entry, _ in finals), *(entry for entry, _ in prereleases)], removed


def _safe_deployment_path(deployment_root: Path, identifier: str) -> Path:
    """Resolve a safe, top-level version or alias path."""
    if not identifier or identifier in {".", ".."} or Path(identifier).name != identifier or "/" in identifier or "\\" in identifier:
        msg = f"Unsafe deployed documentation path: {identifier!r}"
        raise VersionMetadataError(msg)

    path = deployment_root / identifier
    if not path.exists() and not path.is_symlink():
        msg = f"Deployed documentation path does not exist: {path}"
        raise VersionMetadataError(msg)
    return path


def manage_doc_versions(deployment_root: Path, final_version: str | None = None) -> list[str]:
    """Normalize ``versions.json`` and remove superseded prerelease content."""
    versions_path = deployment_root / "versions.json"
    try:
        entries = json.loads(versions_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        msg = f"Unable to read deployed documentation metadata from {versions_path}"
        raise VersionMetadataError(msg) from error

    ordered_entries, removed_entries = order_and_filter_versions(entries, final_version)
    paths_to_remove = [_safe_deployment_path(deployment_root, identifier) for entry in removed_entries for identifier in [entry["version"], *entry["aliases"]]]

    for path in paths_to_remove:
        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)

    versions_path.write_text(f"{json.dumps(ordered_entries, indent=2)}\n", encoding="utf-8")
    removed_versions = [entry["version"] for entry in removed_entries]
    if removed_versions:
        LOGGER.info("Removed superseded documentation versions: %s", ", ".join(removed_versions))
    LOGGER.info("Documentation version order: %s", ", ".join(entry["version"] for entry in ordered_entries))
    return removed_versions


def main() -> None:
    """Run documentation version management from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deployment_root", type=Path, help="Checked-out documentation deployment root")
    parser.add_argument("--final-version", help="Final release whose same-base prerelease documentation should be removed")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    manage_doc_versions(args.deployment_root, args.final_version)


if __name__ == "__main__":
    main()
