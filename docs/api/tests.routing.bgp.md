<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# ANTA catalog for BGP tests

!!! warning "Deprecation Notice"
    As part of our ongoing effort to improve the ANTA catalog and align it with best practices, we are announcing the deprecation of certain BGP tests along with a specific decorator. These will be removed in a future major release of ANTA.

_What is being deprecated?_

- __Tests__: The following BGP tests in the ANTA catalog are marked for deprecation.

```yaml
anta.tests.routing:
  bgp:
    - VerifyBGPIPv4UnicastState:
    - VerifyBGPIPv4UnicastCount:
    - VerifyBGPIPv6UnicastState:
    - VerifyBGPEVPNState:
    - VerifyBGPEVPNCount:
    - VerifyBGPRTCState:
    - VerifyBGPRTCCount:
```

- __Decorator__: The `check_bgp_family_enable` decorator is also being deprecated as it is no longer needed with the new refactored BGP tests.

_What should you do?_

We strongly recommend transitioning to the new set of BGP tests that have been introduced to replace the deprecated ones. Please refer to each test documentation on this page below.

```yaml
anta.tests.routing:
  bgp:
    - VerifyBGPPeerCount:
    - VerifyBGPPeersHealth:
    - VerifyBGPSpecificPeers:
```
___

::: anta.tests.routing.bgp
    options:
      show_root_heading: false
      show_root_toc_entry: false
      merge_init_into_class: false
