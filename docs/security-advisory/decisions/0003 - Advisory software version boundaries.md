<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 0003 - Advisory software version boundaries

- Status: Proposed
- Date: 2026-11-05

## Context

Advisories describe affected software separately from fixed releases. An affected list may stop at the latest published patch even though the resolution does not identify a fix in that train. The next patch might not exist. Its absence from the affected list does not, by itself, establish that it contains a fix.

ANTA currently treats any valid version outside an affected-version matrix as outside affected scope. Most assessments can use that relationship to return `NOT_AFFECTED` before evaluating feature configuration. An unsupported upper boundary can therefore produce a false negative. Decision 0001 defines assessment states but does not define the evidence required for a software-version exclusion.

Some advisories also state that any release absent from the affected list is not vulnerable. When the resolution says that fixed releases are not yet available, treating this generic statement as exhaustive can conflict with the conservative interpretation of the affected list. This precedence question must be resolved before accepting this ADR.

## Proposed decision

1. Software scope MUST be assessed independently for each vulnerability and software component. An EOS fix MUST NOT imply that a separately versioned component is fixed, or vice versa. Boundaries MUST preserve published introduction versions, release trains, suffix exceptions, and hotfix distinctions.

2. An affected range MUST have an upper boundary only when supported by a published fixed release or an explicit statement identifying unaffected versions. An affected list ending at a particular patch, without a declared fix or such an exclusion, MUST NOT by itself establish that later patches in the same affected train are unaffected. The conservative default is to keep that train in affected scope, preserving any published lower boundary. This does not make the device `AFFECTED` unless the other necessary exposure conditions are satisfied.

3. Statements such as “all releases in this train” or “all prior releases” MUST retain their complete published scope. Tests MUST NOT introduce a patch cap for these ranges. Conversely, extending an affected train MUST NOT silently extend scope to unrelated trains, components, or major versions.

4. A published fixed release MAY close software scope only when no additional action is required for that exposure. When remediation also requires configuration, credential conversion, or another action, the assessment MUST retain that requirement after the upgrade. Versions MUST be compared using the advisory's release semantics; a numeric patch comparison MUST NOT discard a significant suffix or hotfix distinction.

5. Outside affected scope and explicitly fixed are distinct evidence. An explicitly excluded release MAY support `NOT_AFFECTED` without being described as fixed. Remediation MUST name only published fixed releases and MUST NOT invent the next patch as an upgrade target. If no fixed release is published, guidance MUST say so and retain any applicable published workaround.

6. An entirely unmentioned train or major version MUST NOT be classified as fixed merely because it sorts after an affected release. The assessment contract MUST establish whether the advisory's applicability statement covers that version before using it as decisive evidence for `NOT_AFFECTED`.

## Precedence requiring agreement

The proposed precedence is that specific affected, fixed, and unaffected-version statements take priority over a generic “unlisted releases are not vulnerable” notice. In particular, an explicit announcement that no fixed release is available would prevent that generic notice alone from establishing an upper boundary in an affected train. A version-specific unaffected statement would still permit an exclusion without a named fix.

This precedence is a recommendation for review, not an accepted policy. The alternative is to treat the generic notice as an exhaustive applicability contract even while fixes are pending. Acceptance MUST select one interpretation and apply it consistently. A genuine contradiction between specific statements requires clarification from the advisory publisher; this ADR does not invent a new assessment state or redefine `INCONCLUSIVE` under decision 0001.

## Examples and consequences

| Published evidence | Interpretation under the proposal |
| --- | --- |
| All 4.32.x releases are affected; no 4.32 fix is named | Keep the entire 4.32 train in software scope. |
| Affected through patch N; no fix or explicit unaffected-version statement | Keep later patches in the same affected train in scope; do not infer a fix at N+1. |
| Fixed from a named release, with no remaining required action | Use that release as the software boundary. |
| A specific version is explicitly declared unaffected | Exclude that version; a fixed-release claim is unnecessary. |
| A named upgrade requires enabling a new control | Continue assessing that control after upgrading. |

The published [SA173](https://www.arista.com/en/support/advisories-notices/security-advisory/24729-security-advisory-0173) says “All prior releases” below its 4.33 affected range. That includes every 4.32 patch, independently of the unresolved generic-notice precedence. Its correction is covered by [PR #1879](https://github.com/aristanetworks/anta/pull/1879).

SA140, SA151, and SA169 have bounded affected lists for older trains without named fixes in those trains. SA201 lists affected EOS limits while its resolution says fixed EOS releases will be announced when available. These cases require reassessment against the accepted precedence; they are not all established implementation bugs. Each reassessment MUST use the publication revision being implemented.

The conservative default can retain exposure assessments for a later release that turns out to be unaffected. That tradeoff avoids claiming safety from an inferred fix, but makes publication updates and explicit source evidence necessary to narrow scope.

## Adoption and validation

- Accepting this ADR requires resolving the precedence above. This proposal changes no runtime behavior or existing accepted ADR.
- Follow-up implementation MUST audit each affected matrix against its advisory and update assessment expectations together with the boundary rules. The current evaluator's complement behavior alone is insufficient evidence for an exclusion.
- Tests MUST cover the last affected release, any declared fixed or excluded release, significant suffix and hotfix boundaries, and assessments that retain post-upgrade requirements.
- Tests MAY use synthetic higher patch numbers to verify that an affected train is unbounded. Such cases MUST NOT be presented as evidence that those releases exist.
- No public model, API, result-state, or class-diagram change is proposed here. Any follow-up requiring a new representation of source uncertainty needs a separate design decision.
