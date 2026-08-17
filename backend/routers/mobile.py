"""Mobile router compatibility wrapper with tenant-scoped revocation epochs.

The historical router is preserved byte-for-byte in ``mobile_legacy``.  This
wrapper only replaces mobile JWT issuance; all endpoints and LAN-first behavior
remain owned by the historical router.
"""
from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt

from backend.security import ALGORITHM, SECRET_KEY
from . import mobile_legacy as _legacy
from .mobile_legacy import *  # noqa: F401,F403


def _create_mobile_jwt(employer_id: int, role: str) -> str:
    """Issue a 24-hour mobile JWT whose JTI carries tenant and issuance time.

    The structured JTI lets the existing persistent blacklist reject every
    token issued before a cabinet-scoped revocation cutoff without tracking
    every active handset token individually.
    """
    now = datetime.now(timezone.utc)
    issued_us = int(now.timestamp() * 1_000_000)
    payload = {
        "sub": str(employer_id),
        "type": "mobile",
        "role": role,
        "jti": f"mobile:{int(employer_id)}:{issued_us}:{uuid.uuid4().hex}",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# claim_pairing_token lives in mobile_legacy and resolves this global at request
# time, so replacing it here changes issuance only; route definitions stay intact.
_legacy._create_mobile_jwt = _create_mobile_jwt
router = _legacy.router
