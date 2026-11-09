---
id: ADR-0003
title: Keep affected release trains unbounded without a published fix
status: accepted
date: 2026-11-05
supersedes: []
superseded_by: []
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# ADR-0003: Keep affected release trains unbounded without a published fix

## Context

An advisory may list “4.32.11M and below” as affected without naming a fixed release in the 4.32 train. That upper limit does not establish that a later patch contains the fix. For example, 4.32.12M must not be assumed fixed merely because it falls outside the listed range; this example does not assert that the release exists.

## Decision

When an advisory identifies affected releases in a train but publishes no fixed release in that train, conservatively treat the whole train as affected for software-version assessment. Do not return `NOT_AFFECTED` for a later patch solely because it exceeds the listed affected upper limit. A generic “unlisted releases are not vulnerable” notice does not override this rule.

Once a fixed release is published for that train, use it as the upper boundary of affected software scope. Until then, keeping the train affected is a conservative assessment policy, not proof that every later patch contains the vulnerability.
