---
title: ANTA Device API
hide:
  - tags
tags:
  - API
  - Inventory
  - Python
---

<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

::: anta.device.DeviceVersion
    options:
      filters: ["!^_", "^\\x5f\\x5fstr\\x5f\\x5f$"]

::: anta.device.AntaDevice
    options:
      filters: ["!^_", "_collect"]

<!-- _collect must be last to be kept -->

::: anta.device.AsyncEOSDevice
    options:
      filters: ["!^_", "_collect"]
