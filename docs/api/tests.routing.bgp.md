---
anta_title: ANTA catalog for BGP tests
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

!!! info "BGP Test Compatibility Note"
    ANTA BGP tests are designed for the `multi-agent` routing protocol model. Starting from EOS 4.30.1F, `service routing protocols models` is set to `multi-agent` by default, and from EOS 4.32.0F it becomes the only supported model.

    The following tests are available for devices using the legacy `ribd` model on earlier EOS versions:

      - `VerifyBGPPeerSessionRibd`
      - `VerifyBGPPeersHealthRibd`

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
