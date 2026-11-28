# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# Zensical loads this standalone callback by path, outside a Python package.
# ruff: noqa: INP001
"""Prepare export-only HTML for Zensical's Markdown converter."""

from __future__ import annotations

from bs4 import BeautifulSoup


def preprocess(html: str, _output: str) -> str:
    """Retain API semantics and link text without modifying browser HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # The normal Mermaid block contains the diagram; this is a duplicate for zoom.
    for source in soup.select(".mermaid-zoom-source"):
        source.decompose()

    # Native cleanup discards the badges. Preserve all labels in the export copy.
    for labels in soup.select(".doc-labels"):
        text = ", ".join(labels.stripped_strings)
        labels.replace_with(f" ({text})" if text else "")

    # Native cleanup drops whole links containing inline icons, including their text.
    # Retain meaningful emoji alt text, and leave ordinary content images alone.
    for icon in soup.select("a .twemoji"):
        alt = icon.get("alt", "")
        icon.replace_with(alt if isinstance(alt, str) else "")
    for icon in soup.select("a svg"):
        icon.decompose()

    return str(soup)
