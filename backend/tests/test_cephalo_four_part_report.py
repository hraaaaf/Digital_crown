"""Four-part PDF is an unsigned clinical draft, not a technical error dump."""
from pathlib import Path

import fitz

from backend import schemas
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator
from backend.services.generators.cephalo_four_part_report import (
    LAYOUT_VERSION,
    select_verified_measurements,
)


def _vm():
    return schemas.CephaloViewModel(
        patient_nom="SYNTHETIQUE",
        patient_prenom="TEST",
        patient_age="12",
        patient_id=1213,
        analysis=schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="synthetic"),
            metrics=schemas.AnalysisMetrics(),
            visual_debug={},
            t1_projection={},
            t2_projection={},
            clinical_data=schemas.ClinicalData(),
        ),
        doctor_name="Dr Test",
        cabinet_config={
            "selected_template": "swiss",
            "primary_color": "#9B2C88",
            "secondary_color": "#51676F",
            "qr_code_enabled": True,
            "qr_code_type": "VALIDATION",
            "qr_code_value": "DOC-TEMP",
        },
    )


def _projection():
    return {
        "contract_version": "CEPHALO_PDF_PROJECTION_V1",
        "layout_version": LAYOUT_VERSION,
        "document_state": "INCOMPLETE",
        "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
        "active_runtime_chain_verified": True,
        "clinical_validation_available": False,
        "measurements": [
            {
                "measurement_id": "measurement:synthetic:SNA",
                "value": 82.5,
                "unit": "°",
                "availability_status": "AVAILABLE",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": False,
                "calibration_ref": None,
            },
            {
                "measurement_id": "measurement:synthetic:IMPA",
                "value": 88,
                "unit": "°",
                "availability_status": "AVAILABLE",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": False,
                "calibration_ref": None,
            },
            {
                "measurement_id": "measurement:synthetic:Situation_A",
                "value": None,
                "unit": "mm",
                "availability_status": "NOT_COMPUTABLE",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": True,
                "calibration_ref": None,
            },
            {
                "measurement_id": "measurement:synthetic:Wits",
                "value": 15,
                "unit": "mm",
                "availability_status": "AVAILABLE",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": True,
                "calibration_ref": None,
            },
            {
                "measurement_id": "measurement:synthetic:SNB",
                "value": float("nan"),
                "unit": "°",
                "availability_status": "AVAILABLE",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": False,
                "calibration_ref": None,
            },
        ],
        "stages": [{
            "stage_id": "R13",
            "presentation_state": "BLOCKED",
            "summary": "CLIENT_UNTRUSTED_TREATMENT_SHOULD_NOT_RENDER",
            "contradictions": ["CLIENT_UNTRUSTED_TECHNICAL_ERROR_SHOULD_NOT_RENDER"],
        }],
    }


def test_presentation_measures_only_verifiable_typed_values():
    selected = select_verified_measurements(_projection())
    assert selected["dental"] == [("IMPA", "88 °")]
    assert selected["skeletal"] == [("SNA", "82.5 °")]
    assert "Situation A" not in str(selected)
    assert "Wits" not in str(selected)
    assert "nan" not in str(selected)

    unverified = _projection()
    unverified["active_runtime_chain_verified"] = False
    assert select_verified_measurements(unverified) == {"dental": [], "skeletal": []}


def test_production_generate_renders_four_sections_not_debug_dump(tmp_path: Path):
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    path = gen.generate(_vm(), filename="four-part.pdf", projection=_projection())
    pdf = fitz.open(path)
    text = "\n".join(page.get_text("text") for page in pdf)
    expected = [
        "CÉPHALOMÉTRIE ET TRACÉ",
        "EXAMEN DES MOULAGES ET DES IMAGES",
        "BILAN DIAGNOSTIQUE ET DIAGNOSTIC FINAL",
        "PLAN DE TRAITEMENT",
    ]
    assert [text.index(part) for part in expected] == sorted(text.index(part) for part in expected)
    for token in ("82.5", "IMPA", "BROUILLON", "NON SIGNÉ"):
        assert token in text
    for token in (
        "CLIENT_UNTRUSTED_TREATMENT_SHOULD_NOT_RENDER",
        "CLIENT_UNTRUSTED_TECHNICAL_ERROR_SHOULD_NOT_RENDER",
        "DOC-TEMP", "NOT_COMPUTABLE", "Non calculable", "Méthode non précisée",
        "15 mm", "nan",
    ):
        assert token not in text
    assert all(590 <= page.rect.width <= 600 for page in pdf)
    assert all(840 <= page.rect.height <= 850 for page in pdf)


