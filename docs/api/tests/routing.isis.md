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
      anta_hide_test_module_description: true
      filters:
        - "!test"
        - "!render"
        - "!^_[^_]"
      merge_init_into_class: false
      show_bases: false
      show_labels: true
      show_root_heading: false
      show_root_toc_entry: false
      show_symbol_type_heading: false
      show_symbol_type_toc: false

# Input models

::: anta.input_models.routing.isis

    options:
      anta_hide_test_module_description: true
      filters:
        - "!^__init__"
        - "!^__str__"
      merge_init_into_class: false
      show_bases: false
      show_labels: true
      show_root_heading: false
      show_root_toc_entry: false
      show_symbol_type_heading: false
      show_symbol_type_toc: false