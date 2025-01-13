---
anta_title: Retrieving Tests information
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

`anta get tests` commands help you discover available tests in ANTA.

### Command overview

```bash
Usage: anta get tests [OPTIONS]

  Show all builtin ANTA tests with an example output retrieved from each test
  documentation.

Options:
  --module TEXT  Filter tests by module name.  [default: anta.tests]
  --test TEXT    Filter by specific test name. If module is specified,
                 searches only within that module.
  --short        Display test names without their inputs.
  --count        Print only the number of tests found.
  --help         Show this message and exit.
```

> [!TIP]
> By default, `anta get tests` will retrieve all tests available in ANTA.

### Examples

#### Default usage

``` yaml title="anta get tests"
anta.tests.aaa:
  - VerifyAcctConsoleMethods:
      # Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x).
      methods:
        - local
        - none
        - logging
      types:
        - system
        - exec
        - commands
        - dot1x
  - VerifyAcctDefaultMethods:
      # Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x).
      methods:
        - local
        - none
        - logging
      types:
        - system
        - exec
        - commands
        - dot1x
[...]
```

#### Module usage

To retrieve all the tests from `anta.tests.stun`.

``` yaml title="anta get tests --module anta.tests.stun"
anta.tests.stun:
  - VerifyStunClient:
      # Verifies STUN client settings, including local IP/port and optionally public IP/port.
      stun_clients:
        - source_address: 172.18.3.2
          public_address: 172.18.3.21
          source_port: 4500
          public_port: 6006
        - source_address: 100.64.3.2
          public_address: 100.64.3.21
          source_port: 4500
          public_port: 6006
  - VerifyStunServer:
      # Verifies the STUN server status is enabled and running.
```

#### Test usage

``` yaml title="anta get tests --test VerifyTacacsSourceIntf"
anta.tests.aaa:
  - VerifyTacacsSourceIntf:
      # Verifies TACACS source-interface for a specified VRF.
      intf: Management0
      vrf: MGMT
```

> [!TIP]
> You can filter tests by providing a prefix - ANTA will return all tests that start with your specified string.

```yaml title="anta get tests --test VerifyTacacs"
anta.tests.aaa:
  - VerifyTacacsServerGroups:
      # Verifies if the provided TACACS server group(s) are configured.
      groups:
        - TACACS-GROUP1
        - TACACS-GROUP2
  - VerifyTacacsServers:
      # Verifies TACACS servers are configured for a specified VRF.
      servers:
        - 10.10.10.21
        - 10.10.10.22
      vrf: MGMT
  - VerifyTacacsSourceIntf:
      # Verifies TACACS source-interface for a specified VRF.
      intf: Management0
      vrf: MGMT
```

#### Count the tests

```bash title="anta get tests --count"
There are 155 tests available in `anta.tests`.
```
