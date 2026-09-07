---
title: Test anta-psirt in the lab
hide:
  - tags
tags:
  - PSIRT
  - Security
---

<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

The `anta psirt` lab is an interactive, cloud-based environment sponsored by
Arista. It is designed for testing and demonstrating the security
advisory reporting capabilities introduced with the ANTA v1.10 CLI. Use it to
try the [`anta psirt`](usage.md) command against preconfigured devices without
setting up a local environment.

## Lab environment

The lab includes four cEOS-lab devices running EOS 4.33.0F and an ANTA
release with `anta psirt` command support.

![ANTA PSIRT lab topology](../imgs/anta-psirt.png){ loading=lazy width="713" }

The lab may cover only a limited number of security advisories available in the installed ANTA release and enabled by the lab configuration.
The ANTA release installed in the lab may change over time without a notice. Please verify the lab before running a demo.

## Launch the lab

To get started, sign in at [labs.arista.com](https://labs.arista.com/) and
confirm that you can access the service. Then launch the lab:

[Start the ANTA PSIRT lab](https://labs.arista.com/launch?lab_type=anta-psirt&origin=tech-lib){ .md-button .md-button--primary target="_blank" rel="noopener" }

Once the lab is ready, follow the walkthrough provided in the lab environment.

!!! warning "One lab per click"
    Every click creates a new lab that runs for eight hours. If you launch one
    by mistake, or finish before it expires, use **Terminate** to stop it.

!!! note "Lab access"
    Due to infrastructure costs and security requirements, Arista labs are available only to registered Arista customers.
    If you do not have the required access, contact your Arista account team.
