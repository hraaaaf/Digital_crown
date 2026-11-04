"""B06 FUE: patient-free signed capture BEFORE independent staff review.

This is an actual SQLCipher test fixture with ephemeral Ed25519 device keys,
not physical scanner enrollment or human clinical certification.
"""
from dataclasses import replace
import inspect
import json
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from isolated_fue_lot06c import unassigned_device_manifest_lab as manifest
from isolated_fue_lot06c.c05b03m_security_gate_lab import BridgeRejected, identity
from isolated_fue_lot06c.test_phase2_staff_review_media_sqlcipher_v15 import _ctx
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _counts, synthetic_sqlcipher_bridge,
)



def test_b06_device_manifest_constructor_has_no_clinical_object_input():
    arguments = set(inspect.signature(manifest.new_unassigned_manifest).parameters)
    assert not arguments.intersection({
        "claim", "patient", "patient_id", "staff", "staff_id",
        "dossier", "dob", "date_naissance", "appointment",
    })
    assert "tenant" in arguments and "digest" in arguments
    with pytest.raises(TypeError):
        manifest.new_unassigned_manifest(patient=42)
    assert not set(manifest.unassigned.c.keys()).intersection({
        "patient", "patient_id", "staff", "staff_id", "dossier",
        "date_naissance", "appointment",
    })
    print("DC06_B06_DEVICE_MANIFEST_CONSTRUCTOR_CANNOT_ACCEPT_PATIENT_PASS")


def test_b06_manifest_has_no_patient_or_staff_and_rejects_forgery_nonce_replay(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _, _, _, _, _, _, _, private, _, _, _, _) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    with Session(engine) as db:
        row = db.execute(select(manifest.unassigned)).mappings().one()
        saved = manifest._from_row(row)
        assert saved.tenant == claim.tenant
        assert saved.device == claim.device
        assert saved.digest == claim.digest
        assert saved.byte_size == claim.byte_size
        assert set(vars(saved)).isdisjoint({
            "patient", "patient_id", "staff", "staff_id", "dossier",
            "date_naissance", "appointment", "appointment_id",
        })
        frame = json.loads(manifest._wire(saved))
        assert "patient" not in frame and "staff" not in frame
        assert "dossier" not in frame and "appointment" not in frame
        assert row["signature"] == manifest.sign_unassigned(saved, private)
        manifest.check_pending(db, claim)

        # Malicious changes cannot be covered by the original signature.
        wrong_key = Ed25519PrivateKey.generate()
        with pytest.raises(BridgeRejected, match="SIGNATURE_INVALID"):
            manifest.register_unassigned(
                db, replace(saved, capture=saved.capture + "-foreign"),
                manifest.sign_unassigned(
                    replace(saved, capture=saved.capture + "-foreign"), wrong_key,
                ),
            )
        for changed in (
            replace(saved, digest="0" * 64),
            replace(saved, byte_size=saved.byte_size + 1),
            replace(saved, capture=saved.capture + "-x"),
            replace(saved, station=saved.station + "-x"),
            replace(saved, generation=saved.generation + 1),
        ):
            with pytest.raises(BridgeRejected):
                manifest.register_unassigned(
                    db, changed, row["signature"],
                )
        with pytest.raises(BridgeRejected, match="DUPLICATE_OR_NONCE_REPLAY"):
            replay = replace(saved, capture=saved.capture + "-replay")
            manifest.register_unassigned(
                db, replay, manifest.sign_unassigned(replay, private),
            )
        # A different nonce must NOT permit overwriting the original
        # immutable capture identity either. Both constraints fail closed.
        with pytest.raises(BridgeRejected, match="DUPLICATE_OR_NONCE_REPLAY"):
            second_nonce = replace(saved, nonce="0" * 48)
            if second_nonce.nonce == saved.nonce:
                second_nonce = replace(saved, nonce="1" * 48)
            manifest.register_unassigned(
                db, second_nonce, manifest.sign_unassigned(second_nonce, private),
            )
        with Session(engine) as verified:
            assert verified.execute(select(manifest.unassigned)).mappings().one()[
                "signature"
            ] == row["signature"]
        db.rollback()

    assert _counts(engine) == (0, 0, 0)
    print("DC06_B06_UNASSIGNED_ED25519_NO_PATIENT_STAFF_NONCE_REPLAY_PASS")


def test_b06_manifest_expiry_tampering_device_revocation_and_atomic_rollback(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _, _, _, _, _, _, _, _, _, _, _, _) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    with Session(engine) as db:
        manifest.check_pending(db, claim)
        db.rollback()

    # Verify a consumption attempt rolled back without a staff decision
    # leaves the manifest available (same SQLCipher transaction boundary).
    with Session(engine) as db:
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        manifest.consume_for_review(db, claim)
        assert db.execute(select(manifest.unassigned.c.consumed)).scalar_one() == 1
        db.rollback()
    with Session(engine) as db:
        manifest.check_pending(db, claim)
        db.rollback()

    with engine.begin() as conn:
        conn.execute(update(manifest.unassigned).values(digest="0" * 64))
    with Session(engine) as db:
        with pytest.raises(BridgeRejected):
            manifest.check_pending(db, claim)
        db.rollback()
    with engine.begin() as conn:
        conn.execute(update(manifest.unassigned).values(digest=claim.digest))
        conn.execute(update(manifest.unassigned).values(expires_at=1))
    with Session(engine) as db:
        with pytest.raises(BridgeRejected, match="EXPIRED"):
            manifest.check_pending(db, claim)
        db.rollback()
    with engine.begin() as conn:
        conn.execute(update(manifest.unassigned).values(
            expires_at=int(time.time()) + 30,
        ))
        conn.execute(update(identity).values(active=0))
    with Session(engine) as db:
        with pytest.raises(BridgeRejected, match="REVOKED"):
            manifest.check_pending(db, claim)
        db.rollback()
    assert _counts(engine) == (0, 0, 0)
    print("DC06_B06_UNASSIGNED_EXPIRY_REVOKE_TAMPER_ATOMIC_ROLLBACK_PASS")
