---
anta_title: Experimental Features
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

ANTA offers experimental features that may improve performance or add capabilities, but haven't been thoroughly tested in all environments. These features might require additional dependencies and special configuration.

## AIOHTTP Transport for HTTPX

### Background

By default, ANTA uses [HTTPX](https://www.python-httpx.org/) with its standard [HTTPCore](https://www.encode.io/httpcore/) backend for API communications. HTTPX is a high-level HTTP client that doesn't interact with I/O directly but relies on a backend library for I/O operations.

While the default HTTPCore backend works well for most scenarios, it can experience performance issues when handling many concurrent connections, potentially causing slowdowns and high CPU usage at scale.

You can refer to the following [GitHub issue](https://github.com/encode/httpx/issues/3215) for more information.

### Using AIOHTTP Transport

As an experimental alternative, ANTA supports using [AIOHTTP](https://docs.aiohttp.org/en/stable/) as the transport layer for HTTPX. This can improve performance for high-scale deployments by delegating connection pooling and socket-level message to AIOHTTP while maintaining HTTPX's API for higher-level HTTP operations.

### Installation

To use this experimental feature, install ANTA with experimental dependencies:

```bash
pip install 'anta[experimental]'
```

### Activation

#### With ANTA CLI

Set the `ANTA_HTTPX_TRANSPORT` environment variable to `aiohttp`:

```bash
ANTA_HTTPX_TRANSPORT=aiohttp anta nrfu table
```

#### As a Python Library

When using ANTA as a library, specify the transport when initializing the `AsyncEOSDevice` object:

```python
from anta.device import AsyncEOSDevice

device = AsyncEOSDevice(
    host="192.168.1.1",
    username="admin",
    password="admin",
    httpx_transport="aiohttp", # Use aiohttp transport
)
```

### Limitations and Considerations

- This feature is experimental and not fully tested in all environments
- A warning will be displayed when using this transport to indicate its experimental status
- If the required dependencies aren't installed but `aiohttp` transport is requested, ANTA will automatically fall back to the default `httpcore` transport with an appropriate error message
- Performance improvements are primarily noticeable in scenarios with many concurrent connections (many devices or tests)

### Feedback

If you encounter any issues of have feedback about the `aiohttp` transport, please open an issue on our [GitHub repository](https://github.com/aristanetworks/anta/issues).
