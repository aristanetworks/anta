---
title: ANTA Tests for device configuration
hide:
  - tags
tags:
  - API
  - Tests
  - Configuration
---

<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
# Tests

::: anta.tests.configuration

    options:
      extra:
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

## Input models

::: anta.input_models.configuration

    options:
      extra:
          anta_hide_test_module_description: true
      filters:
        - "!^__str__"
        - "!^build_description$"
        - "!^matches$"
        - "!^validate_entry$"
        - "!^evaluate$"
      merge_init_into_class: false
      show_bases: false
      show_labels: true
      show_root_heading: false
      show_root_toc_entry: false
      show_symbol_type_heading: false
      show_symbol_type_toc: false
