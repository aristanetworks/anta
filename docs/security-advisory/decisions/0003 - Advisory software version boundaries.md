<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 0003 - Advisory software version boundaries

- Status: Proposed
- Date: 2026-11-05

## Decision

1. Assess software scope independently for each vulnerability and component. Preserve published introduction versions, release trains, suffix exceptions, and hotfix distinctions.

2. Bound an affected train only at a published fixed release or an explicit version-specific exclusion. Otherwise, keep later patches in that train in affected scope. Do not extend scope to unrelated trains or major versions, or infer their safety from version ordering alone.

3. Preserve the complete scope of “all releases in this train” and “all prior releases”; do not introduce patch caps.

4. Continue checking required configuration or credential conversion after an upgrade. A fixed software version alone does not prove that the device is no longer exposed.

5. Distinguish outside affected scope from explicitly fixed. Name only published fixes in remediation; if none is published, say so. Software scope alone does not establish `AFFECTED` without the other required exposure conditions.

6. Test affected, fixed, and excluded boundaries, including significant suffixes, hotfixes, and post-upgrade requirements. Synthetic patch numbers may verify unbounded trains but must not be presented as released versions.

## Pending agreement

Proposed precedence: specific affected, fixed, and unaffected-version statements override a generic “unlisted releases are not vulnerable” notice. An explicit “no fixed release available” statement therefore prevents that notice alone from bounding an affected train. Confirm this precedence before accepting the ADR. Contradictory specific statements require publisher clarification; they do not redefine the assessment states in decision 0001.
