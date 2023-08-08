# Test Result model

## UML Diagram

![](../imgs/uml/anta.result_manager.models.TestResult.jpeg)

### ::: anta.result_manager.models.TestResult
    options:
        filters: ["!^_[^_]", "!__str__"]

### ::: anta.result_manager.models.ListResult
      options:
        filters: ["!^_[^_]", "!^__(len|getitem|iter)__",]
