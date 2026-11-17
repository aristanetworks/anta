# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared ``show dot1x all`` outputs captured on a DCS-7050SX3-48YC12 running EOS 4.32.0F."""

from __future__ import annotations


def dot1x_interface(port_control: str) -> dict[str, object]:
    """Return one ``show dot1x all`` authenticator interface entry."""
    return {
        "portControl": port_control,
        "forceAuthPhone": False,
        "hostMode": "multiHost",
        "sessionReplaceEnabled": False,
        "quietPeriod": 60.0,
        "txPeriod": 5.0,
        "maxReauthReq": 2,
        "reauthTimeoutIgnore": False,
        "authFailVlan": 0,
        "unauthorizedAccessVlanEgress": False,
        "unauthorizedNativeVlanEgress": False,
        "eapolDisabled": False,
        "mbaEnabled": False,
        "mbaTimeout": 180.0,
        "mbaFallback": False,
        "mbaHostMode": False,
        "mbaAuthAlways": False,
    }


def dot1x_all(*, system_auth_control: object = True, interfaces: object = None) -> dict[str, object]:
    """Return ``show dot1x all`` with selected global and interface values."""
    return {
        "dynAuth": False,
        "lldpBypass": False,
        "bpduBypass": False,
        "sendIdentityReqLoggedOffMac": False,
        "sendIdentityReqNewMac": False,
        "sessionMoveEapol": False,
        "sessionReplaceDetectionEnabled": False,
        "sessionReplaceDetectionAction": "detectionDisabled",
        "systemAuthControl": system_auth_control,
        "version": 2,
        "interfaces": {} if interfaces is None else interfaces,
    }
