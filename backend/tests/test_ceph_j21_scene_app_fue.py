"""J2.1 scene FUE: actual disposable application SQLite file + JWT HTTP.

Never a patient/clinic DB or media. Candidate routes and table exist only inside
this synthetic test. Import/scene/edit/reopen use real application dependencies.
"""
from __future__ import annotations

import hashlib
import shutil

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import database, models
from backend.main import app
from backend.models_ceph_premium_scene_fue import CephPremiumSceneFueSnapshot
from backend.models_media_core import ClinicalAsset
from backend.routers.cephalo_study_media_binding import router as media_router
from backend.routers.ceph_premium_scene_app_fue import router as scene_router
from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import _case, _read, _jwt
from backend.tests.test_ceph_j21_m4_real_jwt_fue import (
    _scene_for_binding, _real_encrypted_test_png,
)


@pytest.fixture
def disposable_app(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("CEPH_J21_SCENE_APP_FUE_ONLY", "1")
    monkeypatch.setenv("DC_DOS05_FUE_ONLY", "1")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "00" * 32)
    root = tmp_path / "isolated-app-fue"
    root.mkdir()
    db_file = root / "ceph-j21-scene-app-fue.sqlite3"
    monkeypatch.setenv("CEPH_J21_SCENE_APP_FUE_ROOT", str(root))
    media_root = root / "synthetic-media"
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root", lambda: media_root
    )
    engine = create_engine(f"sqlite:///{db_file.as_posix()}", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    # The license middleware intentionally reads database.SessionLocal directly.
    # Bind that independent middleware lookup to the same disposable app DB.
    monkeypatch.setattr(database, "SessionLocal", Session)
    active = {"session": Session()}

    def app_db():
        yield active["session"]

    # The connected test app uses the same real SQLAlchemy file session for
    # JWT login, patient/media import, study bindings, scene and readback.
    original_dependencies = dict(app.dependency_overrides)
    original_routes = list(app.router.routes)
    app.dependency_overrides[database.get_db] = app_db
    app.include_router(media_router, prefix="/api/ia")
    app.include_router(scene_router, prefix="/api/ia")
    try:
        yield client, active, Session, root, media_root
    finally:
        app.router.routes[:] = original_routes
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_dependencies)
        active["session"].close()
        engine.dispose()
        assert db_file.exists()
        shutil.rmtree(root)  # Synthetic DB and encrypted media removed after FUE.


def _import_and_bind(client, owner, patient, study, headers, revision):
    original = _real_encrypted_test_png()
    incoming = client.post(
        f"/api/patients/{patient.id}/assets/import", headers=headers,
        data={"asset_type": "RADIOGRAPH", "source_kind": "UPLOAD", "timepoint": "T0"},
        files={"file": ("synthetic-scene-only.png", original, "image/png")},
    )
    assert incoming.status_code == 201, incoming.text[:400]
    asset = incoming.json()
    binding = client.post(
        f"/api/ia/analyses/{study.id}/media-bindings/RADIO_SOURCE",
        headers=headers,
        json={"patient_id": patient.id, "asset_id": asset["id"], "expected_revision": revision},
    )
    assert binding.status_code == 201, binding.text[:400]
    scene = _scene_for_binding(owner, patient, study, revision, asset, original)
    return scene, original


def _next_version(previous):
    raw = previous.canonical_dict()
    raw["identity"]["scene_revision"] = previous.identity.scene_revision + 1
    raw["identity"]["parent_scene_sha256"] = previous.sha256()
    first = raw["landmarks"][0]
    first["x"] += 4
    first["origin"] = "PRACTITIONER_EDIT"
    first["score_status"] = "NOT_EMITTED"
    first["confidence"] = None
    for measurement in raw["measurements"]:
        measurement["status"] = "UNAVAILABLE"
        measurement["value"] = None
    return CephaloPremiumSceneDraft.model_validate(raw)


