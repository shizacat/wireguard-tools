#
# Pure Python reimplementation of wireguard-tools
#
# Copyright (c) 2022 Carnegie Mellon University
# SPDX-License-Identifier: MIT
#

from __future__ import annotations

from base64 import standard_b64encode, urlsafe_b64decode, urlsafe_b64encode
from secrets import token_bytes

from attrs import define, field

from .curve25519 import X25519PrivateKey


def convert_wireguard_key(value: str | bytes | WireguardKey) -> bytes:
    """Decodes a wireguard key to its byte string form.
    Accepts urlsafe encoded base64 keys with possibly missing padding.
    Validates that the resulting key value is a 32-byte byte string
    """
    if isinstance(value, WireguardKey):
        return value.keydata

    if isinstance(value, bytes):
        raw_key = value
    elif len(value) == 64:
        raw_key = bytes.fromhex(value)
    else:
        raw_key = urlsafe_b64decode(value + "==")

    if len(raw_key) != 32:
        raise ValueError("Invalid WireGuard key length")

    return raw_key


@define(frozen=True)
class WireguardKey:
    keydata: bytes = field(converter=convert_wireguard_key)

    @classmethod
    def generate(cls) -> WireguardKey:
        """Generate a new private key"""
        random_data = token_bytes(32)
        # turn it into a proper curve25519 private key by fixing/clamping the value
        private_bytes = X25519PrivateKey.from_private_bytes(random_data).private_bytes()
        return cls(private_bytes)

    def public_key(self) -> WireguardKey:
        """Derive public key from private key"""
        public_bytes = X25519PrivateKey.from_private_bytes(self.keydata).public_key()
        return WireguardKey(public_bytes)

    def __bool__(self) -> bool:
        return int.from_bytes(self.keydata, "little") != 0

    def __repr__(self) -> str:
        return f"WireguardKey('{self}')"

    def __str__(self) -> str:
        return standard_b64encode(self.keydata).decode("utf-8")

    @property
    def urlsafe(self) -> str:
        return urlsafe_b64encode(self.keydata).decode("utf-8").rstrip("=")

    def hex(self) -> str:
        return self.keydata.hex()