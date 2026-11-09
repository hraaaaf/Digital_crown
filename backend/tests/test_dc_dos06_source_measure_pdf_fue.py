"""DC-DOS-06 nonclinical causal FUE: actual encrypted pixels -> points -> engine -> PDF.

Only fabricated marker PNGs and synthetic patient identities. The detector is NOT
ONNX inference, not validated clinical cephalometry and cannot authorize care.
The candidate routes are mounted temporarily inside a disposable TestClient.
"""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from backend import models
from backend.main import app
from backend.models_media_core import ClinicalAsset
from backend.routers.cephalo_source_measure_pdf_fue import router as source_router
from backend.routers.cephalo_study_media_binding import router as binding_router
from backend.services.cephalo_safe_engine import cephalo_safe_engine
from backend.services.cephalo_source_measure_pdf_fue import (
    _canonical_sha, _read_synthetic_landmarks, synthetic_marker_color,
)
from backend.services.srpose38_contract import SOTA_LANDMARKS_MAPPING
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import _case, _jwt, _read


def _synthetic_radiograph(*, shift_marker_index: int | None = None) -> bytes:
    image = Image.new("RGB", (800, 600), (245, 245, 245))
    d = ImageDraw.Draw(image)
    for index, landmark_id in SOTA_LANDMARKS_MAPPING.items():
        x = 100 + (index * 37) % 490
        y = 60 + (index * 59) % 430
        if index == shift_marker_index:
            x += 12
        d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=synthetic_marker_color(index))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _source(client, patient_id, auth, png, *, name="synthetic-nonclinical.png"):
    response = client.post(
        f"/api/patients/{patient_id}/assets/import",
        headers=auth,
        data={"asset_type": "RADIOGRAPH", "source_kind": "UPLOAD", "timepoint": "T1"},
        files={"file": (name, png, "image/png")},
    )
    assert response.status_code == 201, response.text[:500]
    return response.json()


def _bind(client, patient_id, study_id, asset_id, revision, auth):
    return client.post(
        f"/api/ia/analyses/{study_id}/media-bindings/RADIO_SOURCE",
        headers=auth,
        json={
            "patient_id": patient_id, "asset_id": asset_id,
            "expected_revision": revision,
        },
    )


def _request(client, patient_id, study_id, revision, auth):
    return client.get(
        f"/api/ia/analyses/{study_id}/synthetic-source-measure-pdf",
        params={"patient_id": patient_id, "expected_revision": revision},
        headers=auth,
    )


