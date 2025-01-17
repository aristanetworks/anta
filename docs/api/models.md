<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Test definition

![AntaTest UML model](../imgs/uml/anta.models.AntaTest.jpeg)

## ::: anta.models.AntaTest

    options:
        filters: ["!^_[^_]", "!__init_subclass__", "!update_progress"]

# Command definition

![AntaCommand UML model](../imgs/uml/anta.models.AntaCommand.jpeg)

## ::: anta.models.AntaCommand

!!! warning
    CLI commands are protected to avoid execution of critical commands such as `reload` or `write erase`.

      - Reload command: `^reload\s*\w*`
      - Configure mode: `^conf\w*\s*(terminal|session)*`
      - Write: `^wr\w*\s*\w+`

# Template definition

![AntaTemplate UML model](../imgs/uml/anta.models.AntaTemplate.jpeg)

## ::: anta.models.AntaTemplate
