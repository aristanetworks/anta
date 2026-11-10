---
id: ADR-0004
title: Preserve decisive evidence when aggregating scoped observations
status: accepted
date: 2026-11-09
supersedes: []
superseded_by: []
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# ADR-0004: Preserve decisive evidence when aggregating scoped observations

## Context

Facts often walk interfaces, peers, or other scoped records. Returning on the first
parsing error can discard an independently proven exposure and make the conclusion
depend on traversal order. This records the aggregation pattern used for SA225.

## Decision

For a condition satisfied by **at least one** qualifying observation:

1. Correlate observations with the required scope, such as linecard slot, VRF, or
   address family. Facts retain neutral device evidence; advisories select the
   relevant scopes and apply vulnerability rules.
2. Use **proven presence > relevant uncertainty > proven absence**. A valid positive
   observation survives errors in other records. With the other prerequisites
   established and no complete verified mitigation, the result is `AFFECTED`.
3. Without a positive observation, missing coverage or a required parsing failure
   prevents `NOT_AFFECTED`. Preserve applicable required problems and their command
   sources. Errors in decisively excluded scopes do not affect the conclusion.
4. Compact summaries per scope are sufficient: whether the scope was observed,
   whether presence was proved, and representative problem/witness evidence. Keep
   partial evidence explicit; a missing positive observation does not prove absence.
   The conclusion must be independent of traversal order.
5. A positive observation must itself be trustworthy. Contradictory data about that
   observation or malformed scope boundaries remain errors when they prevent its
   interpretation. Conditions requiring **every** member, including complete
   mitigation coverage, must verify every required member before concluding safety.

This refines aggregation under [advisory assessment states](0001%20-%20Advisory%20assessment%20states.md)
without changing their meanings.
