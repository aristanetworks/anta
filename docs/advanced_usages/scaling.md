---
anta_title: "🚀 Scaling ANTA: A Comprehensive Guide"
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# 📖 Introduction

!!! warning "Advanced Guide"
    This document covers advanced ANTA configuration and scaling strategies. If you need assistance with specific deployments or optimizations:

    - 📧 Contact your favorite Arista Systems Engineer
    - 💻 Open an issue or a discussion on ANTA [GitHub repository](https://github.com/aristanetworks/anta)
    - 🤝 Join the discussion in our community channels

    This guide also assumes you have a basic understanding of ANTA and are familiar with its core concepts. If you're new to ANTA, we recommend starting with the [ANTA Getting Started](../getting-started.md) before proceeding.

**ANTA** (Arista Network Test Automation) is continually evolving to meet the demands of large-scale network validation. As networks grow in size and complexity, the need for efficient, scalable testing becomes increasingly important. This guide explores comprehensive strategies for scaling ANTA to handle large network fabrics effectively.

# 🔄 Core Optimizations

## Understanding ANTA's Asynchronous Nature

ANTA uses Python `asyncio` library for concurrent execution:

- 📦 Each test is a coroutine in the main event loop
- ⚡ Tests run concurrently, not in parallel
- ⚙️ The event loop manages all coroutines and network I/O

!!! important "Key Concept"
    While `asyncio` provides excellent concurrency, there are practical limits to how many coroutines can be efficiently managed in a single event loop running on one CPU core. High coroutine counts increase event loop overhead, lead to frequent context switching, consume more memory, and may degrade performance.

## Resource Management

This section describes the environment variables to control resource usage provided by ANTA.

!!! note "Default Values"
    The values specified in the following examples are the actual default values used by ANTA. See the [Performance Tuning](#performance-tuning) section for guidance on adjusting these values.

### **Test Concurrency**

ANTA limits the number of concurrent test coroutines to prevent event loop overload. The runner schedules coroutines up to this limit, then waits for some to complete before scheduling more. The following variable can be used to tune this limit:

```bash
export ANTA_MAX_CONCURRENCY=10000
```

### **File Descriptors**

ANTA manages the number of open file descriptors, which are primarily used for handling device connections. At startup, on POSIX systems (Linux/macOS), ANTA attempts to set its process's soft limit to the maximum allowed value (up to 16384). This adjustment is necessary because the default soft limit (typically 1024) may be too low for large-scale testing, while the system's hard limit is often higher. If the system's hard limit is lower than the number of file descriptors ANTA needs, you'll see a warning at startup. The following environment variable controls this setting:

```bash
export ANTA_NOFILE=16384
```

On Windows (non-POSIX systems), ANTA cannot adjust file descriptor limits. In these cases, ANTA will:

- Use Python `sys.maxsize` as the limit
- Display a warning message: "Running on a non-POSIX system, cannot adjust the maximum number of file descriptors"
- Continue operation with system defaults

For POSIX systems, if you need to increase the hard limit:

- Check your current hard limit:

```bash
ulimit -n -H
```

- Set a new limit by creating `/etc/security/limits.d/10-anta.conf`:

```bash
<user> hard nofile <value>
```

Replace `<user>` with the username running ANTA, and `<value>` with your desired limit (system-dependent).

- Log out and back in for changes to take effect.

## Connection Management

For [`AsyncEosDevice`](../api/device.md#async-eos-device-class) implementations (default in ANTA), ANTA uses the [`httpx`](https://www.python-httpx.org/) library as its underlying HTTP client for device connections. Each device has his own connection pool with a default maximum of `100` connections. On large fabrics, this can lead to a very high number of connections (n x 100), which may overwhelm the ANTA process. Note that custom `AntaDevice` subclasses might implement different HTTP settings. For `AsyncEosDevice`, connection pooling can be tuned via the following environment variables. See [HTTPX documentation](https://www.python-httpx.org/advanced/resource-limits/) for more details.

```bash
# Maximum number of allowable connections
export ANTA_MAX_CONNECTIONS=100

# Number of allowable keep-alive connections
export ANTA_MAX_KEEPALIVE_CONNECTIONS=20

# Time limit on idle keep-alive connections in seconds
export ANTA_KEEPALIVE_EXPIRY=5.0
```

!!! warning "Variable relationships"
    The value of `ANTA_MAX_KEEPALIVE_CONNECTIONS` should be lower than `ANTA_MAX_CONNECTIONS`.

## Timeouts Configuration

ANTA provides several environment variables to control `httpx` timeouts. If not set, these values default to the default global timeout value of ANTA (30.0 seconds). The global timeout can also be set via the `--timeout` command-line option. See [HTTPX documentation](https://www.python-httpx.org/advanced/timeouts/) for more details.

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

## Performance Tuning

For optimal performance on large fabrics, consider the following tuning parameters:

1. Increase timeouts for stability:

    ```bash
    export ANTA_CONNECT_TIMEOUT=60.0
    export ANTA_READ_TIMEOUT=300.0
    export ANTA_WRITE_TIMEOUT=60.0
    export ANTA_POOL_TIMEOUT=None
    ```

    This is **very** important for large fabrics. Setting appropriate timeouts for each operation type prevents test failures while maintaining proper error detection. The `ANTA_POOL_TIMEOUT=None` setting is crucial for large-scale deployments because:

      - ANTA launches multiple test coroutines simultaneously (up to `ANTA_MAX_CONCURRENCY`)
      - With thousands of tests, not all can acquire a connection immediately
      - The connection pool queues requests when all connections are in use
      - Without `ANTA_POOL_TIMEOUT=None`, requests might fail if they can't get a connection within the default 30-second global timeout
      - Setting it to `None` allows the connection pool to manage request queuing naturally

2. Adjust concurrency based on test count and system resources:

    ```bash
    # For 250 devices with 100 tests each (25,000 total tests)
    export ANTA_MAX_CONCURRENCY=25000
    ```

    Even though the default value is `10000`, it may not be optimal for your system. The optimal value depends on your CPU usage, memory consumption, and total execution time. Start with the default and adjust in increments while monitoring these metrics to find the best balance for your environment.

3. Optimize connection pooling:

    ```bash
    export ANTA_MAX_CONNECTIONS=10
    export ANTA_MAX_KEEPALIVE_CONNECTIONS=5
    ```

    These values are a good starting point for large fabrics. Adjust them based on your fabric size and performance testing.

4. Consider JSON over YAML for better performance:

    - JSON files load more efficiently than YAML in Python
    - Convert large YAML files to JSON (you can use tools like `jq` or `yq`)

        ```bash
        yq -o=json eval 'inventory.yaml' > inventory.json
        yq -o=json eval 'catalog.yaml' > catalog.json
        ```

    - Particularly beneficial for large inventories and test catalogs

# 🔀 Distributed Testing

While ANTA is designed to work efficiently as a single process, there may be scnarios where running multiple instances of ANTA is beneficial.

## Possible Use Cases

- **Distributed Testing**: Running ANTA instances on different machines to test separate parts of your network (e.g., data centers, regions)
- **Parallel Execution**: Using tools like `GNU Parallel` to run multiple ANTA instances targeting different device groups (e.g., spines, leafs)
- **Independent Testing**: Running separate ANTA instances for different testing purposes (e.g., connectivity tests vs. routing tests)

# 🎉 Conclusion

By implementing these scaling strategies, you can efficiently run ANTA tests on large network fabrics. The combination of optimized resource management, proper tuning, and thoughtful organization ensures fast and reliable network validation.

Remember to:

- ✅ Optimize resource usage through environment variables
- 📋 Consider file format performance impacts
- 📊 Choose appropriate output formats for your needs
- ⚡ Monitor and adjust based on your specific environment

!!! tip "Need Help?"
    Performance tuning can be complex and highly dependent on your specific deployment. See the warning "Advanced Guide" at the beginning of this document for assistance options.

# 📚 Additional Documentation

**Python AsyncIO**:

- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [AsyncIO Event Loop](https://docs.python.org/3/library/asyncio-eventloop.html)
- [AsyncIO Tasks and Coroutines](https://docs.python.org/3/library/asyncio-task.html)

**HTTPX**:

- [HTTPX Documentation](https://www.python-httpx.org/)
- [Timeouts](https://www.python-httpx.org/advanced/timeouts/)
- [Resource Limits](https://www.python-httpx.org/advanced/resource-limits/)

**GNU Parallel**:

- [GNU Parallel Documentation](https://www.gnu.org/software/parallel/)
- [GNU Parallel Tutorial](https://www.gnu.org/software/parallel/parallel_tutorial.html)

**JSON and YAML Processing**:

- [jq Manual](https://jqlang.github.io/jq/manual/)
- [jq GitHub Repository](https://github.com/jqlang/jq)
- [yq Documentation](https://mikefarah.gitbook.io/yq/)
- [yq GitHub Repository](https://github.com/mikefarah/yq/)