def test_j21_app_jwt_import_edit_save_close_reopen_tenant_guards(disposable_app):
    client, active, Session, root, media_root = disposable_app
    db = active["session"]
    dentist = make_user(db, email="j21-fue-synthetic-owner@cabinet.invalid")
    patient, study, _ = _case(db, dentist)
    patient_id = patient.id
    patient_b, study_b, _ = _case(db, dentist)
    outsider = make_user(db, email="j21-fue-synthetic-cabinet-x@cabinet.invalid")
    patient_x, study_x, _ = _case(db, outsider)
    headers = _jwt(client, dentist)
    _, science = _read(client, study.id, headers)
    scene, original = _import_and_bind(
        client, dentist, patient, study, headers, science["revision"]
    )
    initial_scene = scene.canonical_dict()
    initial_scene["measurements"] = [{
        "id": "SNA", "unit": "DEG", "status": "RAW_NONCLINICAL", "value": 80.4
    }]
    scene = CephaloPremiumSceneDraft.model_validate(initial_scene)
    path = f"/api/ia/analyses/{study.id}/premium-scene-fue"

    # Media identity must be proven before the first scene ever commits.
    initial = client.post(
        path, headers=headers, json={"scene": scene.canonical_dict(), "expected_parent_sha256": None}
    )
    assert initial.status_code == 201, initial.text[:700]
    first = initial.json()
    assert first["scene_sha256"] == scene.sha256()
    assert first["verified_original"]["image_sha256"] == hashlib.sha256(original).hexdigest()
    assert first["clinical_release"] is False
    assert first["scientific_digest_source_certified"] is False
    assert first["desktop_fue_verified"] is False

    client.cookies.clear()
    assert client.get(path, params={"patient_id": patient.id}).status_code == 401
    denied_x = client.get(path, headers=_jwt(client, outsider), params={"patient_id": patient.id})
    assert denied_x.status_code == 403, denied_x.text[:300]
    headers = _jwt(client, dentist)
    wrong_patient = client.get(path, headers=headers, params={"patient_id": patient_b.id})
    assert wrong_patient.status_code in (403, 404)
    forged = scene.canonical_dict()
    forged["identity"]["employer_id"] = outsider.id
    cross_tenant = client.post(
        path, headers=headers, json={"scene": forged, "expected_parent_sha256": None}
    )
    assert cross_tenant.status_code == 403

    edited = _next_version(scene)
    forged_auto = edited.canonical_dict()
    forged_auto["landmarks"][0]["origin"] = "SRPOSE38_AUTO"
    mislabelled = client.post(
        path, headers=headers, json={
            "scene": forged_auto, "expected_parent_sha256": first["scene_sha256"]
        }
    )
    assert mislabelled.status_code == 409
    forged_measurement = edited.canonical_dict()
    forged_measurement["measurements"][0]["status"] = "RAW_NONCLINICAL"
    forged_measurement["measurements"][0]["value"] = 80.4
    not_invalidated = client.post(
        path, headers=headers, json={
            "scene": forged_measurement, "expected_parent_sha256": first["scene_sha256"]
        }
    )
    assert not_invalidated.status_code == 409
    step2 = client.post(
        path, headers=headers, json={
            "scene": edited.canonical_dict(), "expected_parent_sha256": first["scene_sha256"]
        }
    )
    assert step2.status_code == 201, step2.text[:700]
    assert step2.json()["scene_sha256"] != first["scene_sha256"]
    replay = client.post(
        path, headers=headers, json={
            "scene": edited.canonical_dict(), "expected_parent_sha256": first["scene_sha256"]
        }
    )
    assert replay.status_code == 409

    # This is a new genuine SQLAlchemy session on the same test application DB
    # after the previous connection is closed; it is not the old in-memory ledger.
    active["session"].close()
    active["session"] = Session()
    reopened = client.get(path, headers=headers, params={"patient_id": patient_id})
    assert reopened.status_code == 200, reopened.text[:700]
    result = reopened.json()
    assert result["scene_sha256"] == edited.sha256()
    assert result["scene"]["landmarks"] == edited.canonical_dict()["landmarks"]
    assert result["scene_revision"] == 2
    assert result["scene"]["measurements"][0]["status"] == "UNAVAILABLE"
    assert result["scene"]["measurements"][0]["value"] is None
    assert active["session"].query(CephPremiumSceneFueSnapshot).count() == 2
    assert result["verified_original"]["image_sha256"] == hashlib.sha256(original).hexdigest()

    # A scene digest can never turn corrupted persistent JSON into normal state.
    row = (active["session"].query(CephPremiumSceneFueSnapshot)
           .filter(CephPremiumSceneFueSnapshot.scene_revision == 2).one())
    row.payload = "{}"
    active["session"].commit()
    tamper = client.get(path, headers=headers, params={"patient_id": patient_id})
    assert tamper.status_code == 409
    row.payload = edited.canonical_bytes().decode("utf-8")
    active["session"].commit()

    asset = active["session"].get(ClinicalAsset, edited.identity.original_asset_id)
    ciphertext = media_root.joinpath(*asset.storage_key.split("/"))
    protected = ciphertext.read_bytes()
    damaged = bytearray(protected)
    damaged[-1] ^= 1
    ciphertext.write_bytes(damaged)
    source_tamper = client.get(path, headers=headers, params={"patient_id": patient_id})
    assert source_tamper.status_code == 409
    ciphertext.write_bytes(protected)
    assert client.get(path, headers=headers, params={"patient_id": patient_id}).status_code == 200
    assert media_root.is_dir()


def test_j21_app_fue_denied_without_env_or_correct_file(disposable_app, monkeypatch, tmp_path):
    client, active, Session, root, media_root = disposable_app
    user = make_user(active["session"], email="j21-fue-guard@cabinet.invalid")
    patient, study, _ = _case(active["session"], user)
    headers = _jwt(client, user)
    path = f"/api/ia/analyses/{study.id}/premium-scene-fue"
    monkeypatch.delenv("CEPH_J21_SCENE_APP_FUE_ONLY")
    reply = client.get(path, headers=headers, params={"patient_id": patient.id})
    assert reply.status_code == 503
    monkeypatch.setenv("CEPH_J21_SCENE_APP_FUE_ONLY", "1")
    monkeypatch.setenv("CEPH_J21_SCENE_APP_FUE_ROOT", str(tmp_path))
    mismatch = client.get(path, headers=headers, params={"patient_id": patient.id})
    assert mismatch.status_code == 503
