<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 0002 - Agent tracing as an exposure condition

- Status: Accepted
- Date: 2026-10-28

## Context

Some advisories condition exposure on an EOS agent trace facility and level, typically because the trace writes secrets to agent logs. Decision 0001 makes the absence of a necessary feature `NOT_AFFECTED` and forbids future operator actions from softening `AFFECTED`, but it does not say which of the two applies to tracing.

Trace state is not reliably observable from the device:

- Persistent `trace <agent> setting` configuration accepts regex selectors, wildcards, level ranges, and negated directives.
- The exec command `start trace <agent> setting <facility>/<level> timeout <duration>` enables tracing without any running-config record.
- `show trace <agent>` reports an exec trace level only while its timer runs. A facility can also be missing from its output until the agent handles work, for example before the first gNPSI subscription.

For SA158, a timed exec trace of `EosRpcAuth/7` wrote a gNPSI client password to the Gnpsi agent log in clear text. It left no running-config entry, and `show trace Gnpsi` stopped reporting level 7 once the timer expired.

## Decision

1. Enabling an agent trace is an operator action under decision 0001 item 4. Missing trace configuration or empty `show trace` output is not disablement of a necessary feature under decision 0001 item 3 and is not a mitigation.

2. When an advisory conditions exposure on agent tracing, the assessment MUST derive the result from the advisory's other conditions. Trace configuration and `show trace` output MUST NOT produce `NOT_AFFECTED`, `MITIGATED`, or `INCONCLUSIVE`.

3. This applies even when the advisory names trace as a required condition or presents disabling trace as a workaround or mitigation. Trace-related guidance, such as cleaning logs or rotating credentials that were logged, MAY appear as conditional remediation.

4. Observed trace state MAY be reported as context. It MUST NOT change the result.

5. This decision concerns runtime diagnostics that can be active without a durable, observable device record. Another diagnostic mechanism follows it only once that property is established. Persistent feature configuration remains assessed under decision 0001: the possibility that an operator configures a vulnerable feature later does not make a device `AFFECTED`.

## Consequences

Trace-conditioned issues report `AFFECTED` on devices where the advisory's literal conditions do not currently hold. This is accepted because the device cannot show that the trace is not, or will not be, enabled. Existing tests that derive their result from trace state must be updated to follow this decision.
