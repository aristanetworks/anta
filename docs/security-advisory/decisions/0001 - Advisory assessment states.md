<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 0001 — Advisory assessment states

- Status: Accepted
- Date: 2026-09-07

## Context

ANTA exposes success, failure, inconclusive, error, and skipped. Advisory evaluation also needs typed conclusions that distinguish inherent uncertainty, unavailable input, verified mitigation, and absence of exposure. ANTA does not yet expose a dedicated mitigated status.

## Decision

1. Each vulnerability or independently identified issue MUST produce exactly one `VulnerabilityResult`: `NotAffectedResult`, `AffectedResult`, `MitigatedResult`, `InconclusiveResult`, or `ErrorResult`. Assessment code MUST return this typed result without setting or rendering an ANTA result.

2. The semantic states are:

   - `NOT_AFFECTED`: the device does not satisfy the advisory's conditions for vulnerability or exposure. An independently fixed release, an excluded platform, or an absent required feature are examples.
   - `AFFECTED`: the device satisfies the advisory's conditions for vulnerability or exposure, and the issue is not fully mitigated. Exploitation, compromise, attacker access, external behavior, and future operator actions do not need to be observed.
   - `MITIGATED`: the device would otherwise be `AFFECTED`, but every exposure is covered by a verified, device-enforced mitigation expressly documented by the advisory. A mitigation MUST NOT be inferred from general security practice.
   - `INCONCLUSIVE`: available device facts indicate possible vulnerability, but a fact necessary to determine the device's applicability, exposure, or mitigation is inherently unobservable. Unknown exploitation, triggering, operator behavior, or external behavior MUST NOT turn an otherwise established `AFFECTED` result into `INCONCLUSIVE`.
   - `ERROR`: required observable evidence is missing, malformed, contradictory, or unavailable, or the test cannot execute its contract. `ERROR` makes no security claim.

3. Disabling a necessary vulnerable feature is `NOT_AFFECTED`, even when the advisory calls disablement a mitigation. An advisory-documented, device-enforced compensating control around an active vulnerable feature is `MITIGATED` only when its complete effective scope is observable.

4. Assessment concerns whether the device is vulnerable or exposed, not whether the vulnerability has been or will be triggered or exploited. Operational intent, unenforced recommendations, external trust assertions, and unknown future actions MUST NOT produce `MITIGATED` or soften an established `AFFECTED` result to `INCONCLUSIVE`. An advisory-documented device-enforced control over peer reachability or identity MAY produce `INCONCLUSIVE` even if its complete effective scope is observable, since correctness of the control cannot be determined.

5. IOC evidence and absence of logged exploitation MUST NOT produce `NOT_AFFECTED` or `MITIGATED`.

## Consequences

Existing tests that conflate unknown, inconclusive, mitigated, and affected conditions will require review. Native inconclusive results now preserve uncertainty in ANTA reports. Mitigated results temporarily share that native status while remaining distinguishable in the structured advisory result.
