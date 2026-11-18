---
title: ANTA Class Diagram
hide:
  - tags
tags:
  - API
  - Python
---

<!--
  ~ Copyright (c) 2025-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

<!-- Zensical 0.1.0 Markdown-export workaround: an icon inside a link makes
     the exporter drop the entire link, including its text. Keep the Pydantic
     icon outside the text link below. Recheck after upgrading Zensical. -->
!!! info
    The classes colored in pink :fontawesome-solid-square-full:{ .pydantic_pink } are :simple-pydantic:{ .pydantic_pink } [pydantic models](https://docs.pydantic.dev/latest/concepts/models/).
    The classes colored in green :fontawesome-solid-square-full:{ .dataclass_green } are dataclasses, annotated with `<<Dataclass>>`. Frozen dataclasses are marked with `<<Frozen Dataclass>>` instead.
<!-- Zensical 0.1.0 Markdown-export workaround: a hidden textarea leaks this
     duplicate zoom source into the export. An inert text/plain script preserves
     the raw Mermaid text for the zoom helper and is omitted from exports.
     Keep the normal Mermaid block below; recheck after upgrading Zensical. -->
<script type="text/plain" class="mermaid-zoom-source" data-title="ANTA Class Diagram">
--8<-- "api/class-diagram.mmd"
</script>

``` mermaid
--8<-- "api/class-diagram.mmd"
```