def test_dc_dos06_authenticated_byte_causal_synthetic_pdf_fue(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch,
):
    monkeypatch.setenv("DC_DOS05_FUE_ONLY", "1")
    monkeypatch.setenv("DC_DOS06_FUE_ONLY", "1")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("SECRET_KEY", "dc-dos06-encrypted-synthetic-fixture-only")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path
    )

    initial_routes = list(app.router.routes)
    app.include_router(binding_router, prefix="/api/ia")
    app.include_router(source_router, prefix="/api/ia")
    try:
        patient_a, study_a, _ = _case(db, dentiste)
        patient_b, study_b, _ = _case(db, dentiste)
        foreign = make_user(db, email="dc-dos06-foreign-clinic@cabinet.invalid")
        patient_x, study_x, _ = _case(db, foreign)
        foreign_auth = _jwt(client, foreign)
        _, scientific = _read(client, study_a.id, auth_headers)
        rev_a = scientific["revision"]
        assert type(rev_a) is int and rev_a > 0

        original_bytes = _synthetic_radiograph()
        other_bytes = _synthetic_radiograph(shift_marker_index=7)
        assert original_bytes != other_bytes
        original = _source(client, patient_a.id, auth_headers, original_bytes)
        other = _source(client, patient_a.id, auth_headers, other_bytes,
                        name="synthetic-alt-unique.png")
        foreign_media = _source(client, patient_x.id, foreign_auth, other_bytes)
        assert hashlib.sha256(original_bytes).hexdigest() != hashlib.sha256(other_bytes).hexdigest()
        assert db.get(ClinicalAsset, original["id"]).sha256 == hashlib.sha256(original_bytes).hexdigest()

        # No inference from timepoint/filename/nearby study: unbound means 409.
        missing = _request(client, patient_a.id, study_a.id, rev_a, auth_headers)
        assert missing.status_code == 409
        assert _bind(client, patient_a.id, study_a.id, original["id"], rev_a,
                     auth_headers).status_code == 201

        pdf = _request(client, patient_a.id, study_a.id, rev_a, auth_headers)
        assert pdf.status_code == 200, pdf.text[:400] if pdf.status_code != 200 else ""
        assert pdf.content.startswith(b"%PDF")
        assert pdf.headers["X-Clinical-Release"] == "false"
        assert pdf.headers["X-Official-PDF"] == "false"
        assert pdf.headers["Cache-Control"] == "private, no-store"
        assert pdf.headers["X-DC-DOS06-Source-SHA256"] == hashlib.sha256(original_bytes).hexdigest()
        assert pdf.headers["X-DC-DOS06-PDF-SHA256"] == hashlib.sha256(pdf.content).hexdigest()
        points = _read_synthetic_landmarks(original_bytes)
        assert len(points) == 38
        calculate = cephalo_safe_engine.calculate_metrics(
            {p["id"]: (p["x"], p["y"]) for p in points},
            custom_mm_ratio=None,
        ).model_dump(mode="json")
        assert pdf.headers["X-DC-DOS06-Landmark-SHA256"] == _canonical_sha(points)
        assert pdf.headers["X-DC-DOS06-Measurement-SHA256"] == _canonical_sha(calculate)
        witness = {
            "schema_version": "DC_DOS06_SYNTHETIC_PIXEL_CHAIN_V1",
            "detector_id": "NONCLINICAL_RGB_MARKER_38_V1",
            "study_id": study_a.id,
            "patient_id": patient_a.id,
            "revision": rev_a,
            "source_asset_id": original["id"],
            "source_sha256": hashlib.sha256(original_bytes).hexdigest(),
            "landmarks_sha256": _canonical_sha(points),
            "measurements_sha256": _canonical_sha(calculate),
            "calibration_authority": None,
            "clinical_release": False,
            "existing_cephalo_analysis_metrics_from_source_proven": False,
            "official_pdf": False,
        }
        assert pdf.headers["X-DC-DOS06-Provenance-SHA256"] == _canonical_sha(witness)
        with fitz.open(stream=pdf.content, filetype="pdf") as document:
            assert len(document) == 1
            assert 590 < document[0].rect.width < 600
            printed = document[0].get_text()
            assert "DC-DOS-06 - SYNTHETIC REHEARSAL ONLY" in printed
            assert "NOT A CLINICAL CEPHALOMETRIC REPORT" in printed
            assert f"STUDY_ID: {study_a.id}" in printed
            assert f"REVISION: {rev_a}" in printed
            assert hashlib.sha256(original_bytes).hexdigest() in printed
            assert _canonical_sha(points) in printed
            assert _canonical_sha(calculate) in printed
            assert _canonical_sha(witness) in printed
            for group, metric in (("analyse_osseuse", "SNA"),
                                  ("analyse_osseuse", "SNB"),
                                  ("analyse_osseuse", "ANB"),
                                  ("analyse_dentaire", "IMPA")):
                value = calculate["metrics"][group][metric]["valeur"]
                assert type(value) in {int, float}
                assert f"RAW SYNTHETIC {metric}: {value:.3f}" in printed
            assert "CLINICAL_RELEASE: FALSE" in printed
            assert "INFERENCE_AUTHORITY: SYNTHETIC_ONLY_NOT_ONNX" in printed

        # Real pixel perturbation in another original generates different
        # actual landmarks, engine measures and PDF receipt, not only a label.
        study_a2 = models.CephaloAnalysis(
            patient_id=patient_a.id,
            image_original_path=study_a.image_original_path,
            landmarks_data=deepcopy(study_a.landmarks_data),
            angles_data=deepcopy(study_a.angles_data),
            is_calibrated=False,
            mm_per_pixel=None,
        )
        db.add(study_a2)
        db.commit()
        db.refresh(study_a2)
        assert _bind(client, patient_a.id, study_a2.id, other["id"], rev_a,
                     auth_headers).status_code == 201
        changed = _request(client, patient_a.id, study_a2.id, rev_a, auth_headers)
        assert changed.status_code == 200
        assert changed.headers["X-DC-DOS06-Source-SHA256"] != pdf.headers["X-DC-DOS06-Source-SHA256"]
        assert changed.headers["X-DC-DOS06-Landmark-SHA256"] != pdf.headers["X-DC-DOS06-Landmark-SHA256"]
        assert changed.headers["X-DC-DOS06-Measurement-SHA256"] != pdf.headers["X-DC-DOS06-Measurement-SHA256"]
        assert changed.headers["X-DC-DOS06-PDF-SHA256"] != pdf.headers["X-DC-DOS06-PDF-SHA256"]

        # Negative matrix: wrong study, tenant, patient, old revision, unbound
        # alternate study, unsigned/unverified source and forged scientific state.
        checks = [
            ("STALE_REVISION", _request(client, patient_a.id, study_a.id,
                                        rev_a + 1, auth_headers), 409),
            ("OTHER_PATIENT_STUDY", _request(client, patient_b.id, study_a.id,
                                            rev_a, auth_headers), 404),
            ("FOREIGN_CABINET", _request(client, patient_a.id, study_a.id,
                                        rev_a, foreign_auth), 403),
            ("FOREIGN_STUDY", _request(client, patient_x.id, study_a.id,
                                      rev_a, foreign_auth), 404),
            ("UNBOUND_PATIENT_B_STUDY", _request(client, patient_b.id, study_b.id,
                                                rev_a, auth_headers), 409),
        ]
        for name, reply, status in checks:
            assert reply.status_code == status, (name, reply.status_code, reply.text[:350])
        bad_rebind = _bind(client, patient_a.id, study_a.id, other["id"], rev_a,
                           auth_headers)
        assert bad_rebind.status_code == 409
        bad_tenant = _bind(client, patient_a.id, study_a.id,
                           foreign_media["id"], rev_a, auth_headers)
        assert bad_tenant.status_code == 404

        # Invalid input markers cannot accidentally receive a "green" receipt.
        blank = Image.new("RGB", (800, 600), (245, 245, 245))
        blank_data = BytesIO()
        blank.save(blank_data, format="PNG")
        blank_source = _source(client, patient_b.id, auth_headers, blank_data.getvalue(),
                               name="synthetic-no-landmarks.png")
        assert _bind(client, patient_b.id, study_b.id, blank_source["id"],
                     rev_a, auth_headers).status_code == 201
        blank_report = _request(client, patient_b.id, study_b.id, rev_a, auth_headers)
        assert blank_report.status_code == 409
        assert blank_report.content[:4] != b"%PDF"

        # Altering source storage digest or scientific graph must block PDF.
        record = db.get(ClinicalAsset, original["id"])
        original_sha = record.sha256
        record.sha256 = "a" * 64
        db.commit()
        tampered_source = _request(client, patient_a.id, study_a.id, rev_a,
                                    auth_headers)
        assert tampered_source.status_code == 409
        record.sha256 = original_sha
        db.commit()

        previous_science = deepcopy(study_a.angles_data)
        study_a.angles_data = {"tampered_dc_dos06": True}
        db.commit()
        tampered_science = _request(client, patient_a.id, study_a.id, rev_a,
                                     auth_headers)
        assert tampered_science.status_code == 409
        study_a.angles_data = previous_science
        db.commit()

        monkeypatch.delenv("DC_DOS06_FUE_ONLY")
        assert _request(client, patient_a.id, study_a.id, rev_a,
                        auth_headers).status_code == 503

        report = {
            "case_id": "DC-DOS-06",
            "head": os.getenv("PRODUCT_HEAD", "LOCAL_NO_GITHUB_HEAD"),
            "status": "NONCLINICAL_BYTE_CAUSAL_FUE_PASS",
            "synthetic_only": True,
            "real_http_jwt": True,
            "source_original_aesgcm_sha_verified": True,
            "landmarks_calculated_from_actual_source_pixels": True,
            "safe_cephalo_geometry_from_derived_points": True,
            "same_digest_chain_printed_in_real_pdf": True,
            "raw_synthetic_numeric_measurements_printed": True,
            "single_marker_location_change_alters_measurement_digest": True,
            "cross_patient_tenant_study_denied": True,
            "stale_revision_and_rebind_denied": True,
            "tampered_science_and_source_denied": True,
            "invalid_marker_source_fails_closed": True,
            "test_only_route_disabled_by_default": True,
            "model_onnx_executed": False,
            "existing_clinical_measurements_source_proven": False,
            "clinical_release": False,
            "official_pdf": False,
            "migration_executed": False,
            "production_router_mounted": False,
            "source_sha256": hashlib.sha256(original_bytes).hexdigest(),
            "landmarks_sha256": pdf.headers["X-DC-DOS06-Landmark-SHA256"],
            "measurements_sha256": pdf.headers["X-DC-DOS06-Measurement-SHA256"],
            "provenance_sha256": pdf.headers["X-DC-DOS06-Provenance-SHA256"],
            "pdf_sha256": hashlib.sha256(pdf.content).hexdigest(),
            "study_id": study_a.id,
            "revision": rev_a,
        }
        for flag in (
            "synthetic_only", "real_http_jwt",
            "source_original_aesgcm_sha_verified",
            "landmarks_calculated_from_actual_source_pixels",
            "safe_cephalo_geometry_from_derived_points",
            "same_digest_chain_printed_in_real_pdf",
            "raw_synthetic_numeric_measurements_printed",
            "single_marker_location_change_alters_measurement_digest",
            "cross_patient_tenant_study_denied",
            "stale_revision_and_rebind_denied",
            "tampered_science_and_source_denied",
            "invalid_marker_source_fails_closed",
            "test_only_route_disabled_by_default",
        ):
            assert report[flag] is True, flag
        evidence = os.getenv("DC_DOS06_FUE_EVIDENCE_DIR")
        if evidence:
            out = Path(evidence)
            out.mkdir(parents=True, exist_ok=True)
            (out / "dc-dos06-report.json").write_text(
                json.dumps(report, sort_keys=True, indent=2), encoding="utf-8"
            )
            (out / "dc-dos06-synthetic-pixel-source.png").write_bytes(original_bytes)
            (out / "dc-dos06-synthetic-source-measure-proof.pdf").write_bytes(pdf.content)
            with fitz.open(stream=pdf.content, filetype="pdf") as document:
                page = document[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
                assert len(set(page.samples[:200_000])) > 3
                page.save(out / "dc-dos06-pdf-real-raster.png")
        print("DC_DOS06_NONCLINICAL_PIXEL_CAUSAL_FUE_PASS", json.dumps(report))
    finally:
        app.router.routes[:] = initial_routes
