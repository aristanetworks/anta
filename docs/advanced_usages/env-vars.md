---
title: Environment Variables
hide:
  - tags
tags:
  - Configuration
---

<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->
---

ANTA exposes several environment variables that allow you to configure its behavior. These variables are automatically read during the initialization and preparation phases, ensuring the environment is configured correctly before any tests are executed.

## Summary

| Variable | Default | Consumed By | Description |
| -------- | ------- | ----------- | ----------- |
| `ANTA_HTTPX_TRUST_ENV` | `true` | AsyncEOSDevice | Configures the `trust_env` parameter for the underlying httpx2 client. When false, httpx2 ignores environment variables for proxy and SSL settings. See the [httpx2 documentation](https://httpx2.pydantic.dev/environment_variables/) for details. |

---

## Example Usage

The examples below show common scenarios where environment variables can be used to adjust ANTA's behavior.

### Disabling proxy environment variable passthrough

```bash
export ANTA_HTTPX_TRUST_ENV=false
anta nrfu table
```

---
