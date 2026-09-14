"""R17 document-level certification for authoritative cephalometric restitution."""
from __future__ import annotations

from pathlib import Path

import fitz

from backend import schemas
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator


def _vm() -> schemas.CephaloViewModel:
    return schemas.CephaloViewModel(
        patient_nom="CERTIFICATION",
        patient_prenom="R17",
        patient_age="12",
        patient_id=17017,
        analysis=schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="certification"),
            metrics=schemas.AnalysisMetrics(),
            visual_debug={},
            t1_projection={},
            t2_projection={},
            ai_diagnostic=schemas.DiagnosticSLM(
                diagnostic_squelettique="CLIENT_DIAG_SHOULD_NOT_RENDER",
                analyse_moulages="CLIENT_MOULAGES_SHOULD_NOT_RENDER",
                synthese_diagnostique="CLIENT_SYNTHESIS_SHOULD_NOT_RENDER",
                strategie_therapeutique="Damon CLIENT_PLAN_SHOULD_NOT_RENDER",
            ),
            clinical_data=schemas.ClinicalData(
                denture_type="MIXTE",
                preference_technique="DAMON",
                plan_traitement="CLIENT_PLAN_SHOULD_NOT_RENDER",
            ),
        ),
        doctor_name="Dr Certification",
        is_pre_bilan=True,
        validation_warnings=["certification-warning"],
    )


def _projection() -> dict:
    return {
        "contract_version": "CEPHALO_PDF_PROJECTION_V1",
        "document_state": "INCOMPLETE",
        "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
        "active_runtime_chain_verified": True,
        "evidence_graph_present": True,
        "clinical_validation_available": False,
        "clinical_validation_reason": "R14 authority unavailable",
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "measurements": [
            {
                "measurement_id": "SNA",
                "value": 81.5,
                "unit": "deg",
                "availability_status": "AVAILABLE",
                "method_id": "STEINER",
                "method_version": "1",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": False,
                "calibration_ref": None,
            },
            {
                "measurement_id": "Situation_A",
                "value": None,
                "unit": "mm",
                "availability_status": "NOT_COMPUTABLE",
                "method_id": "CRANIOM",
                "method_version": "1",
                "scientific_source": "EVIDENCE_GRAPH_V1",
                "requires_calibration": True,
                "calibration_ref": None,
            },
        ],
        "stages": [
            {
                "stage_id": "R11",
                "title": "Diagnostic scientifique",
                "presentation_state": "BLOCKED",
                "authoritative_status": None,
                "summary": "Diagnostic non promu sans snapshot autoritaire.",
                "blocking_gates": ["r11_authoritative_snapshot_not_persisted"],
                "missing_data_refs": ["source:missing"],
                "contradictions": ["synthetic contradiction"],
                "contraindications": [],
                "provenance": [{"label": "source", "value": "EVIDENCE_GRAPH_V1"}],
            },
            {
                "stage_id": "R13",
                "title": "Options therapeutiques",
                "presentation_state": "BLOCKED",
                "authoritative_status": "BLOCKED",
                "summary": "EVALUABLE n'est jamais une prescription.",
                "blocking_gates": ["r13_authoritative_snapshot_not_persisted"],
                "missing_data_refs": [],
                "contradictions": [],
                "contraindications": ["synthetic contraindication"],
                "provenance": [{"label": "source", "value": "R15_STUDIO"}],
            },
            {
                "stage_id": "R14",
                "title": "Validation clinique finale",
                "presentation_state": "AWAITING_CLINICIAN",
                "authoritative_status": None,
                "summary": "Validation praticien requise.",
                "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
                "missing_data_refs": [],
                "contradictions": [],
                "contraindications": [],
                "provenance": [{"label": "authority", "value": "R13 selection required"}],
            },
        ],
    }


def _required_tokens() -> tuple[str, ...]:
    return (
        "SNA",
        "81.5",
        "NOT_COMPUTABLE",
        "R11",
        "R13",
        "R14",
        "BLOCKED",
        "synthetic contradiction",
        "synthetic contraindication",
        "EVIDENCE_GRAPH_V1",
    )


def _forbidden_tokens() -> tuple[str, ...]:
    return (
        "CLIENT_DIAG_SHOULD_NOT_RENDER",
        "CLIENT_MOULAGES_SHOULD_NOT_RENDER",
        "CLIENT_SYNTHESIS_SHOULD_NOT_RENDER",
        "CLIENT_PLAN_SHOULD_NOT_RENDER",
        "Damon",
        "DAMON",
    )


def _assert_semantics(text: str) -> None:
    for token in _required_tokens():
        assert token in text, f"required semantic missing: {token}"
    for token in _forbidden_tokens():
        assert token not in text, f"legacy/non-authoritative semantic leaked: {token}"


def test_reportlab_pdf_is_real_readable_and_fail_closed(tmp_path: Path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    pdf_path = tmp_path / "r17-reportlab-after.pdf"
    generator._generate_reportlab(_vm(), str(pdf_path), projection=_projection())

    assert pdf_path.exists() and pdf_path.stat().st_size > 5_000
    doc = fitz.open(pdf_path)
    assert len(doc) >= 1

    full_text = "\n".join(page.get_text("text") for page in doc)
    _assert_semantics(full_text)
    assert "INCOMPLETE" in full_text

    for page in doc:
        rect = page.rect
        assert 590 <= rect.width <= 600
        assert 840 <= rect.height <= 850
        text_blocks = [block for block in page.get_text("blocks") if str(block[4]).strip()]
        assert text_blocks, "blank PDF page"
        for x0, y0, x1, y1, *_ in text_blocks:
            assert x0 >= -0.5 and y0 >= -0.5
            assert x1 <= rect.width + 0.5 and y1 <= rect.height + 0.5
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        assert pix.width > 800 and pix.height > 1200


def test_html_and_reportlab_share_the_same_authoritative_semantics(tmp_path: Path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    context = generator._shared_context(_vm(), _projection())
    html = generator.jinja_env.get_template("bilan_ortho_authoritative.html").render(context)

    _assert_semantics(html)
    assert "DOCUMENT CLINIQUE INCOMPLET" in html
    assert "AWAITING_CLINICIAN" in html
    assert "EVALUABLE n'est jamais une prescription" in html
    assert context["measurements"][1]["value"] == "NOT_COMPUTABLE"
    assert context["document_state"] == "INCOMPLETE"
