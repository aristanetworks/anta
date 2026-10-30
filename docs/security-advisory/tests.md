---
title: Security Advisory Tests
hide:
  - tags
tags:
  - API
  - Tests
  - Security
---

<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

This page documents each security advisory test currently implemented in ANTA.
See the [Security Advisory Tests Overview](tests-overview.md) for the support
matrix.

Each test's expected results use the advisory assessment states described in
[Security Advisory Reports](reports.md#interpret-results). Standard ANTA test
statuses map these states as follows: Not Affected and Mitigated are success,
Affected and Inconclusive are failure, and Error is error.

## SA178: credential syntax and hotfix assessment

SA178 checks both local and remote SNMPv3 authentication keys using the current EOS release, applicable persistent SWIX, and credential syntax.
On affected releases, encrypted syntax without an effective applicable SWIX remains Affected; encrypted syntax with that SWIX is Mitigated.
Legacy syntax remains Affected on both fixed and hotfixed software because installing the SWIX or upgrading does not convert existing credentials.

For configured authentication keys and available required evidence:

| Credential syntax | EOS release | SWIX state | Assessment | Remediation |
| --- | --- | --- | --- | --- |
| Legacy | Affected | Effective and applicable | Affected | Convert credentials with the SWIX active. |
| Legacy | Affected | Absent, ineffective, or not applicable | Affected | Upgrade to a fixed release, then convert credentials. |
| Legacy | Fixed | Any; ignored | Affected | Convert credentials. |
| Encrypted | Affected | Effective and applicable | Mitigated | Preserve the SWIX; follow fixed-release upgrade guidance. |
| Encrypted | Affected | Absent, ineffective, or not applicable | Affected | Upgrade to a fixed release, then convert credentials. |
| Encrypted | Fixed | Any; ignored | Not Affected | None. |

Conversion guidance means running `configure convert new-syntax`. An effective applicable SWIX must match a documented eligible release and be
installed and boot-persistent. Affected produces ANTA failure; Mitigated and Not Affected produce ANTA success.

The assessment classifies current software, hotfix, and credential syntax. It does not establish whether or when credential conversion was
performed. Copying encrypted credentials between releases is outside its scope. Salt offsets alone cannot establish whether a key is affected;
the assessment does not decode credential payloads or classify keys by salt offset.

If no authentication keys are configured, the result is Not Affected even when software or SWIX evidence is unavailable. Otherwise, missing
required evidence produces Error. Fixed releases with encrypted credentials remain Not Affected without requiring SWIX evidence.

## Test reference

::: anta.tests.advisories

    options:
      extra:
          anta_hide_test_module_description: true
      members:
        - SA178
        - SA177
        - SA176
        - SA175
        - SA174
        - SA173
        - SA172
        - SA171
        - SA170
        - SA169
        - SA168
        - SA167
        - SA166
        - SA165
        - SA164
        - SA163
        - SA162
        - SA161
        - SA160
        - SA159
        - SA158
        - SA157
        - SA156
        - SA155
        - SA154
        - SA153
        - SA152
        - SA151
        - SA150
        - SA149
        - SA147
        - SA146
        - SA142
        - SA140
        - SA117
      filters:
        - "^SA"
      merge_init_into_class: false
      show_bases: false
      show_docstring_examples: false
      show_labels: true
      show_root_heading: false
      show_root_toc_entry: false
      show_symbol_type_heading: false
      show_symbol_type_toc: false
