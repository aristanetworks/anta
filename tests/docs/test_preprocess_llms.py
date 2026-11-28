# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Protect API semantics and authored content in export-only preprocessing."""

from __future__ import annotations

from html import escape

import pytest
from bs4 import BeautifulSoup

from docs.scripts.preprocess_llms import preprocess


@pytest.mark.parametrize(
    "labels",
    [("async", "abstractmethod"), ("classmethod",), ("staticmethod",), ("property", "writable"), ("dataclass",), ("deprecated",)],
)
def test_api_labels_survive_native_cleanup(labels: tuple[str, ...]) -> None:
    """Every label contributes to the heading, including combinations."""
    badges = "".join(f'<small class="doc-label"><code>{label}</code></small>' for label in labels)
    html = f'<h3 id="object">Object<span class="doc-labels">{badges}</span></h3>'

    soup = BeautifulSoup(preprocess(html, "api/device/index.md"), "html.parser")

    assert soup.h3 is not None
    assert soup.h3.get_text() == f"Object ({', '.join(labels)})"
    assert soup.h3["id"] == "object"
    assert not soup.select(".doc-labels")


def test_zoom_helpers_are_removed_without_losing_the_normal_diagram() -> None:
    """Textarea and script helpers must not duplicate or flatten diagram source."""
    diagram = 'flowchart LR\n  A["<start>"] --> B["A & B"]\n'
    html = (
        f'<textarea hidden class="mermaid-zoom-source">{escape(diagram)}</textarea>'
        f'<script type="text/plain" class="mermaid-zoom-source">{diagram}</script>'
        f'<pre class="mermaid"><code>{escape(diagram)}</code></pre>'
    )

    soup = BeautifulSoup(preprocess(html, "troubleshooting/index.md"), "html.parser")

    assert not soup.select(".mermaid-zoom-source")
    assert soup.pre is not None
    assert soup.pre.get_text() == diagram


def test_icons_do_not_erase_link_text_or_resolved_api_destinations() -> None:
    """Strip inline icons while preserving nested text, titles, and destinations."""
    html = (
        '<a href="https://docs.pydantic.dev/latest/concepts/models/" title="Pydantic">'
        '<span class="twemoji"><svg><path d="M0 0"/></svg></span>pydantic <em>models</em></a>'
        '<a href="../device/index.md#anta.device.AntaDevice.refresh" title="refresh async">refresh()</a>'
        '<a href="../target/index.md"><svg><path d="M1 1"/></svg>Target</a>'
    )

    soup = BeautifulSoup(preprocess(html, "api/class-diagram/index.md"), "html.parser")
    links = soup.find_all("a")

    assert links[0].get_text() == "pydantic models"
    assert links[0]["href"] == "https://docs.pydantic.dev/latest/concepts/models/"
    assert links[0]["title"] == "Pydantic"
    assert links[0].em is not None
    assert links[1]["href"] == "../device/index.md#anta.device.AntaDevice.refresh"
    assert links[1]["title"] == "refresh async"
    assert links[2].get_text() == "Target"
    assert not soup.select("a svg, a .twemoji")


def test_content_images_and_meaningful_emoji_are_retained() -> None:
    """Ordinary local images and remote badges must not be treated as icons."""
    html = (
        '<a href="../status/index.md"><img class="twemoji" alt="🟢" src="emoji.svg"> Available</a>'
        '<a href="../imgs/screenshot.png"><img alt="Screenshot" src="../imgs/screenshot.png"></a>'
        '<a href="https://example.org"><img alt="Build" src="https://shields.io/badge.svg"></a>'
    )

    soup = BeautifulSoup(preprocess(html, "index.md"), "html.parser")

    assert soup.a is not None
    assert soup.a.get_text() == "🟢 Available"
    assert [image["src"] for image in soup.find_all("img")] == ["../imgs/screenshot.png", "https://shields.io/badge.svg"]


def test_examples_and_source_markers_are_preserved_and_preprocessing_is_idempotent() -> None:
    """Cleanup must not rewrite literal markup examples or expose implementation code."""
    example = '<span class="doc-labels">async</span><textarea class="mermaid-zoom-source">Diagram</textarea>'
    html = (
        f"<pre><code>{escape(example)}</code></pre>"
        '<details class="mkdocstrings-source"><summary>Source</summary>Implementation</details>'
        '<h3>Unlabelled<span class="doc-labels"> </span></h3>'
    )

    output = preprocess(html, "index.md")
    soup = BeautifulSoup(output, "html.parser")

    assert soup.code is not None
    assert soup.code.get_text() == example
    assert soup.select_one("details.mkdocstrings-source") is not None
    assert soup.h3 is not None
    assert soup.h3.get_text() == "Unlabelled"
    assert preprocess(output, "index.md") == output
