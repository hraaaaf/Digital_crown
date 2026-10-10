"""Purpose-separated key material; legacy database passphrases never rotate implicitly."""
from __future__ import annotations
import hashlib
import hmac
import os

MOBILE_KEY_VERSION = "2"

def keys_equal(left: str, right: str) -> bool:
    """Compare encoded key bytes too; hex case cannot bypass separation."""
    if not left or not right:
        return False
    if hmac.compare_digest(left.encode(), right.encode()):
        return True
    try:
        return hmac.compare_digest(bytes.fromhex(left), bytes.fromhex(right))
    except ValueError:
        return False


def sqlcipher_passphrase() -> str:
    dedicated = os.getenv("SQLCIPHER_KEY_HEX", "").strip()
    if dedicated:
        try:
            if len(bytes.fromhex(dedicated)) != 32:
                raise ValueError()
        except ValueError:
            raise ValueError("SQLCIPHER_KEY_HEX must encode 32 bytes") from None
        if keys_equal(dedicated, os.getenv("SECRET_KEY", "")):
            raise ValueError("Storage key must be independent from authentication key")
        return dedicated
    # Compatibility: retain the EXACT historical passphrase, without rekey/stamp.
    return os.getenv("CABINET_MASTER_KEY_HEX") or os.getenv("SECRET_KEY") or "default-dc-fallback-key"

def mobile_pairing_key_hex() -> str:
    dedicated = os.getenv("MOBILE_PAIRING_KEY_HEX", "").strip()
    if dedicated:
        try:
            if len(bytes.fromhex(dedicated)) != 32:
                raise ValueError()
        except ValueError:
            raise ValueError("MOBILE_PAIRING_KEY_HEX must encode 32 bytes") from None
        if any(keys_equal(dedicated, other) for other in (sqlcipher_passphrase(), os.getenv("CABINET_MASTER_KEY_HEX", ""), os.getenv("SECRET_KEY", ""))):
            raise ValueError("Mobile key must be independent from storage and authentication keys")
        return dedicated
    root = os.getenv("CABINET_MASTER_KEY_HEX", "").strip()
    if not root:
        raise ValueError("CABINET_MASTER_KEY_HEX required for legacy mobile key derivation")
    try:
        raw = bytes.fromhex(root)
        if len(raw) != 32:
            raise ValueError()
    except ValueError:
        raise ValueError("Invalid cabinet root key") from None
    # One-way domain separation: never deliver the database/backup root to a phone.
    return hmac.new(raw, b"DigitalCrown/mobile-payload/v2", hashlib.sha256).hexdigest()
