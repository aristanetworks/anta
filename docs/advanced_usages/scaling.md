<!--
  ~ Copyright (c) 2023-2024 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 🚀 Scaling ANTA: A Comprehensive Guide

**Table of Contents:**

- [🚀 Scaling ANTA: A Comprehensive Guide](#-scaling-anta-a-comprehensive-guide)
  - [📖 Introduction](#-introduction)
  - [🔄 Single Process Optimization](#-single-process-optimization)
    - [Understanding ANTA's Asynchronous Nature](#understanding-antas-asynchronous-nature)
    - [Resource Management](#resource-management)
    - [Connection Management](#connection-management)
    - [Timeouts Configuration](#timeouts-configuration)
    - [Performance Tuning](#performance-tuning)
  - [🔀 Multi-Process Scaling](#-multi-process-scaling)
    - [Prerequisites](#prerequisites)
    - [Installation Requirements](#installation-requirements)
      - [Installing Required Tools](#installing-required-tools)
    - [Scaling Strategies](#scaling-strategies)
      - [Device-Based Parallelization](#device-based-parallelization)
      - [Tag-Based Parallelization](#tag-based-parallelization)
      - [Optimizing Catalog Distribution](#optimizing-catalog-distribution)
    - [Implementation](#implementation)
      - [Device-Based Implementation](#device-based-implementation)
      - [Tag-Based Implementation](#tag-based-implementation)
    - [Performance Considerations](#performance-considerations)
      - [Parallel Job Control](#parallel-job-control)
      - [JSON vs YAML](#json-vs-yaml)
    - [Results Management](#results-management)
  - [🎉 Conclusion](#-conclusion)
  - [📚 References](#-references)

## 📖 Introduction

!!! warning "Advanced Guide"
    This document covers advanced ANTA configuration and scaling strategies. If you need assistance with specific deployments or optimizations:

    - 📧 Contact your favorite Arista Systems Engineer
    - 💻 Open an issue on ANTA's [GitHub repository](https://github.com/aristanetworks/anta)
    - 🤝 Join the discussion in our community channels

    This guide also assumes you have a basic understanding of ANTA and are familiar with its core concepts. If you're new to ANTA, we recommend starting with the [ANTA Getting Started](../getting-started.md) before proceeding.

ANTA (Arista Network Test Automation) is continually evolving to meet the demands of large-scale network validation. As networks grow in size and complexity, the need for efficient, scalable testing becomes increasingly important. This guide explores comprehensive strategies for scaling ANTA to handle large network fabrics effectively.

We'll cover two main approaches:

1. 🔄 Single Process Optimization: Leveraging ANTA's built-in asynchronous capabilities with resource management
2. 🔀 Multi-Process Scaling: Running multiple ANTA instances in parallel (covered in [Part 2](#-multi-process-scaling))

For large fabrics (500+ devices), you may need to combine both approaches for optimal performance.

## 🔄 Single Process Optimization

### Understanding ANTA's Asynchronous Nature

ANTA uses Python's `asyncio` library for concurrent execution:

- 📦 Each test is a coroutine in the main event loop
- 🔄 Tests run concurrently, not in parallel
- ⚙️ The event loop manages all coroutines and network I/O

**Key Concept**: While `asyncio` provides excellent concurrency, there are practical limits to how many coroutines can be efficiently managed in a single event loop running on one CPU core. High coroutine counts increase event loop overhead, lead to frequent context switching, consume more memory, and may degrade performance.

### Resource Management

ANTA now provides several environment variables to control resource usage:

!!! note "Default Values"
    The values specified in the following examples are the actual default values used by ANTA. See the [Performance Tuning](#performance-tuning) section for guidance on adjusting these values.

1. **Test Concurrency**:

    ```bash
    export ANTA_MAX_CONCURRENCY=10000
    ```

    This limits the number of concurrent test coroutines to prevent event loop overload. ANTA will schedule coroutines up to this limit, then wait for some to complete before scheduling more.

2. **File Descriptors**:

    ```bash
    export ANTA_NOFILE=16384
    ```

    Sets the maximum number of open file descriptors for the ANTA process, usually for handling device connections. At startup, ANTA sets its process’s soft limit to the maximum allowed (up to `16384`). This adjustment is necessary because the soft limit is typically set to `1024`, while the hard limit is often higher (system-dependent). If ANTA’s hard limit is lower than the number of selected tests in ANTA, the process may request more file descriptors than the operating system allows, causing an error. In such cases, a WARNING is displayed at startup.

    To address this, consider increasing the hard limit for the user starting the ANTA process. You can check the current hard limit for a user by running the command `ulimit -n -H` in the terminal. To set a new limit, create the file `/etc/security/limits.d/10-anta.conf` with the following content:

    ```bash
    <user> hard nofile <value>
    ```

    Replace `<user>` with the username used to start the ANTA process, and `<value>` with the desired hard limit. The maximum value will depend on your system. After creating this file, log out of your current session and log back in for the changes to take effect.

### Connection Management

ANTA uses the `httpx` library as its underlying HTTP client for device connections. Each device has his own connection pool with a default maximum of `100` connections. On large fabrics, this can lead to a very high number of connections (n x 100), which may overwhelm the ANTA process. Connection pooling can be tuned via:

```bash
# Maximum number of allowable connections
export ANTA_MAX_CONNECTIONS=100

# Number of allowable keep-alive connections
export ANTA_MAX_KEEPALIVE_CONNECTIONS=20

# Time limit on idle keep-alive connections in seconds
export ANTA_KEEPALIVE_EXPIRY=5.0
```

**Best Practice**: For large fabrics, limiting connections (5-10 per device) has shown optimal performance in testing. `ANTA_MAX_KEEPALIVE_CONNECTIONS` should be lower than `ANTA_MAX_CONNECTIONS`. See [HTTPX documentation](https://www.python-httpx.org/advanced/resource-limits/) for more details.

### Timeouts Configuration

ANTA provides several environment variables to control `httpx` timeouts:

```bash
# Global timeout
export ANTA_TIMEOUT=30.0

# Maximum amount of time to wait until a socket connection to the requested host is established
export ANTA_CONNECT_TIMEOUT=30.0

# Maximum duration to wait for a chunk of data to be received (for example, a chunk of the response body)
export ANTA_READ_TIMEOUT=30.0

# Maximum duration to wait for a chunk of data to be sent (for example, a chunk of the request body)
export ANTA_WRITE_TIMEOUT=30.0

# Maximum duration to wait for acquiring a connection from the connection pool
export ANTA_POOL_TIMEOUT=30.0
```

If not set, these values default to the global `timeout` of ANTA, which is `30.0` seconds by default. The global timeout can also be set via the `--timeout` command-line option. See [HTTPX documentation](https://www.python-httpx.org/advanced/timeouts/) for more details.

### Performance Tuning

For optimal single-process performance, consider the following tuning parameters:

1. Adjust concurrency based on test count and system resources:

    ```bash
    # For 250 devices with 100 tests each (25,000 total tests)
    export ANTA_MAX_CONCURRENCY=25000
    ```

    Even though the default value is `10000`, it may not be optimal for your system. You can increase or decrease this value gradually to find the best setting for your environment.

2. Optimize connection pooling:

    ```bash
    export ANTA_MAX_CONNECTIONS=10
    export ANTA_MAX_KEEPALIVE_CONNECTIONS=5
    ```

    These values are a good starting point for large fabrics. Adjust them based on your fabric size and performance testing.

3. Increase timeouts for stability:

    ```bash
    export ANTA_TIMEOUT=3600.0
    ```

    This is **very** important for large fabrics. Increase the global timeout to prevent test failures due to timeouts. You shouldn't need to adjust the other timeout values unless you have specific requirements.

## 🔀 Multi-Process Scaling

When single-process optimization isn't enough, you can scale ANTA horizontally by running multiple instances in parallel. This approach is particularly useful for large fabrics with 500+ devices. This section will provide a few examples of how to achieve this using the common tool [`GNU Parallel`](https://www.gnu.org/software/parallel/).

By leveraging `GNU Parallel` and proper test organization, we can significantly reduce execution time and improve overall performance while maintaining accurate test results.

### Prerequisites

Before implementing multi-process scaling:

- 🏗️ Understand your fabric topology
- 🎯 Identify natural test boundaries (e.g., devices, PODs, roles, etc.)
- 📋 Plan your test catalog(s) accordingly
- 💻 Understand basic Linux command-line operations

### Installation Requirements

!!! info "System Requirements"
    The following procedures and examples were tested on **Ubuntu 22.04**, using `GNU Parallel` version `20241022` and `yq` version `v4.44.3`. Please refer the tool's documentation for specific installation instructions.

#### Installing Required Tools

1. Install `GNU Parallel` using the following commands:

    ```bash
    apt-get install parallel
    ```

2. Install `yq` using the following commands:

    ```bash
    wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq &&\
        chmod +x /usr/bin/yq
    ```

3. Confirm the installation by running:

    ```bash
    parallel --version
    yq --version
    ```

    You should see the version information for both tools if the installation was successful:

    ```bash
    (.dev) ~ parallel --version
    GNU parallel 20241022
    Copyright (C) 2007-2024 Ole Tange, http://ole.tange.dk and Free Software
    Foundation, Inc.
    License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>
    This is free software: you are free to change and redistribute it.
    GNU parallel comes with no warranty.

    Web site: https://www.gnu.org/software/parallel

    When using programs that use GNU Parallel to process data for publication
    please cite as described in 'parallel --citation'.

    (.dev) ~ yq --version
    yq (https://github.com/mikefarah/yq/) version v4.44.3
    ```

### Scaling Strategies

#### Device-Based Parallelization

In this approach, we run ANTA instances in parallel, with each instance handling a specific device. This strategy is effective when:

- Each device has unique test requirements, i.e., one catalog per device
- You want to maintain separate results per device
- You need fine-grained control over test execution

Example inventory structure:

```yaml
anta_inventory:
  hosts:
  - host: 172.20.20.101
    name: DC1-SPINE1
  - host: 172.20.20.102
    name: DC1-SPINE2
  # ... more devices
```

Example test catalog structure (one catalog per device):

```yaml
# DC1-SPINE2.yml
anta.tests.connectivity:
- VerifyLLDPNeighbors:
    neighbors:
    - neighbor_device: DC1-LEAF1A
      neighbor_port: Ethernet1
      port: Ethernet1
    result_overwrite:
      custom_field: 'Local: Ethernet1 - Remote: DC1-LEAF1A Ethernet1'

# DC1-SPINE1.yml
anta.tests.connectivity:
- VerifyLLDPNeighbors:
    neighbors:
    - neighbor_device: DC1-LEAF1A
      neighbor_port: Ethernet2
      port: Ethernet1
    result_overwrite:
      custom_field: 'Local: Ethernet1 - Remote: DC1-LEAF1A Ethernet2'
```

#### Tag-Based Parallelization

This approach runs parallel instances based on device tags, useful when:

- Devices in the same role share similar test requirements
- You want to test entire PODs or device groups simultaneously
- You need to organize tests by network function or location

Example inventory structure:

```yaml
---
anta_inventory:
  hosts:
  - host: 172.20.20.101
    name: DC1-SPINE1
    tags: ["SPINE", "DC1"]

  - host: 172.20.20.102
    name: DC1-SPINE2
    tags: ["SPINE", "DC1"]

  - host: 172.20.20.111
    name: DC1-LEAF1A
    tags: ["LEAF", "DC1"]

  - host: 172.20.20.112
    name: DC1-LEAF1B
    tags: ["LEAF", "DC1"]

  - host: 172.20.20.201
    name: DC2-SPINE1
    tags: ["SPINE", "DC2"]

  - host: 172.20.20.202
    name: DC2-SPINE2
    tags: ["SPINE", "DC2"]
  # ... more devices
```

Example test catalog structure (one catalog for all devices):

```yaml
anta.tests.vxlan:
  - VerifyVxlan1Interface:
      filters:
        tags: ["BL", "LEAF"]
  - VerifyVxlanConfigSanity:
      filters:
        tags: ["BL", "LEAF"]

anta.tests.routing:
  generic:
    - VerifyRoutingProtocolModel:
        model: multi-agent
        filters:
          tags: ["SPINE"]
```

#### Optimizing Catalog Distribution

For large fabrics, consider:

1. Creating separate catalogs per device type
2. Organizing catalogs by POD or datacenter
3. Using tag-based filtering within catalogs

Benefits:

- Reduced memory usage per ANTA instance
- Faster catalog processing
- More efficient test execution

### Implementation

#### Device-Based Implementation

1. Create the device-specific test runner BASH script (`nrfu.sh`):

    ```bash
    #!/bin/bash

    set -euo pipefail

    exec 2>&1

    usage() {
        echo "Usage: $0 <node-name> [<nrfu-reports-path>]"
        exit 1
    }

    ANTA_INVENTORY="anta_inventory.yml"
    TEST_CATALOGS_PATH="intended/test_catalogs"
    NODE_NAME=${1:-}
    NRFU_REPORT_PATH=${2:-nrfu_reports}


    if [[ -z "$NODE_NAME" ]]; then
        usage
    fi

    anta nrfu \
        -d "$NODE_NAME" \
        -i "$ANTA_INVENTORY" \
        -c "$TEST_CATALOGS_PATH/$NODE_NAME-catalog.yml" \
        json -o "$NRFU_REPORT_PATH/$NODE_NAME.json"
    ```

    Change `ANTA_INVENTORY` and `TEST_CATALOGS_PATH` to match your environment.

2. Create the parallel execution script (`run.sh`):

    ```bash
    #!/bin/bash

    mkdir -p nrfu_reports

    NODE_NAMES=$(yq '.anta_inventory.hosts[].name' < "anta_inventory.yml" | tr -d '"')

    parallel --tag './nrfu.sh {} nrfu_reports' ::: $NODE_NAMES || NRFU_STATUS=$?

    exit $NRFU_STATUS
    ```

    Also change `anta_inventory.yml` to match your inventory file specified in `ANTA_INVENTORY` of `nrfu.sh`.

3. Make both scripts executable:

    ```bash
    chmod +x nrfu.sh run.sh
    ```

4. Run the script:

    ```bash
    ./run.sh
    ```

5. The script will execute ANTA tests for each device in parallel, generating a JSON report for each device in the `nrfu_reports` directory.

#### Tag-Based Implementation

1. Create the tag-specific test runner (`nrfu-tag.sh`):

    ```bash
    #!/bin/bash
    set -euo pipefail

    exec 2>&1

    usage() {
        echo "Usage: $0 <tag-name> [<nrfu-reports-path>]"
        exit 1
    }

    ANTA_INVENTORY="anta_inventory.yml"
    ANTA_CATALOG="anta_catalog.yml"
    TAG_NAME=${1:-}
    NRFU_REPORT_PATH=${2:-nrfu_reports}

    if [[ -z "$TAG_NAME" ]]; then
        usage
    fi

    anta nrfu \
        --tags "$TAG_NAME" \
        -i "$ANTA_INVENTORY" \
        -c "$ANTA_CATALOG" \
        json -o "$NRFU_REPORT_PATH/${TAG_NAME}.json"
    ```

    Same as before, adjust `ANTA_INVENTORY`, `ANTA_CATALOG` to match your environment.

2. Create the parallel execution script (`run-tag.sh`):

    ```bash
    #!/bin/bash

    mkdir -p nrfu_reports

    TAGS=$(yq -r '.. | select(.filters?) | .filters.tags[]' < "anta_catalog.yml" | sort -u)

    parallel --tag './nrfu_tag.sh {} nrfu_reports' ::: $TAGS || NRFU_STATUS=$?

    exit $NRFU_STATUS
    ```

    Change `anta_catalog.yml` to match your catalog file specified in `ANTA_CATALOG` of `nrfu-tag.sh`.

3. Make both scripts executable:

    ```bash
    chmod +x nrfu-tag.sh run-tag.sh
    ```

4. Run the script:

    ```bash
    ./run-tag.sh
    ```

5. The script will execute ANTA tests for each tag in parallel, generating a JSON report for each tag in the `nrfu_reports` directory.

### Performance Considerations

#### Parallel Job Control

The `-j` option in `GNU Parallel` controls the number of concurrent jobs. Consider these factors when setting the job limit:

1. **Available CPU cores**:

     - Recommend: jobs = number of cores - 1
     - Example: For 8 cores, use `-j7`

2. **Memory requirements**:

     - Each ANTA instance requires memory
     - Monitor system resources during execution using `htop` or similar tools

#### JSON vs YAML

When working with large catalogs and inventories, using JSON format instead of YAML can provide better performance as ANTA loads JSON files more efficiently. If you choose to use JSON:

- Convert your YAML files to JSON (you can use `yq` for this)
- Modify the scripts to use `jq` instead of `yq`:

  ```bash
  # For device-based implementation
  NODE_NAMES=$(jq -r '.anta_inventory.hosts[].name' < "anta_inventory.json")

  # For tag-based implementation
  TAGS=$(jq -r '.. | select(.filters?) | .filters.tags[]' < "anta_catalog.json" | sort -u)
  ```

  Example of converting YAML to JSON:

  ```bash
  yq -o=json eval 'anta_inventory.yaml' > anta_inventory.json
  yq -o=json eval 'anta_catalog.yaml' > anta_catalog.json
  ```

### Results Management

ANTA can output results in various formats:

1. JSON format (default in our scripts):

    ```bash
    anta nrfu -d <device> -i <inventory> -c <catalog> json -o <output-file>
    ```

2. Markdown format:

    ```bash
    anta nrfu -d <device> -i <inventory> -c <catalog> md-report --md-output <output-file>
    ```

    Please refer to the [ANTA CLI documentation](https://anta.arista.com/stable/cli/nrfu/) for more information on result output formats.

    !!! note "Output Formats"
        The scripts provided in this guide output JSON files for each device or tag. You can modify them to output in other formats as needed.

3. Optional: You can merge the JSON results and generate a JUnit report using the following Python script (requires `junitparser`):

    ```python
    from pathlib import Path

    from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Error, Failure
    import json

    xml = JUnitXml()

    for report_path in Path("nrfu_reports").glob("*.json"):
        node_name = report_path.stem
        test_case_results = {}

        print(f"Processing {report_path}")
        with open(report_path, mode="r", encoding="utf-8") as fd:
            nrfu_report = json.load(fd)

        for report_idx, report in enumerate(nrfu_report):
            report_test = report["test"]
            test_case = test_case_results.setdefault(report_test, [])

            report_result = report["result"]
            if report_result == "success":
                continue

            report_message = ",".join(report["messages"])

            result_cls = {
                "error": Error,
                "skipped": Skipped,
                "failure": Failure,
            }.get(report_result)
            test_case.append(result_cls(message=report_message))

        # Add suite to JunitXml
        node_suite = TestSuite(node_name)
        test_cases = []
        n_tests = 0
        for test_name, test_results in test_case_results.items():
            test_case = TestCase(name=test_name, classname=f"{node_name}")
            test_case.result = test_results
            n_tests += len(test_results)
            test_cases.append(test_case)
        node_suite.add_testcases(test_cases)
        xml.add_testsuite(node_suite)

    xml.write("nrfu.xml", pretty=True)
    ```

    !!! tip "CI/CD Integration"
        This report format can be used with CI/CD tools like Jenkins, GitLab, or GitHub Actions.

## 🎉 Conclusion

By implementing these scaling strategies, you can efficiently run ANTA tests on large network fabrics. The combination of parallel execution, optimized catalogs, and proper resource management ensures fast and reliable network validation.

Remember to:

- ✅ Choose the appropriate parallelization strategy
- 📋 Optimize catalog organization
- 📊 Monitor system resources
- ⚡ Adjust parallel job limits based on your environment

!!! tip "Need Help?"
    Performance tuning can be complex and highly dependent on your specific deployment. Don't hesitate to:

    - 📞 Reach out to your Arista SE for guidance
    - 📝 Document your specific use case on [GitHub](https://github.com/aristanetworks/anta)
    - 🔍 Share your findings with the community

## 📚 References

- **Python AsyncIO**
  - [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
  - [AsyncIO Event Loop](https://docs.python.org/3/library/asyncio-eventloop.html)
  - [AsyncIO Tasks and Coroutines](https://docs.python.org/3/library/asyncio-task.html)

- **HTTPX**
  - [HTTPX Documentation](https://www.python-httpx.org/)
  - [Timeouts](https://www.python-httpx.org/advanced/timeouts/)
  - [Resource Limits](https://www.python-httpx.org/advanced/resource-limits/)

- **GNU Parallel**
  - [GNU Parallel Documentation](https://www.gnu.org/software/parallel/)
  - [GNU Parallel Tutorial](https://www.gnu.org/software/parallel/parallel_tutorial.html)

- **JSON and YAML Processing**
  - [jq Manual](https://jqlang.github.io/jq/manual/)
  - [jq GitHub Repository](https://github.com/jqlang/jq)
  - [yq Documentation](https://mikefarah.gitbook.io/yq/)
  - [yq GitHub Repository](https://github.com/mikefarah/yq/)

- **JUnit/xUnit Result XML Parser**
  - [junitparser Documentation](https://junitparser.readthedocs.io/en/latest/)
  - [junitparser GitHub Repository](https://github.com/weiwei/junitparser)
