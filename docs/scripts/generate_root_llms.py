#!/usr/bin/env python
# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Publish LLM export discovery after normalizing a Mike deployment."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from urllib.parse import quote, urljoin


def generate_root_llms(deployment_root: Path, config_path: Path) -> None:
    """List only deployed export indexes, preferring stable before development."""
    with config_path.open("rb") as config_file:
        site_url = tomllib.load(config_file)["project"]["site_url"].rstrip("/") + "/"
    versions = json.loads((deployment_root / "versions.json").read_text(encoding="utf-8"))
    links: list[tuple[int, str]] = []
    for entry in versions:
        version = entry["version"]
        if not (deployment_root / version / "llms.txt").is_file():
            continue
        destination = version
        if "stable" in entry["aliases"]:
            title, priority = f"Stable ({version})", 0
            if (deployment_root / "stable" / "llms.txt").is_file():
                destination = "stable"
        elif version == "main":
            title, priority = "Development (main)", 1
        else:
            title, priority = version, 2
        url = urljoin(site_url, f"{quote(destination, safe='')}/llms.txt")
        links.append((priority, f"- [{title}](<{url}>)"))

    if not links:
        msg = f"No versioned llms.txt exports found under {deployment_root}; leaving the root index unchanged"
        raise ValueError(msg)
    # Stable sorting retains the normalized release order within each priority.
    links.sort(key=lambda link: link[0])
    content = (
        "# Arista Network Test Automation - ANTA\n\n"
        "> Versioned documentation indexes for ANTA network validation.\n\n"
        "Choose the documentation version matching your installed ANTA package. "
        "The main index describes unreleased development. "
        "Each version index links to rendered Markdown pages.\n\n"
        "## Documentation versions\n\n"
    )
    (deployment_root / "llms.txt").write_text(content + "\n".join(link for _, link in links) + "\n", encoding="utf-8")


def main() -> None:
    """Generate the root index before the deployment is committed and pushed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deployment_root", type=Path)
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[2] / "zensical.toml")
    args = parser.parse_args()
    try:
        generate_root_llms(args.deployment_root, args.config)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Cannot generate root llms.txt: {error}\n")


if __name__ == "__main__":
    main()
