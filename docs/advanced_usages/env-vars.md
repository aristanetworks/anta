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
| `ANTA_HTTPX_TRUST_ENV` | `true` | AsyncEOSDevice | Configures the `trust_env` parameter for the underlying HTTPX client. When false, HTTPX ignores environment variables for proxy and SSL settings. See the [HTTPX documentation](https://www.python-httpx.org/environment_variables/) for details. |

---

## Example Usage

The examples below show common scenarios where environment variables can be used to adjust ANTA's behavior.

### Disabling proxy environment variable passthrough

```bash
export ANTA_HTTPX_TRUST_ENV=false
anta nrfu table
```

---
