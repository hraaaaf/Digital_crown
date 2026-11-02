"""Céphalo V1 L3: A4 document skin, patient imagery, and safe preview contract."""
from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import fitz
import pytest
from PIL import Image

from backend import schemas
from backend.services import cephalo_pdf_media as media
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator


def _test_vm():
    return schemas.CephaloViewModel(
        patient_nom="PATIENT",
        patient_prenom="TEST",
        patient_age="12",
        patient_id=42,
        analysis=schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="test"),
            metrics=schemas.AnalysisMetrics(),
            visual_debug={}, t1_projection={}, t2_projection={},
        ),
        doctor_name="Dr Test",
        cabinet_config={
            "selected_template": "swiss",
            "primary_color": "#12406B",
            "secondary_color": "#637084",
            "header_lines_fr": ["Dr Test", "Chirurgien Dentiste"],
            "header_lines_ar": [],
            "footer_address": "Adresse cabinet",
            "qr_code_enabled": False,
        },
        is_pre_bilan=True,
    )


def _projection():
    return {
        "contract_version": "CEPHALO_PDF_PROJECTION_V1",
        "patient_id": 42, "analysis_id": 77, "analysis_revision": 3,
        "document_state": "INCOMPLETE",
        "clinical_validation_available": False,
        "clinical_validation_reason": "R14 not persisted",
        "active_runtime_chain_verified": True,
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "measurements": [
            {"measurement_id": "SNA", "value": 81.5, "unit": "deg",
             "availability_status": "AVAILABLE", "method_id": "STEINER",
             "method_version": "1", "scientific_source": "EVIDENCE_GRAPH_V1"},
        ],
        "stages": [
            {"stage_id": "R11", "title": "Diagnostic scientifique",
             "presentation_state": "BLOCKED",
             "summary": "R11 source non persistée", "blocking_gates": ["R11 missing"]},
            {"stage_id": "R13", "title": "Options thérapeutiques",
             "presentation_state": "BLOCKED", "summary": "R13 no clinician option"},
            {"stage_id": "R14", "title": "Validation finale",
             "presentation_state": "BLOCKED", "summary": "R14 cannot sign"},
        ],
    }


def _jpeg():
    image = Image.new("RGB", (120, 90), (240, 240, 240))
    buf = BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def test_cephalo_pdf_renders_real_a4_with_cabinet_skin_and_optional_photos(tmp_path, monkeypatch):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    observed = []
    real_draw = generator.draw_static_elements

    def capture(canvas, doc, *, config=None, user=None):
        observed.append((doc.pagesize, config, user))
        return real_draw(canvas, doc, config=config, user=user)

    monkeypatch.setattr(generator, "draw_static_elements", capture)
    current_user = SimpleNamespace(nom_complet="Dr Test", email="test@example.invalid")
    output = generator.generate(
        _test_vm(), projection=_projection(), user=current_user,
        media={"radio_jpeg": _jpeg(), "photos": [
            {"group": "Extra-buccales", "label": "Face repos", "jpeg": _jpeg()},
            {"group": "Intra-buccales", "label": "Intra frontal", "jpeg": _jpeg()},
        ], "media_unavailable": []},
    )
    with fitz.open(output) as doc:
        assert len(doc) >= 1
        assert all(590 <= page.rect.width <= 600 for page in doc)
        assert all(840 <= page.rect.height <= 850 for page in doc)
        words = "\n".join(page.get_text() for page in doc)
        for label in ("BILAN ORTHODONTIQUE", "SNA", "Face repos",
                      "Intra frontal", "Moulages", "Diagnostic", "Traitement",
                      "R14", "INCOMPLETE"):
            assert label.lower() in words.lower()
        assert "R14 cannot sign" in words
        assert "Dr Test" in words
        assert "R11 source non persistée" in words
        assert "R13 no clinician option" in words
        assert "R14 not persisted" in words
    assert observed
    assert all(config["primary_color"] == "#12406B" for _, config, _ in observed)
    assert all(user is current_user for _, _, user in observed)


def test_client_media_paths_and_oversized_images_fail_closed():
    assert media._authorized_study_radio("https://evil.example/x.png") is None
    assert media._authorized_study_radio("/etc/passwd") is None
    assert media._authorized_study_radio(
        "api/static/uploads/radios/../../tmp/patient.jpg"
    ) is None
    assert media._authorized_study_radio(
        "api/static/uploads/radios/evil.svg"
    ) is None
    with pytest.raises(ValueError):
        media._verified_jpeg(b"not-an-image")


def test_media_reader_is_tenant_scoped_and_uses_only_verifiable_slots(monkeypatch):
    seen = []

    monkeypatch.setattr(
        media, "_authorized_study_radio", lambda _: None,
    )
    monkeypatch.setattr(
        media, "build_ortho_media_record", lambda _db, **kwargs: (
            seen.append(("record", kwargs))
            or {"photo_slots": [
                {"state": "FILLED", "slot_id": "EXTRA_PROFILE",
                 "asset": {"asset_id": 123, "mime_type": "image/jpeg"}},
                {"state": "EMPTY", "slot_id": "INTRA_LEFT", "asset": None},
            ]}
        ),
    )
    monkeypatch.setattr(
        media, "read_clinical_asset_bytes", lambda _db, **kwargs: (
            seen.append(("read", kwargs)) or _jpeg()
        ),
    )
    result = media.load_cephalo_pdf_media(
        object(), employer_id=9, patient_id=42, image_original_path=None,
    )
    assert len(result["photos"]) == 1
    assert result["photos"][0]["slot_id"] == "EXTRA_PROFILE"
    assert seen == [
        ("record", {"employer_id": 9, "patient_id": 42, "timepoint": "T0"}),
        ("read", {"employer_id": 9, "patient_id": 42, "asset_id": 123}),
    ]


def test_unverified_validation_qr_never_generates_doc_temp(tmp_path, monkeypatch):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    vm = _test_vm()
    vm.cabinet_config["qr_code_enabled"] = True
    vm.cabinet_config["qr_code_type"] = "VALIDATION"
    seen = []
    monkeypatch.setattr(
        generator, "draw_static_elements",
        lambda _canvas, _doc, *, config=None, user=None:
            seen.append(dict(config)),
    )
    output = generator.generate(vm, projection=_projection())
    assert output.endswith(".pdf")
    assert seen and all(row["qr_code_enabled"] is False for row in seen)
