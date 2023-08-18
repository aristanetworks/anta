<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Test Result model

## UML Diagram

![](../imgs/uml/anta.result_manager.models.TestResult.jpeg)

### ::: anta.result_manager.models.TestResult
    options:
        filters: ["!^_[^_]", "!__str__"]

### ::: anta.result_manager.models.ListResult
      options:
        filters: ["!^_[^_]", "!^__(len|getitem|iter)__",]
