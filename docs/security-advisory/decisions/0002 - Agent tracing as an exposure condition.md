<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 0002 - Agent tracing as an exposure condition

- Status: Accepted
- Date: 2026-10-28

## Context

Some advisories condition exposure on an EOS agent trace, usually because it logs secrets. Trace state is not reliably observable: `start trace <agent> setting <facility>/<level> timeout <duration>` leaves no running-config record, and `show trace <agent>` stops reporting it once the timer expires. Such a trace can log secrets without lasting device evidence.

## Decision

1. Enabling an agent trace is an operator action under decision 0001 item 4, not a necessary feature under item 3. Trace configuration and `show trace` output MUST NOT produce `NOT_AFFECTED`, `MITIGATED`, or `INCONCLUSIVE`; the result comes from the advisory's other conditions. This applies even when the advisory names trace as a condition or workaround.

2. Trace state MAY be reported as context, and trace-related cleanup MAY appear as conditional remediation.

3. This decision covers runtime diagnostics without a durable, observable device record. Persistent feature configuration remains assessed under decision 0001.
