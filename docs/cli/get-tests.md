---
anta_title: Retrieving Tests information
---
<!--
  ~ Copyright (c) 2023-2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

## `anta get tests`

`anta get tests` commands help you discover the available tests in ANTA.

### Command overview

```bash
--8<-- "anta_get_tests_help.txt"
```

> [!TIP]
> By default, `anta get tests` retrieves all the tests available in ANTA.

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

#### Filtering using `--module`

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

#### Filtering using `--test`

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

## `anta get commands`

`anta get commands` returns the EOS commands used by the targeted tests, if no filter is provided, the targeted tests are all the built-in ANTA tests.

### Command overview

```bash
--8<-- "anta_get_commands_help.txt"
```

> [!TIP]
> By default, `anta get commands` returns the commands from every tests builtin in ANTA.

### Examples

#### Default usage

``` yaml title="anta get commands"
anta.tests.aaa:
  - VerifyAcctConsoleMethods:
    - show aaa methods accounting
  - VerifyAcctDefaultMethods:
    - show aaa methods accounting
  - VerifyAuthenMethods:
    - show aaa methods authentication
  - VerifyAuthzMethods:
    - show aaa methods authorization
  - VerifyTacacsServerGroups:
    - show tacacs
  - VerifyTacacsServers:
    - show tacacs
  - VerifyTacacsSourceIntf:
    - show tacacs
anta.tests.avt:
  - VerifyAVTPathHealth:
    - show adaptive-virtual-topology path
  - VerifyAVTRole:
    - show adaptive-virtual-topology path
  - VerifyAVTSpecificPath:
    - show adaptive-virtual-topology path
[...]
```

#### Filtering using `--module`

To retrieve all the commands from the tests in `anta.tests.stun`.

``` yaml title="anta get commands --module anta.tests.stun"
anta.tests.stun:
  - VerifyStunClient:
    - show stun client translations {source_address} {source_port}
  - VerifyStunClientTranslation:
    - show stun client translations {source_address} {source_port}
  - VerifyStunServer:
    - show stun server status
```

#### Filtering using `--test`

``` yaml title="anta get commands --test VerifyBGPExchangedRoutes"
anta.tests.routing.bgp:
  - VerifyBGPExchangedRoutes:
    - show bgp neighbors {peer} advertised-routes vrf {vrf}
    - show bgp neighbors {peer} routes vrf {vrf}
      vrf: MGMT
```

> [!TIP]
> You can filter tests by providing a prefix - ANTA will return all tests that start with your specified string.

```yaml title="anta get tests --test VerifyTacacs"
anta.tests.aaa:
  - VerifyTacacsServerGroups:
    - show tacacs
  - VerifyTacacsServers:
    - show tacacs
  - VerifyTacacsSourceIntf:
    - show tacacs
```

#### Filtering using `--catalog`

To retrieve all the commands from the tests in a catalog:

``` yaml title="anta get commands --catalog my-catalog.yml"
anta.tests.interfaces:
  - VerifyL3MTU:
    - show interfaces
anta.tests.mlag:
  - VerifyMlagStatus:
    - show mlag
anta.tests.system:
  - VerifyAgentLogs:
    - show agent logs crash
  - VerifyCPUUtilization:
    - show processes top once
  - VerifyCoredump:
    - show system coredump
  - VerifyFileSystemUtilization:
    - bash timeout 10 df -h
  - VerifyMemoryUtilization:
    - show version
  - VerifyNTP:
    - show ntp status
  - VerifyReloadCause:
    - show reload cause
  - VerifyUptime:
    - show uptime
```

#### Output using `--unique`

Using the `--unique` flag will output only the list of unique commands that will be run which can be useful to configure a AAA system.

For instance with the previous catalog, the output would be:

``` yaml title="anta get commands --catalog my-catalog.yml --unique"
show processes top once
bash timeout 10 df -h
show system coredump
show agent logs crash
show interfaces
show uptime
show ntp status
show version
show reload cause
show mlag
```
