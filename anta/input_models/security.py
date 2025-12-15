# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for security tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Any, ClassVar, get_args
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
    description: str | None = None
    """Optional metadata describing the IPSec peer. Used for reporting."""
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
        description = f" ({self.description})" if self.description else ""
        return f"Peer: {self.peer}{description} VRF: {self.vrf}"


class IPSecConn(BaseModel):
    """Details of an IPv4 security connection for a peer."""

    model_config = ConfigDict(extra="forbid")
    source_address: IPv4Address
    """The IPv4 address of the source in the security connection."""
    destination_address: IPv4Address
    """The IPv4 address of the destination in the security connection."""

    def __str__(self) -> str:
        """Return a string representation of the IPSecConn model. Used in failure messages.

        Examples
        --------
        - Source: 100.64.3.2 Destination: 100.64.2.2
        """
        return f"Source: {self.source_address} Destination: {self.destination_address}"


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


class ACLEntry(BaseModel):
    """Model for an Access Control List (ACL) entry."""

    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=1, le=4294967295)
    """Sequence number of the ACL entry, used to define the order of processing. Must be between 1 and 4294967295."""
    action: str
    """Action of the ACL entry. Example: `deny ip any any`."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ACLEntry for reporting.

        Examples
        --------
        - Sequence: 10
        """
        return f"Sequence: {self.sequence}"


class ACL(BaseModel):
    """Model for an Access Control List (ACL)."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """Name of the ACL."""
    entries: list[ACLEntry]
    """List of the ACL entries."""
    IPv4ACLEntry: ClassVar[type[ACLEntry]] = ACLEntry
    """To maintain backward compatibility."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ACL for reporting.

        Examples
        --------
        - ACL name: Test
        """
        return f"ACL name: {self.name}"


class IPv4ACL(ACL):  # pragma: no cover
    """Alias for the ACL model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the ACL model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the IPv4ACL class, emitting a deprecation warning."""
        warn(
            message="IPv4ACL model is deprecated and will be removed in ANTA v2.0.0. Use the ACL model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class IPSecPeers(IPSecPeer):  # pragma: no cover
    """Alias for the IPSecPeers model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the IPSecPeer model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the IPSecPeers class, emitting a deprecation warning."""
        warn(
            message="IPSecPeers model is deprecated and will be removed in ANTA v2.0.0. Use the IPSecPeer model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
