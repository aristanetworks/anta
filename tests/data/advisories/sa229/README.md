<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# SA229 boot-control evidence

Sanitized observations from DCS-7280SR3M-48YC8-F running EOS 4.35.6M, with a
`tg3` management NIC, captured during lab qualification on November 25, 2026.

`boot-handler.json` contains the temporary handler's observed entry from native
`show event-handler` JSON output. Unrelated handlers, device addresses, and
credentials are excluded. The temporary handler was removed after the experiment.

The test treats this as evidence that the boot control is configured, not proof
of effective receive-channel settings. It never executes the action or collects
Bash output. Mutated, disabled, incomplete, and malformed handler records in unit
tests are synthetic variants of this captured JSON.
