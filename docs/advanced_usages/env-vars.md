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
| `ANTA_HTTPX_TRUST_ENV` | `true` | AsyncEOSDevice | Configures the `trust_env` parameter for the underlying HTTPX client. When false, HTTPX ignores environment variables for proxy and SSL settings. See the [HTTPX documentation](https://www.python-httpx.org/environment_variables/) for details. |
| `ANTA_SSL_CIPHERS` | unset | AsyncEOSDevice | OpenSSL cipher list used by HTTPS eAPI connections without explicit per-device `ssl_params`. Custom ciphers may reduce TLS security. |
| `ANTA_NOFILE` | `16384` | ANTA runner | Maximum number of open file descriptors for the ANTA process. The soft limit is raised to this value but never above the system hard limit. Ignored on non-POSIX systems such as Windows. |
| `ANTA_MAX_CONCURRENCY` | `50000` | ANTA runner | Maximum number of tests that can run concurrently in the event loop. See the [FAQ](../faq.md) for guidance on tuning this value. |

## CLI options

Most `anta` CLI options can also be set with an environment variable. The command line value takes precedence over the environment variable. The CLI help (`--help`) displays the variable name next to each option.

| Variable | CLI option | Default | Description |
| -------- | ---------- | ------- | ----------- |
| `ANTA_USERNAME` | `--username`, `-u` | none | Username to connect to EOS. |
| `ANTA_PASSWORD` | `--password`, `-p` | none | Password to connect to EOS. Can be prompted with `--prompt` instead. |
| `ANTA_ENABLE_PASSWORD` | `--enable-password` | none | Password to access EOS Privileged EXEC mode. Requires `--enable`. |
| `ANTA_ENABLE` | `--enable` | `false` | Try to access EOS Privileged EXEC mode before sending a command to the device. |
| `ANTA_PROMPT` | `--prompt`, `-P` | `false` | Prompt for passwords if they are not provided. |
| `ANTA_TIMEOUT` | `--timeout` | `30.0` | Global API timeout in seconds, used for all devices. |
| `ANTA_INSECURE` | `--insecure` | `false` | Disable SSH host key validation. |
| `ANTA_DISABLE_CACHE` | `--disable-cache` | `false` | Disable the command cache globally. |
| `ANTA_USE_SESSION_AUTH` | `--use-session-auth` / `--no-session-auth` | unset | Enable or explicitly disable eAPI session authentication globally. When unset, the per-device inventory values apply. |
| `ANTA_INVENTORY` | `--inventory`, `-i` | none | Path to the inventory file. |
| `ANTA_INVENTORY_FORMAT` | `--inventory-format` | `yaml` | Format of the inventory file, either `yaml` or `json`. |
| `ANTA_CATALOG` | `--catalog`, `-c` | none | Path to the test catalog file. |
| `ANTA_CATALOG_FORMAT` | `--catalog-format` | `yaml` | Format of the catalog file, either `yaml` or `json`. |
| `ANTA_TAGS` | `--tags` | none | Comma-separated list of tags used to filter devices or tests, for example `tag1,tag2,tag3`. |
| `ANTA_DISCONNECT_INVENTORY` | `--disconnect` / `--no-disconnect` | `true` | Disconnect the inventory devices once the `anta nrfu` run is complete. |

!!! warning
    Avoid exporting `ANTA_PASSWORD` and `ANTA_ENABLE_PASSWORD` in shared shells or committing them to scripts. Prefer `--prompt` or a secrets manager when possible.

---

## Example Usage

The examples below show common scenarios where environment variables can be used to adjust ANTA's behavior.

### Disabling proxy environment variable passthrough

```bash
export ANTA_HTTPX_TRUST_ENV=false
anta nrfu table
```

### Configuring SSL ciphers globally

```bash
export ANTA_SSL_CIPHERS="AES256-SHA:DHE-RSA-AES256-SHA:AES128-SHA:DHE-RSA-AES128-SHA"
anta nrfu table
```

`ANTA_SSL_CIPHERS` applies to every HTTPS inventory entry that does not define `ssl_params`. Prefer upgrading EOS or configuring an EOS server-side SSL profile instead of enabling legacy ciphers when possible.

### Tuning the runner for a large fabric

```bash
export ANTA_NOFILE=32768
export ANTA_MAX_CONCURRENCY=20000
anta nrfu table
```

### Setting CLI defaults

```bash
export ANTA_USERNAME=admin
export ANTA_INVENTORY=inventory.yml
export ANTA_CATALOG=catalog.yml
anta nrfu --prompt table
```

---
