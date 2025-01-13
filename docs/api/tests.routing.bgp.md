---
anta_title: ANTA catalog for BGP tests
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

!!! info "`multi-agent` Service Routing Protocols Model Requirements"
    The BGP tests in this section are only supported on switches running the `multi-agent` routing protocols model. Starting from EOS version 4.30.1F, `service routing protocols model` is set to `multi-agent` by default. These BGP commands may **not** be compatible with switches running the legacy `ribd` routing protocols model and may fail if attempted.

# Tests

::: anta.tests.routing.bgp

    options:
      show_root_heading: false
      show_root_toc_entry: false
      show_bases: false
      merge_init_into_class: false
      anta_hide_test_module_description: true
      show_labels: true
      filters:
        - "!test"
        - "!render"
        - "!^_[^_]"

# Input models

::: anta.input_models.routing.bgp

    options:
      show_root_heading: false
      show_root_toc_entry: false
      show_bases: false
      anta_hide_test_module_description: true
      merge_init_into_class: false
      show_labels: true
      filters:
        - "!^__init__"
        - "!^__str__"
        - "!AFI_SAFI_EOS_KEY"
        - "!eos_key"
        - "!BgpAfi"
