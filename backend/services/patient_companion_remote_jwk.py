from __future__ import annotations

import json
import uuid
from typing import Literal

from jwcrypto import jwk
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PublicP256Jwk(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    kty: Literal["EC"] = "EC"
    crv: Literal["P-256"] = "P-256"
    kid: str
    use: Literal["sig", "enc"]
    x: str = Field(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]{43}$")
    y: str = Field(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]{43}$")

    @field_validator("kid")
    @classmethod
    def require_uuid_kid(cls, value: str) -> str:
        return str(uuid.UUID(value))

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(), separators=(",", ":"), sort_keys=True)

    def validate_curve_point(self) -> None:
        parsed = jwk.JWK.from_json(self.canonical_json())
        # Forces jwcrypto to materialize the expected public operation key.
        operation = "verify" if self.use == "sig" else "encrypt"
        parsed.get_op_key(operation)


class RemotePublicKeyEnrollment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signing: PublicP256Jwk
    encryption: PublicP256Jwk

    @field_validator("signing")
    @classmethod
    def require_signing_use(cls, value: PublicP256Jwk) -> PublicP256Jwk:
        if value.use != "sig":
            raise ValueError("signing key must use=sig")
        value.validate_curve_point()
        return value

    @field_validator("encryption")
    @classmethod
    def require_encryption_use(cls, value: PublicP256Jwk) -> PublicP256Jwk:
        if value.use != "enc":
            raise ValueError("encryption key must use=enc")
        value.validate_curve_point()
        return value
