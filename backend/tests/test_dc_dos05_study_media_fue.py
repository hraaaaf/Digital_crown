"""DC-DOS-05 isolated FUE: real FastAPI JWT + SQLite + encrypted originals.

Router is intentionally NOT mounted in production. FUE explicitly mounts the
candidate only inside a synthetic test client, then removes its routes.
No actual patient data, clinical source assertion, DB migration or release.
"""
from __future__ import annotations

import hashlib
import os
from io import BytesIO
from json import dumps
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.exc import IntegrityError

from backend import models
from backend.main import app
from backend.models_cephalo_study_media import CephaloStudyMediaBinding
from backend.models_media_core import ClinicalAsset
from backend.routers.cephalo_study_media_binding import router as candidate_router
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import _case, _jwt, _read


def _png(color):
    buffer = BytesIO()
    Image.new("RGB", (800, 600), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _import(client, headers, patient_id, kind, timepoint, name, data):
    result = client.post(
        f"/api/patients/{patient_id}/assets/import",
        headers=headers,
        data={"asset_type": kind, "source_kind": "UPLOAD", "timepoint": timepoint},
        files={"file": (name, data, "image/png")},
    )
    assert result.status_code == 201, result.text[:400]
    return result.json()


def test_dc_dos05_real_jwt_two_origins_two_studies_two_cabinets_fail_closed(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setenv("DC_DOS05_FUE_ONLY", "1")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("SECRET_KEY", "dc-dos05-synthetic-test-media-encryption-secret-only")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path
    )

    # This candidate route is never mounted in backend/routers/__init__.py.
    original_routes = list(app.router.routes)
    app.include_router(candidate_router, prefix="/api/ia")
    try:
        patient_a, study_a, _ = _case(db, dentiste)
        patient_b, study_b, _ = _case(db, dentiste)
        cabinet_x = make_user(db, email="dos05-isolated-x@cabinet.invalid")
        patient_x, study_x, _ = _case(db, cabinet_x)
        x_headers = _jwt(client, cabinet_x)
        _, science_a = _read(client, study_a.id, auth_headers)
        revision = science_a["revision"]
        assert type(revision) is int and revision > 0

        photo_bytes = _png((25, 85, 165))
        radio_bytes = _png((194, 118, 32))
        other_bytes = _png((42, 140, 80))
        photo = _import(
            client, auth_headers, patient_a.id,
            "PHOTO", "T0", "dos05-context-photo.png", photo_bytes,
        )
        radio = _import(
            client, auth_headers, patient_a.id,
            "RADIOGRAPH", "T1", "dos05-source-radio.png", radio_bytes,
        )
        different_photo = _import(
            client, auth_headers, patient_a.id,
            "PHOTO", "T1", "dos05-unbound-candidate.png", other_bytes,
        )
        b_photo = _import(
            client, auth_headers, patient_b.id,
            "PHOTO", "T0", "dos05-b.png", _png((92, 20, 105)),
        )
        x_photo = _import(
            client, x_headers, patient_x.id,
            "PHOTO", "T0", "dos05-x.png", _png((200, 40, 80)),
        )
        assert len({photo["id"], radio["id"], b_photo["id"], x_photo["id"]}) == 4
        base = f"/api/ia/analyses/{study_a.id}/media-bindings"

        def payload(asset_id, rev=revision, patient_id=patient_a.id):
            return {"patient_id": patient_id, "asset_id": asset_id,
                    "expected_revision": rev}

        assert client.get(base, headers=auth_headers,
                          params={"patient_id": patient_a.id}).status_code == 409
        # Foreign patient, tenant, analysis, role and revision cannot be re-bound.
        checks = [
            ("B_ASSET_TO_A_STUDY_DENIED",
             client.post(base + "/PHOTO_CONTEXT", headers=auth_headers,
                         json=payload(b_photo["id"])), 404),
            ("TENANT_X_ASSET_TO_A_STUDY_DENIED",
             client.post(base + "/PHOTO_CONTEXT", headers=auth_headers,
                         json=payload(x_photo["id"])), 404),
            ("TENANT_X_STUDY_A_DENIED",
             client.post(base + "/PHOTO_CONTEXT", headers=x_headers,
                         json=payload(x_photo["id"])), 403),
            ("PATIENT_B_WITH_STUDY_A_DENIED",
             client.post(base + "/PHOTO_CONTEXT", headers=auth_headers,
                         json=payload(photo["id"], patient_id=patient_b.id)), 404),
            ("REVISION_STALE_DENIED",
             client.post(base + "/PHOTO_CONTEXT", headers=auth_headers,
                         json=payload(photo["id"], rev=revision + 1)), 409),
            ("ROLE_TYPE_SWAP_DENIED",
             client.post(base + "/RADIO_SOURCE", headers=auth_headers,
                         json=payload(photo["id"])), 409),
            ("UNKNOWN_ROLE_DENIED",
             client.post(base + "/UNKNOWN", headers=auth_headers,
                         json=payload(photo["id"])), 422),
            ("DERIVED_THUMBNAIL_DENIED",
             client.post(base + "/PHOTO_CONTEXT", headers=auth_headers,
                         json=payload(photo["thumbnail_asset_id"])), 409),
        ]
        for name, reply, code in checks:
            assert reply.status_code == code, (name, reply.status_code, reply.text[:300])

        original = client.post(
            base + "/PHOTO_CONTEXT", headers=auth_headers,
            json=payload(photo["id"]),
        )
        assert original.status_code == 201, original.text[:400]
        assert original.json()["created"] is True
        assert original.json()["clinical_release"] is False
        assert original.json()["cephalo_computation_from_source_proven"] is False
        repeat = client.post(
            base + "/PHOTO_CONTEXT", headers=auth_headers,
            json=payload(photo["id"]),
        )
        assert repeat.status_code == 201 and repeat.json()["created"] is False
        assert repeat.json()["id"] == original.json()["id"]
        swap = client.post(
            base + "/PHOTO_CONTEXT", headers=auth_headers,
            json=payload(different_photo["id"]),
        )
        assert swap.status_code == 409

        source = client.post(
            base + "/RADIO_SOURCE", headers=auth_headers,
            json=payload(radio["id"]),
        )
        assert source.status_code == 201, source.text[:400]
        assert source.json()["asset_sha256"] == hashlib.sha256(radio_bytes).hexdigest()
        scoped = client.get(
            base, headers=auth_headers, params={"patient_id": patient_a.id},
        )
        assert scoped.status_code == 200, scoped.text[:300]
        data = scoped.json()
        assert data["study_id"] == study_a.id
        assert data["patient_id"] == patient_a.id
        assert data["revision"] == revision
        assert data["clinical_release"] is False
        assert data["cephalo_computation_from_source_proven"] is False
        assert {x["role"] for x in data["items"]} == {
            "RADIO_SOURCE", "PHOTO_CONTEXT",
        }
        assert {x["asset_id"] for x in data["items"]} == {
            photo["id"], radio["id"],
        }
        assert db.query(CephaloStudyMediaBinding).filter(
            CephaloStudyMediaBinding.study_id == study_a.id,
        ).count() == 2
        assert db.query(CephaloStudyMediaBinding).filter(
            CephaloStudyMediaBinding.study_id.in_([study_b.id, study_x.id]),
        ).count() == 0
        # Even a bypass of the service cannot append a second role for the
        # same study: the real SQLite UNIQUE constraint is tested directly.
        with pytest.raises(IntegrityError):
            with db.begin_nested():
                db.add(CephaloStudyMediaBinding(
                    employer_id=dentiste.id,
                    patient_id=patient_a.id,
                    study_id=study_a.id,
                    asset_id=different_photo["id"],
                    role="PHOTO_CONTEXT",
                    asset_sha256=hashlib.sha256(other_bytes).hexdigest(),
                    revision=revision,
                    created_by=dentiste.id,
                ))
                db.flush()
        assert client.get(
            base, headers=x_headers, params={"patient_id": patient_a.id},
        ).status_code == 403
        assert client.get(
            base, headers=auth_headers, params={"patient_id": patient_b.id},
        ).status_code == 404

        # Re-open original: even direct DB metadata tampering cannot pass a read.
        radio_row = db.get(ClinicalAsset, radio["id"])
        original_hash = radio_row.sha256
        radio_row.sha256 = "a" * 64
        db.commit()
        tampered = client.get(
            base, headers=auth_headers, params={"patient_id": patient_a.id},
        )
        assert tampered.status_code == 409, tampered.text[:300]
        radio_row.sha256 = original_hash
        db.commit()

        # A study whose scientific evidence is no longer verifiable cannot
        # silently retain a supposedly authoritative study-media association.
        original_angles = study_a.angles_data
        study_a.angles_data = {"dc_dos05_tampered": True}
        db.commit()
        invalid_science = client.get(
            base, headers=auth_headers, params={"patient_id": patient_a.id},
        )
        assert invalid_science.status_code == 409, invalid_science.text[:300]
        study_a.angles_data = original_angles
        db.commit()

        # Without FUE-only gating, even on the test application, API is off.
        monkeypatch.delenv("DC_DOS05_FUE_ONLY")
        disabled = client.get(
            base, headers=auth_headers, params={"patient_id": patient_a.id},
        )
        assert disabled.status_code == 503

        report = {
            "head": os.environ.get("PRODUCT_HEAD", "LOCAL_NO_GITHUB_HEAD"),
            "case_id": "DC-DOS-05",
            "synthetic_only": True,
            "status": "FUE_API_STUDY_MEDIA_PREPRODUCTION_PASS",
            "study_media_roles": ["PHOTO_CONTEXT", "RADIO_SOURCE"],
            "real_http_jwt": True,
            "patient_a_b_and_cabinet_x_refused": True,
            "study_and_source_digest_revision_bound": True,
            "write_once_swap_refused": True,
            "db_unique_write_once": True,
            "tamper_fail_closed": True,
            "scientific_tamper_fail_closed": True,
            "unknown_role_denied": True,
            "default_disabled": True,
            "migration_executed": False,
            "production_router_mounted": False,
            "clinical_release": False,
        }
        assert all(report[key] is True for key in (
            "real_http_jwt", "patient_a_b_and_cabinet_x_refused",
            "study_and_source_digest_revision_bound", "write_once_swap_refused",
            "db_unique_write_once", "tamper_fail_closed", "scientific_tamper_fail_closed",
            "unknown_role_denied", "default_disabled",
        ))
        if os.environ.get("DC_DOS05_FUE_EVIDENCE_DIR"):
            output = Path(os.environ["DC_DOS05_FUE_EVIDENCE_DIR"])
            output.mkdir(parents=True, exist_ok=True)
            (output / "dc-dos05-fue-report.json").write_text(
                dumps(report, sort_keys=True, indent=2), encoding="utf-8",
            )
        print("DC_DOS05_STUDY_MEDIA_REAL_JWT_FUE_PASS", dumps(report))
    finally:
        app.router.routes[:] = original_routes
