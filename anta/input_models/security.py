# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for security tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Any, get_args
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anta.custom_types import EcdsaKeySize, EncryptionAlgorithm, RsaKeySize

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class IPSecPeer(BaseModel):
    """IPSec (Internet Protocol Security) model represents the details of an IPv4 security peer."""

    model_config = ConfigDict(extra="forbid")
    peer: IPv4Address
    """The IPv4 address of the security peer."""
    vrf: str = "default"
    """VRF context. Defaults to `default`."""
    connections: list[IPSecConn] | None = None
    """A list of IPv4 security connections associated with the peer. Defaults to None."""

    def __str__(self) -> str:
        """Return a string representation of the IPSecPeer model. Used in failure messages.

        Examples
        --------
        - Peer: 1.1.1.1 VRF: default
        """
        return f"Peer: {self.peer} VRF: {self.vrf}"


class IPSecConn(BaseModel):
    """Details of an IPv4 security connection for a peer."""

    model_config = ConfigDict(extra="forbid")
    source_address: IPv4Address
    """The IPv4 address of the source in the security connection."""
    destination_address: IPv4Address
    """The IPv4 address of the destination in the security connection."""


class APISSLCertificate(BaseModel):
    """Model for an API SSL certificate."""

    model_config = ConfigDict(extra="forbid")
    certificate_name: str
    """The name of the certificate to be verified."""
    expiry_threshold: int
    """The expiry threshold of the certificate in days."""
    common_name: str
    """The Common Name of the certificate."""
    encryption_algorithm: EncryptionAlgorithm
    """The encryption algorithm used by the certificate."""
    key_size: RsaKeySize | EcdsaKeySize
    """The key size (in bits) of the encryption algorithm."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the APISSLCertificate for reporting.

        Examples
        --------
        - Certificate: SIGNING_CA.crt
        """
        return f"Certificate: {self.certificate_name}"

    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        """Validate the key size provided to the APISSLCertificates class.

        If encryption_algorithm is RSA then key_size should be in {2048, 3072, 4096}.

        If encryption_algorithm is ECDSA then key_size should be in {256, 384, 521}.
        """
        if self.encryption_algorithm == "RSA" and self.key_size not in get_args(RsaKeySize):
            msg = f"`{self.certificate_name}` key size {self.key_size} is invalid for RSA encryption. Allowed sizes are {get_args(RsaKeySize)}."
            raise ValueError(msg)

        if self.encryption_algorithm == "ECDSA" and self.key_size not in get_args(EcdsaKeySize):
            msg = f"`{self.certificate_name}` key size {self.key_size} is invalid for ECDSA encryption. Allowed sizes are {get_args(EcdsaKeySize)}."
            raise ValueError(msg)

        return self


class ACL(BaseModel):
    """Model for an Access Control List (ACL)."""

    name: str
    """Name of the ACL."""
    entries: list[ACLEntry]
    """List of the ACL entries."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ACL for reporting.

        Examples
        --------
        - ACL name: Test
        """
        return f"ACL name: {self.name}"


class ACLEntry(BaseModel):
    """Model for an Access Control List (ACL) entry."""

    sequence: int = Field(ge=1, le=4294967295)
    """The unique sequence number of the ACL entry, used to define the order of processing. Must be between 1 and 4294967295."""
    action: str
    """The action to be applied to matching traffic.

    Attributes:
        - action (str): Specifies whether the traffic should be permitted or denied. For example, 'permit' allows the traffic to pass, while 'deny' blocks it.
        - protocol (str): Defines the protocol for the rule, such as 'icmp', 'icmpv6' or 'ipv6'. This specifies the type of traffic the rule applies to.
        - source_address (str): The source address for the rule. 'any' means it matches any source address.
        - destination_address (str): The destination address for the rule. 'any' means it matches any destination address.
        - security context(Optional[str]): A keyword used to specify additional conditions for the rule

    This ACL entry specifies the action to be applied to traffic that matches the defined conditions (e.g., 'permit ipv6 any any' allows any IPv6 traffic).
    """

    def __str__(self) -> str:
        """Return a human-readable string representation of the ACLEntry for reporting.

        Examples
        --------
        - Sequence: 10
        """
        return f"Sequence: {self.sequence}"


class IPSecPeers(IPSecPeer):  # pragma: no cover
    """Alias for the IPSecPeers model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the IPSecPeer model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the IPSecPeer class, emitting a deprecation warning."""
        warn(
            message="IPSecPeers model is deprecated and will be removed in ANTA v2.0.0. Use the IPSecPeer model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
