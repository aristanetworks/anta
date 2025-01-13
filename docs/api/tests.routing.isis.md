---
anta_title: ANTA catalog for IS-IS tests
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Tests

::: anta.tests.routing.isis

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

::: anta.input_models.routing.isis

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