def test_never_promotes_unverified_final_status(tmp_path: Path):
    data = _projection()
    data["document_state"] = "COMPLETE"
    data["clinical_validation_available"] = True
    data["clinical_sections"] = {"diagnosis": "FAKE_DIAGNOSIS", "plan": "FAKE_PLAN"}
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    text = "\n".join(p.get_text("text") for p in fitz.open(gen.generate(
        _vm(), filename="unsigned.pdf", projection=data
    )))
    assert "BROUILLON" in text and "NON SIGNÉ" in text
    assert "FAKE_DIAGNOSIS" not in text
    assert "FAKE_PLAN" not in text


def _synthetic_photo_bytes() -> bytes:
    from io import BytesIO
    from PIL import Image

    output = BytesIO()
    Image.new("RGB", (128, 96), (165, 184, 201)).save(output, format="JPEG")
    return output.getvalue()


def test_media_core_photo_provenance_is_preserved_without_new_storage(monkeypatch):
    from datetime import datetime
    from backend.services import cephalo_pdf_media as media_loader
    from backend.services.ortho_media_record import ORTHO_MEDIA_SCHEMA_VERSION

    recorded = []
    monkeypatch.setattr(media_loader, "build_ortho_media_record", lambda db, **kwargs: {
        "patient_id": kwargs["patient_id"],
        "timepoint": "T0",
        "photo_slots": [{
            "slot_id": "EXTRA_PROFILE",
            "state": "FILLED",
            "asset": {
                "slot_id": "EXTRA_PROFILE",
                "asset_id": 24680,
                "source_kind": "UPLOAD",
                "timepoint": "T0",
                "provenance_schema_version": ORTHO_MEDIA_SCHEMA_VERSION,
                "mime_type": "image/jpeg",
                "captured_at": datetime(2026, 11, 6, 9, 30),
            },
        }],
    })

    def verified_read(db, **kwargs):
        recorded.append(kwargs)
        return _synthetic_photo_bytes()

    monkeypatch.setattr(media_loader, "read_clinical_asset_bytes", verified_read)
    evidence = media_loader.load_cephalo_pdf_media(
        None, employer_id=19, patient_id=1213, image_original_path=None,
    )
    assert evidence["media_unavailable"] == []
    assert recorded == [{"employer_id": 19, "patient_id": 1213, "asset_id": 24680}]
    assert len(evidence["photos"]) == 1
    image = evidence["photos"][0]
    assert (image["asset_id"], image["timepoint"], image["captured_at"]) == (
        24680, "T0", "06/11/2026",
    )
    assert image["group"] == "Extra-buccales"
    assert image["jpeg"].startswith(bytes((0xFF, 0xD8)))


def test_media_core_photo_loader_rejects_wrong_patient_or_unverified_provenance(monkeypatch):
    import pytest
    from datetime import datetime
    from backend.services import cephalo_pdf_media as media_loader
    from backend.services.ortho_media_record import ORTHO_MEDIA_SCHEMA_VERSION

    record = {
        "patient_id": 9999,
        "timepoint": "T0",
        "photo_slots": [],
    }
    monkeypatch.setattr(media_loader, "build_ortho_media_record", lambda *a, **k: record)
    def forbidden(*args, **kwargs):
        raise AssertionError("Unverified asset bytes must never be loaded")
    monkeypatch.setattr(media_loader, "read_clinical_asset_bytes", forbidden)
    with pytest.raises(ValueError, match="identity mismatch"):
        media_loader.load_cephalo_pdf_media(None, employer_id=19, patient_id=1213, image_original_path=None)

    record["patient_id"] = 1213
    record["photo_slots"] = [{
        "slot_id": "INTRA_RIGHT",
        "state": "FILLED",
        "asset": {
            "slot_id": "INTRA_RIGHT",
            "asset_id": 11,
            "source_kind": "UPLOAD",
            "timepoint": "T0",
            "provenance_schema_version": ORTHO_MEDIA_SCHEMA_VERSION,
            "mime_type": "image/png",
            "captured_at": datetime(2026, 11, 6),
        },
    }]
    record["photo_slots"][0]["asset"]["provenance_schema_version"] = "UNVERIFIED"
    evidence = media_loader.load_cephalo_pdf_media(None, employer_id=19, patient_id=1213, image_original_path=None)
    assert evidence["photos"] == []
    assert "INTRA_RIGHT" in evidence["media_unavailable"]


