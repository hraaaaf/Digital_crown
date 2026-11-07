"""Adversarial synthetic-only FUE for B06-4D-F1. No DB or clinic access."""
import hashlib
import pytest

from isolated_fue_lot06c.b06_versioned_crypto_synthetic import (
    SyntheticCryptoDenied, SyntheticKeyring,
)

P = b"synthetic-radiograph-pixels-not-a-patient"
D = hashlib.sha256(P).hexdigest()
K1 = bytes(range(32))
K2 = bytes(reversed(range(32)))


def ring():
    return SyntheticKeyring(
        media_keys={"media1": K1, "media2": K2},
        locator_keys={"loc1": K1},
    )


def test_f1_01_versioned_roundtrip_and_rotation():
    r = ring()
    first = r.encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media1")
    second = r.encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media2")
    assert first.startswith(b"DCM2") and second.startswith(b"DCM2")
    assert first != second
    assert r.decrypt(tenant=1, digest=D, envelope=first) == P
    assert r.decrypt(tenant=1, digest=D, envelope=second) == P


def test_f1_02_locator_stable_across_media_key_rotation_and_tenant_scoped():
    r = ring()
    before = r.locator(tenant=1, digest=D, locator_key_id="loc1")
    rotated = SyntheticKeyring(media_keys={"media2": K2}, locator_keys={"loc1": K1})
    assert rotated.locator(tenant=1, digest=D, locator_key_id="loc1") == before
    assert rotated.locator(tenant=2, digest=D, locator_key_id="loc1") != before


def test_f1_03_historical_key_missing_fails_closed():
    old = ring().encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media1")
    new_only = SyntheticKeyring(media_keys={"media2": K2}, locator_keys={"loc1": K1})
    with pytest.raises(SyntheticCryptoDenied, match="KEY_UNAVAILABLE"):
        new_only.decrypt(tenant=1, digest=D, envelope=old)


def test_f1_04_wrong_historical_key_fails_closed():
    old = ring().encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media1")
    wrong = SyntheticKeyring(media_keys={"media1": K2}, locator_keys={"loc1": K1})
    with pytest.raises(SyntheticCryptoDenied, match="AUTHENTICATION_FAILED"):
        wrong.decrypt(tenant=1, digest=D, envelope=old)


def test_f1_05_cross_tenant_and_digest_swap_denied():
    r = ring()
    blob = r.encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media1")
    with pytest.raises(SyntheticCryptoDenied, match="AUTHENTICATION_FAILED"):
        r.decrypt(tenant=2, digest=D, envelope=blob)
    with pytest.raises(SyntheticCryptoDenied, match="AUTHENTICATION_FAILED"):
        r.decrypt(tenant=1, digest=hashlib.sha256(b"other").hexdigest(), envelope=blob)


def test_f1_06_tampered_ciphertext_or_header_denied():
    r = ring()
    blob = r.encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media1")
    for damaged in (blob[:-1] + bytes([blob[-1] ^ 1]), b"DCM1" + blob[4:],
                    blob[:5] + b"media2" + blob[11:]):
        with pytest.raises(SyntheticCryptoDenied):
            r.decrypt(tenant=1, digest=D, envelope=damaged)


@pytest.mark.parametrize("bad_id", ["", "../x", "MEDIA", "a" * 33, "méd"])
def test_f1_07_invalid_key_ids_rejected(bad_id):
    with pytest.raises(SyntheticCryptoDenied, match="INVALID_KEY_ID"):
        ring().encrypt(tenant=1, digest=D, plaintext=P, media_key_id=bad_id)


def test_f1_08_bad_digest_and_plaintext_denied():
    with pytest.raises(SyntheticCryptoDenied, match="DIGEST_MISMATCH"):
        ring().encrypt(tenant=1, digest=D, plaintext=b"wrong", media_key_id="media1")
    with pytest.raises(SyntheticCryptoDenied, match="INVALID_DIGEST"):
        ring().locator(tenant=1, digest="no", locator_key_id="loc1")


def test_f1_09_short_and_truncated_envelopes_denied():
    r = ring()
    blob = r.encrypt(tenant=1, digest=D, plaintext=P, media_key_id="media1")
    for damaged in (b"", b"DCM2", b"DCM2" + bytes([255]), blob[:17]):
        with pytest.raises(SyntheticCryptoDenied):
            r.decrypt(tenant=1, digest=D, envelope=damaged)


def test_f1_10_no_legacy_dcm1_silent_fallback():
    with pytest.raises(SyntheticCryptoDenied, match="INVALID_ENVELOPE"):
        ring().decrypt(tenant=1, digest=D, envelope=b"DCM1" + b"x" * 64)
