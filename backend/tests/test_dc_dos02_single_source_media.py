"""DC-DOS-02: each synthetic manual media import has one canonical original ID.

A C3 thumbnail is an authorized DERIVED artifact, NOT a second source.
Prove API import -> bounded timeline -> authenticated content -> tenant-scoped
encrypted file bytes for PHOTO, RADIOGRAPH, DOCUMENT, T0/T1/T2.
All identities and bytes live in in-memory SQLite and tmp_path only.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from io import BytesIO

import fitz
from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import _jwt


def _patient(db, employer_id: int, suffix: str):
    item = models.Patient(
        numero_dossier=f"DC-DOS02-{suffix}",
        nom="SYNTHESE",
        prenom=suffix,
        date_naissance=datetime(2002, 1, 1),
        sexe="F",
        employer_id=employer_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _png(rgb: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (820, 620), rgb)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _pdf() -> bytes:
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text(
            (64, 80), "DC-DOS02 SYNTHETIC MEDIA TEST - NOT A CLINICAL REPORT",
        )
        return document.tobytes(garbage=4, deflate=True)


def test_dc_dos02_photo_radio_pdf_preserve_original_asset_id_through_timeline_and_content(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setenv("SECRET_KEY", "dc-dos02-disposable-storage-test-key")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root",
        lambda: tmp_path,
    )

    patient_a = _patient(db, dentiste.id, "A")
    patient_b = _patient(db, dentiste.id, "B")
    foreign = make_user(db, email="dos02-foreign-cabinet@cabinet.invalid")
    patient_x = _patient(db, foreign.id, "X")
    foreign_headers = _jwt(client, foreign)
    assert len({patient_a.id, patient_b.id, patient_x.id}) == 3

    originals = [
        ("PHOTO", "T0", "image/png", "a-t0.png", _png((20, 100, 180))),
        ("RADIOGRAPH", "T1", "image/png", "a-t1.png", _png((210, 110, 30))),
        ("DOCUMENT", "T2", "application/pdf", "a-t2.pdf", _pdf()),
    ]

    original_ids = set()
    derivative_ids = set()
    storage_keys = set()
    for media_type, timepoint, mime, filename, payload in originals:
        posted = client.post(
            f"/api/patients/{patient_a.id}/assets/import",
            headers=auth_headers,
            data={"asset_type": media_type, "source_kind": "UPLOAD",
                  "timepoint": timepoint},
            files={"file": (filename, payload, mime)},
        )
        assert posted.status_code == 201, (media_type, posted.text[:500])
        info = posted.json()
        asset_id = info["id"]
        derivative_id = info["thumbnail_asset_id"]
        assert isinstance(asset_id, int) and asset_id not in original_ids
        assert isinstance(derivative_id, int) and derivative_id != asset_id
        original_ids.add(asset_id)
        derivative_ids.add(derivative_id)

        original = db.get(ClinicalAsset, asset_id)
        derivative = db.get(ClinicalAsset, derivative_id)
        assert original.employer_id == dentiste.id
        assert original.patient_id == patient_a.id
        assert original.asset_type == media_type
        assert original.source_kind == "UPLOAD"
        assert original.timepoint == timepoint
        assert original.mime_type == mime
        assert original.provenance_json["ingestion_channel"] == "WEB_API"
        assert original.provenance_json["validation_version"] == "C3_V1"
        assert original.sha256 == hashlib.sha256(payload).hexdigest()
        assert original.byte_size == len(payload)
        assert derivative.source_kind == "DERIVED"
        assert derivative.parent_asset_id == asset_id
        assert derivative.patient_id == original.patient_id
        assert derivative.employer_id == original.employer_id
        assert derivative.storage_key != original.storage_key

        for row in (original, derivative):
            assert row.storage_key not in storage_keys
            storage_keys.add(row.storage_key)
            encrypted = tmp_path.joinpath(row.storage_key).read_bytes()
            assert encrypted.startswith(b"DCM1")
            assert encrypted != payload

        # Timeline uses the ORIGINAL ID, never its separate thumbnail.
        result = client.get(
            f"/api/patients/{patient_a.id}/assets",
            headers=auth_headers,
            params={"asset_type": media_type, "timepoint": timepoint},
        )
        assert result.status_code == 200
        entries = result.json()["items"]
        assert len(entries) == 1
        assert entries[0]["id"] == asset_id
        assert entries[0]["thumbnail_asset_id"] == derivative_id
        assert entries[0]["source_kind"] == "UPLOAD"
        assert "storage_key" not in entries[0]
        assert "sha256" not in entries[0]

        content_url = f"/api/patients/{patient_a.id}/assets/{asset_id}/content"
        downloaded = client.get(content_url, headers=auth_headers)
        assert downloaded.status_code == 200
        assert downloaded.content == payload
        assert downloaded.headers["cache-control"] == "private, no-store"
        assert downloaded.headers["x-content-type-options"] == "nosniff"
        assert client.get(
            f"/api/patients/{patient_b.id}/assets/{asset_id}/content",
            headers=auth_headers,
        ).status_code in (403, 404)
        assert client.get(content_url, headers=foreign_headers).status_code in (403, 404)

    # Exactly three original source assets, each surfaced once, and three
    # explicitly linked derivatives; NO shadow DocumentArchive was produced.
    all_items = client.get(
        f"/api/patients/{patient_a.id}/assets", headers=auth_headers,
    )
    assert all_items.status_code == 200
    ids = [item["id"] for item in all_items.json()["items"]]
    assert len(ids) == 3 and set(ids) == original_ids
    assert not derivative_ids.intersection(ids)
    assert db.query(ClinicalAsset).filter(
        ClinicalAsset.patient_id == patient_a.id,
    ).count() == 6
    assert len(storage_keys) == 6
    assert len(list(tmp_path.rglob("*.dcm"))) == 6
    assert db.query(models.DocumentArchive).count() == 0
    assert client.get(
        f"/api/patients/{patient_x.id}/assets", headers=auth_headers,
    ).status_code in (403, 404)
    assert client.get(
        f"/api/patients/{patient_a.id}/assets", headers=foreign_headers,
    ).status_code in (403, 404)