def test_four_part_a4_prints_only_dated_canonical_photos_and_no_asset_identifiers(tmp_path: Path):
    photo = {
        "asset_id": 24680,
        "slot_id": "EXTRA_PROFILE",
        "group": "Extra-buccales",
        "label": "Profil",
        "timepoint": "T0",
        "captured_at": "06/11/2026",
        "jpeg": _synthetic_photo_bytes(),
    }
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    pdf_path = generator.generate(
        _vm(), filename="with-dated-photos.pdf", projection=_projection(),
        media={"radio_jpeg": None, "photos": [photo]},
    )
    with fitz.open(pdf_path) as pdf:
        content = chr(10).join(page.get_text() for page in pdf)
        assert "Profil" in content
        assert "06/11/2026" in content
        assert "T0" in content
        assert "24680" not in content
        assert "BROUILLON" in content and "NON SIGNÉ" in content
        assert all(590 <= page.rect.width <= 600 for page in pdf)
        assert all(840 <= page.rect.height <= 850 for page in pdf)



def test_four_part_a4_displays_only_verified_study_and_revision(tmp_path: Path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    projection = _projection()
    projection["analysis_id"] = 867
    projection["analysis_revision"] = 4
    good = generator.generate(_vm(), filename="study-verified.pdf", projection=projection)
    with fitz.open(good) as doc:
        text = chr(10).join(page.get_text() for page in doc)
    assert "867" in text and "Révision 4" in text

    projection["active_runtime_chain_verified"] = False
    blocked = generator.generate(_vm(), filename="study-unverified.pdf", projection=projection)
    with fitz.open(blocked) as doc:
        text = chr(10).join(page.get_text() for page in doc)
    assert "Révision 4" not in text
    assert "BROUILLON" in text and "NON SIGNÉ" in text



def _clinician_audited_graph():
    """Synthetic graph with individually audited decisions and exact case scope."""
    from dataclasses import replace
    from backend.schemas.cephalo_evidence import (
        ClinicianValidationEvidence, ValidationAction,
    )
    from backend.tests.test_cephalo_evidence_graph import _valid_graph, NOW

    case_id = "cephalo:fourpart-synthetic"
    original = _valid_graph()
    sources = [
        source.model_copy(update={"metadata": {"case_id": case_id}})
        for source in original.sources
    ]
    ids = [
        ("diagnosis", "diagnosis:synthetic"),
        ("problem", "problem:synthetic"),
        ("objective", "objective:synthetic"),
        ("treatment_option", "option:synthetic"),
    ]
    audits = [
        ClinicianValidationEvidence(
            validation_id="validation:extra:" + str(i),
            clinician_id="clinician:1", validated_at=NOW,
            action=ValidationAction.ACCEPT, target_type=kind, target_id=target,
            before_snapshot_hash="synthetic-before",
            after_snapshot_hash="synthetic-after",
        )
        for i, (kind, target) in enumerate(ids)
    ]
    graph = replace(
        original, sources=sources,
        validations=[*original.validations, *audits],
    )
    return graph, case_id


def test_audited_graph_renders_real_confirmed_text_only_in_unsigned_a4(tmp_path: Path):
    from backend.services.cephalo_pdf_clinician_evidence import (
        project_audited_clinician_evidence,
    )

    from dataclasses import replace
    graph, case_id = _clinician_audited_graph()
    option = graph.treatment_options[0].model_copy(update={
        "risks": ["SYNTHETIC_RISK_FROM_SELECTED_OPTION"],
        "limits": ["SYNTHETIC_LIMIT_FROM_SELECTED_OPTION"],
        "benefits": ["SYNTHETIC_BENEFIT_FROM_SELECTED_OPTION"],
    })
    phase = graph.final_plans[0].phases[0].model_copy(update={
        "procedures": ["SYNTHETIC_PROCEDURE_FROM_PLAN"],
    })
    plan = graph.final_plans[0].model_copy(update={"phases": [phase]})
    graph = replace(graph, treatment_options=[option], final_plans=[plan])
    evidence = project_audited_clinician_evidence(
        graph, patient_id=1, case_id=case_id, analysis_id=867, revision=4,
    )
    assert len(evidence["diagnoses"]) == 1
    assert evidence["plan"]["phases"][0]["title"] == "Synthetic phase"
    assert evidence["plan"]["option_context"]["risks"] == ["SYNTHETIC_RISK_FROM_SELECTED_OPTION"]
    assert evidence["report_signed"] is False

    source = _projection()
    source.update({
        "patient_id": 1,
        "analysis_id": 867,
        "analysis_revision": 4,
        "evidence_graph_present": True,
        "clinician_evidence": evidence,
    })
    vm = _vm().model_copy(update={"patient_id": 1})
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    pdf = gen.generate(vm, filename="audited-evidence-unsigned.pdf", projection=source)
    with fitz.open(pdf) as document:
        text = chr(10).join(p.get_text() for p in document)
    assert "Synthetic diagnosis used only to test graph integrity." in text
    assert "Synthetic target" in text
    assert "Synthetic phase" in text
    assert "SYNTHETIC_RISK_FROM_SELECTED_OPTION" in text
    assert "SYNTHETIC_LIMIT_FROM_SELECTED_OPTION" in text
    assert "SYNTHETIC_BENEFIT_FROM_SELECTED_OPTION" in text
    assert "SYNTHETIC_PROCEDURE_FROM_PLAN" in text
    assert "BROUILLON" in text and "NON SIGNÉ" in text


def test_wrong_case_or_missing_clinician_audits_never_promotes_diagnosis(tmp_path: Path):
    import pytest
    from dataclasses import replace
    from backend.services.cephalo_pdf_clinician_evidence import (
        project_audited_clinician_evidence,
    )

    graph, case_id = _clinician_audited_graph()
    with pytest.raises(ValueError):
        project_audited_clinician_evidence(
            graph, patient_id=2, case_id=case_id, analysis_id=867, revision=4,
        )
    with pytest.raises(ValueError):
        project_audited_clinician_evidence(
            graph, patient_id=1, case_id="cephalo:other", analysis_id=867, revision=4,
        )
    with pytest.raises(ValueError):
        project_audited_clinician_evidence(
            replace(graph, validations=graph.validations[:1]),
            patient_id=1, case_id=case_id, analysis_id=867, revision=4,
        )

    source = _projection()
    source.update({
        "patient_id": 1213,
        "analysis_id": 867,
        "analysis_revision": 4,
        "evidence_graph_present": True,
        "clinician_evidence": {
            "version": "CEPHALO_CLINICIAN_PDF_EVIDENCE_V1",
            "patient_id": 2,
            "analysis_id": 867,
            "analysis_revision": 4,
            "report_signed": False,
            "diagnoses": [{"statement": "WRONG_PATIENT_UNVERIFIED_DIAGNOSIS"}],
            "plan": {"phases": [{"title": "WRONG_PATIENT_UNVERIFIED_PLAN"}]},
        },
    })
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    file = gen.generate(_vm(), filename="cross-patient-denied.pdf", projection=source)
    with fitz.open(file) as document:
        text = chr(10).join(p.get_text() for p in document)
    assert "WRONG_PATIENT_UNVERIFIED_DIAGNOSIS" not in text
    assert "WRONG_PATIENT_UNVERIFIED_PLAN" not in text
    assert "NON SIGNÉ" in text



def test_a4_diagnosis_and_treatment_stay_together_after_full_media_gallery(tmp_path: Path):
    from backend.services.cephalo_pdf_clinician_evidence import (
        project_audited_clinician_evidence,
    )

    graph, case_id = _clinician_audited_graph()
    clinical = project_audited_clinician_evidence(
        graph, patient_id=1, case_id=case_id, analysis_id=867, revision=4,
    )
    source = _projection()
    source.update({
        "patient_id": 1,
        "analysis_id": 867,
        "analysis_revision": 4,
        "evidence_graph_present": True,
        "clinician_evidence": clinical,
    })
    photos = []
    for index, slot in enumerate((
        "EXTRA_FRONTAL_REPOSE", "EXTRA_PROFILE", "EXTRA_SMILE",
        "INTRA_FRONTAL", "INTRA_RIGHT", "INTRA_LEFT",
        "INTRA_OCCLUSAL_MAXILLARY", "INTRA_OCCLUSAL_MANDIBULAR",
    )):
        photos.append({
            "slot_id": slot,
            "asset_id": 40000 + index,
            "group": "Extra-buccales" if slot.startswith("EXTRA_") else "Intra-buccales",
            "timepoint": "T0",
            "captured_at": "06/11/2026",
            "label": slot,
            "jpeg": _synthetic_photo_bytes(),
        })
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    file = gen.generate(
        _vm().model_copy(update={"patient_id": 1}),
        filename="audited-page-coherence.pdf",
        projection=source, media={"photos": photos, "radio_jpeg": None},
    )
    with fitz.open(file) as document:
        assert len(document) >= 2
        last_page = document[-1].get_text("text")
        assert "BILAN DIAGNOSTIQUE ET DIAGNOSTIC FINAL" in last_page
        assert "PLAN DE TRAITEMENT" in last_page
        assert "Synthetic diagnosis used only to test graph integrity." in last_page
        assert "Synthetic phase" in last_page
        assert "NON SIGNÉ" in document[0].get_text("text")


def test_four_part_a4_inherits_cabinet_theme_tokens(tmp_path: Path):
    """The A4 content uses the same primary/secondary/accent tokens as the letterhead."""
    vm = _vm().model_copy(update={"cabinet_config": {
        **_vm().cabinet_config,
        "primary_color": "#9B2C88",
        "secondary_color": "#51676F",
        "accent_color": "#198C70",
    }})
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    path = gen.generate(vm, filename="theme-tokens.pdf", projection=_projection())
    spans = []
    with fitz.open(path) as pdf:
        for page in pdf:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans.extend(line.get("spans", []))
    def has_color(text, rgb):
        return any(text in span["text"] and span["color"] == rgb for span in spans)
    assert has_color("BILAN ORTHODONTIQUE", 0x9B2C88)
    assert has_color("Analyse dento-alvéolaire", 0x198C70)
    assert any("BROUILLON" in span["text"] and span["color"] == 0x51676F for span in spans)


def test_four_part_a4_shared_header_footer_logo_and_two_themes(tmp_path: Path, monkeypatch):
    """Synthetic cabinet branding renders on every A4 page across shared templates."""
    from PIL import Image
    from backend.services import base_template_core

    logo = tmp_path / "synthetic-cabinet-logo.png"
    Image.new("RGB", (60, 60), (18, 102, 135)).save(logo)
    monkeypatch.setattr(base_template_core, "get_media_root", lambda: str(tmp_path))
    gen = BilanOrthoPDFGenerator(str(tmp_path))
    palette_cases = (
        ("swiss", "#9B2C88", "#51676F", "#198C70"),
        ("clinical", "#1A566F", "#596873", "#B66A16"),
    )
    for template, primary, secondary, accent in palette_cases:
        vm = _vm().model_copy(update={"cabinet_config": {
            **_vm().cabinet_config,
            "selected_template": template,
            "primary_color": primary,
            "secondary_color": secondary,
            "accent_color": accent,
            "logo_path": logo.name,
            "header_lines_fr": ["Dr Test Cabinet", "Orthodontie de demonstration"],
            "footer_address": "Adresse fictive de test, 10000",
            "footer_phones": "05 00 00 00 00",
        }})
        path = gen.generate(vm, filename=f"branding-{template}.pdf", projection=_projection())
        expected_title_rgb = int(primary[1:], 16)
        with fitz.open(path) as pdf:
            assert len(pdf) >= 1
            assert "BROUILLON" in chr(10).join(page.get_text("text") for page in pdf)
            for page in pdf:
                txt = page.get_text("text")
                assert "Dr Test Cabinet" in txt
                assert "Adresse fictive de test" in txt
                assert "05 00 00 00 00" in txt
                assert page.get_images(full=True), "the shared letterhead must embed the configured logo"
                assert any(
                    span["color"] == expected_title_rgb and "BILAN ORTHODONTIQUE" in span["text"]
                    for block in page.get_text("dict")["blocks"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                ) if "BILAN ORTHODONTIQUE" in txt else True
