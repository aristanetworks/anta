<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 0001 — Advisory assessment states

- Status: Accepted
- Date: 2026-09-07

## Context

ANTA exposes success, failure, error, and skipped. Advisory evaluation also needs typed conclusions that distinguish inherent uncertainty, unavailable input, verified mitigation, and absence of exposure.

## Decision

1. Each vulnerability or independently identified issue MUST produce exactly one `VulnerabilityResult`: `NotAffectedResult`, `AffectedResult`, `MitigatedResult`, `InconclusiveResult`, or `ErrorResult`. Assessment code MUST return this typed result without setting or rendering an ANTA result.

2. The semantic states are:

   - `NOT_AFFECTED`: the device does not satisfy the advisory's conditions for vulnerability or exposure. An independently fixed release, an excluded platform, or an absent required feature are examples.
   - `AFFECTED`: the device satisfies the advisory's conditions for vulnerability or exposure, and the issue is not fully mitigated. Exploitation, compromise, attacker access, external behavior, and future operator actions do not need to be observed.
   - `MITIGATED`: the device would otherwise be `AFFECTED`, but every exposure is covered by a verified, device-enforced mitigation expressly documented by the advisory. A mitigation MUST NOT be inferred from general security practice.
   - `INCONCLUSIVE`: available device facts indicate possible vulnerability, but a necessary property is not observable from device state under the supported assessment contract. Collection or parsing failures MUST NOT produce `INCONCLUSIVE`. Unknown exploitation, triggering, operator behavior, or external behavior MUST NOT soften an established `AFFECTED` result.
   - `ERROR`: evidence defined by the assessment contract as device-observable is missing, could not be collected, is malformed or contradictory, or the test cannot execute its contract. `ERROR` makes no security claim.

3. Disabling a necessary vulnerable feature is `NOT_AFFECTED`, even when the advisory calls disablement a mitigation. An advisory-documented, device-enforced compensating control around an active vulnerable feature is `MITIGATED` only when its complete effective scope is observable.

4. Assessment concerns whether the device is vulnerable or exposed, not whether the vulnerability has been or will be triggered or exploited. Operational intent, unenforced recommendations, external trust assertions, and unknown future actions MUST NOT produce `MITIGATED` or soften an established `AFFECTED` result to `INCONCLUSIVE`. An advisory-documented, device-enforced control over peer reachability or identity MAY produce `INCONCLUSIVE` when the control and its effective scope are observable, but whether the permitted peers satisfy the advisory's trust requirement cannot be determined from device state. This exception concerns peer trustworthiness; unknown peer behavior alone MUST NOT soften an established `AFFECTED` result.

5. IOC evidence and absence of logged exploitation MUST NOT produce `NOT_AFFECTED` or `MITIGATED`.

6. Advisory conclusions project onto ANTA results as follows: `NOT_AFFECTED` and `MITIGATED` are `SUCCESS`; `AFFECTED` and `INCONCLUSIVE` are `FAILURE`; and `ERROR` is `ERROR`. The semantic advisory status remains attached internally to each atomic advisory result and is used by advisory-specific reporters.
