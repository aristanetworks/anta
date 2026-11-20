# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tag resolution engine for bug database matching.

Resolves device tags from two sources:
1. Hardware/platform tags — derived from the device model name via ``tagImplication``.
2. Feature tags — determined by evaluating AQL queryRules against SysDB data.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import TYPE_CHECKING

from anta.bugdb.aql import AqlNode, aql_compile, aql_evaluate
from anta.bugdb.sysdb import fetch_sysdb_paths

if TYPE_CHECKING:
    from anta.bugdb.models import QueryRule
    from anta.device import AntaDevice

logger = logging.getLogger(__name__)

# Suffixes stripped from device model names for tag matching
_MODEL_SUFFIXES = ["-SSD-F", "-SSD-R", "-M-F", "-M-R", "-F", "-R"]


def build_implication_graph(tag_implications: list[list[str]]) -> dict[str, set[str]]:
    """Build a tag implication graph from ``tagImplication`` entries.

    Parameters
    ----------
    tag_implications
        List of ``[source_tag, implied_tag]`` pairs.

    Returns
    -------
    dict[str, set[str]]
        Mapping from each tag to the set of tags it implies (transitive closure).
    """
    direct: dict[str, set[str]] = defaultdict(set)
    for pair in tag_implications:
        if len(pair) == 2:  # noqa: PLR2004
            direct[pair[0]].add(pair[1])

    # Compute transitive closure via BFS
    closure: dict[str, set[str]] = {}
    for source, implied in direct.items():
        visited: set[str] = set()
        queue = list(implied)
        while queue:
            tag = queue.pop(0)
            if tag in visited:
                continue
            visited.add(tag)
            if tag in direct:
                queue.extend(direct[tag] - visited)
        closure[source] = visited

    return closure


def resolve_hardware_tags(hw_model: str | None, implication_graph: dict[str, set[str]]) -> set[str]:
    """Resolve hardware and platform tags from a device's model name.

    Uses the ``tagImplication`` graph to transitively expand model identifiers
    into all implied tags (ASIC family, platform series, etc.).

    Parameters
    ----------
    hw_model
        The device's hardware model from ``show version`` (e.g. ``DCS-7280SR3-48YC8-F``).
    implication_graph
        Precomputed transitive closure of tag implications.

    Returns
    -------
    set[str]
        All tags that apply to the device based on its hardware.
    """
    if not hw_model:
        return set()

    tags: set[str] = set()

    # Generate candidate tag keys from the model name
    candidates = _extract_model_candidates(hw_model)

    for candidate in candidates:
        # Direct match in implication graph
        if candidate in implication_graph:
            tags.add(candidate)
            tags.update(implication_graph[candidate])

    # Also add the full model name as a tag (some bugs reference exact SKUs)
    tags.add(hw_model)

    return tags


def _extract_model_candidates(hw_model: str) -> list[str]:
    """Extract candidate tag keys from a device model name.

    From ``DCS-7280SR3-48YC8-F`` generates candidates like:
    ``DCS-7280SR3-48YC8``, ``7280SR3-48YC8``, ``7280SR3``, ``7280``, etc.
    """
    candidates: list[str] = [hw_model]

    # Strip common suffixes
    stripped = hw_model
    for suffix in _MODEL_SUFFIXES:
        stripped = stripped.replace(suffix, "")
    if stripped != hw_model:
        candidates.append(stripped)

    # Without DCS- prefix
    no_prefix = stripped
    if no_prefix.startswith("DCS-"):
        no_prefix = no_prefix[4:]
        candidates.append(no_prefix)
        candidates.append(f"DCS-{no_prefix}")

    # Extract the platform series (e.g. "7280SR3" from "7280SR3-48YC8")
    m = re.match(r"(\d+[A-Za-z]*\d*)", no_prefix)
    if m:
        series = m.group(1)
        if series != no_prefix:
            candidates.append(series)

    return candidates


def compile_query_rules(query_rules: list[QueryRule]) -> dict[str, tuple[AqlNode, list[str]]]:
    """Compile AQL query rules into ASTs, selecting the highest revision per tag.

    Parameters
    ----------
    query_rules
        Combined list of ``queryRules`` and ``queryRulesRev`` entries.

    Returns
    -------
    dict[str, tuple[AqlNode, list[str]]]
        Mapping from tag name to ``(compiled_ast, path_filters)``.
    """
    # Group rules by tag, then try revisions in descending order
    rules_by_tag: dict[str, list[QueryRule]] = defaultdict(list)
    for rule in query_rules:
        rules_by_tag[rule.tag].append(rule)

    compiled: dict[str, tuple[AqlNode, list[str]]] = {}
    for tag, rules in rules_by_tag.items():
        for rule in sorted(rules, key=lambda r: r.revision, reverse=True):
            try:
                compiled[tag] = (aql_compile(rule.query), rule.path_filters)
                break
            except SyntaxError:
                logger.debug("Failed to compile AQL rule for tag '%s' rev %s", tag, rule.revision)

    return compiled


async def resolve_feature_tags(
    device: AntaDevice,
    compiled_rules: dict[str, tuple[AqlNode, list[str]]],
) -> set[str]:
    """Resolve feature tags by evaluating AQL rules against device SysDB data.

    Parameters
    ----------
    device
        The ANTA device to query.
    compiled_rules
        Pre-compiled AQL rules from ``compile_query_rules``.

    Returns
    -------
    set[str]
        Set of feature tags that apply to the device.
    """
    # Collect all unique paths to fetch
    all_paths: set[str] = set()
    for _ast, path_filters in compiled_rules.values():
        all_paths.update(path_filters)

    # Fetch all paths from the device in one batch
    sysdb_data = await fetch_sysdb_paths(device, all_paths)

    # Evaluate each rule
    tags: set[str] = set()
    for tag, (ast, _path_filters) in compiled_rules.items():
        try:
            if aql_evaluate(ast, sysdb_data):
                tags.add(tag)
        except Exception:  # noqa: BLE001, PERF203
            logger.debug("Error evaluating AQL rule for tag '%s' on %s", tag, device.name)

    return tags


async def resolve_all_tags(
    device: AntaDevice,
    implication_graph: dict[str, set[str]],
    compiled_rules: dict[str, tuple[AqlNode, list[str]]],
) -> set[str]:
    """Resolve all tags (hardware + feature) for a device.

    Parameters
    ----------
    device
        The ANTA device to query.
    implication_graph
        Precomputed tag implication graph.
    compiled_rules
        Pre-compiled AQL query rules.

    Returns
    -------
    set[str]
        Complete set of tags for the device.
    """
    hw_tags = resolve_hardware_tags(device.hw_model, implication_graph)
    feature_tags = await resolve_feature_tags(device, compiled_rules)
    return hw_tags | feature_tags
