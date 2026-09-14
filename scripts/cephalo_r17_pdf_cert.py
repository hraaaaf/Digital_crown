from __future__ import annotations

import json
from pathlib import Path

import fitz

from backend import schemas
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator


OUT = Path("artifacts/cephalo-r17-pdf-cert")
OUT.mkdir(parents=True, exist_ok=True)


def vm() -> schemas.CephaloViewModel:
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


def projection() -> dict:
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


def text_and_render(pdf_path: Path, prefix: str) -> tuple[str, list[str]]:
    doc = fitz.open(pdf_path)
    texts = []
    images = []
    for idx, page in enumerate(doc):
        texts.append(page.get_text("text"))
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        png = OUT / f"{prefix}-page-{idx + 1}.png"
        pix.save(png)
        images.append(str(png))
    return "\n".join(texts), images


def assert_semantics(text: str) -> None:
    required = [
        "INCOMPLETE",
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
    ]
    forbidden = [
        "CLIENT_DIAG_SHOULD_NOT_RENDER",
        "CLIENT_MOULAGES_SHOULD_NOT_RENDER",
        "CLIENT_SYNTHESIS_SHOULD_NOT_RENDER",
        "CLIENT_PLAN_SHOULD_NOT_RENDER",
        "Damon",
        "DAMON",
    ]
    for token in required:
        assert token in text, f"required semantic missing from PDF: {token}"
    for token in forbidden:
        assert token not in text, f"legacy/non-authoritative semantic leaked into PDF: {token}"


def main() -> None:
    generator = BilanOrthoPDFGenerator(str(OUT))
    model = projection()
    view = vm()

    html_pdf = OUT / "r17-after-html.pdf"
    reportlab_pdf = OUT / "r17-after-reportlab.pdf"

    generator._generate_weasyprint(view, str(html_pdf), projection=model)
    generator._generate_reportlab(view, str(reportlab_pdf), projection=model)

    html_text, html_images = text_and_render(html_pdf, "html")
    rl_text, rl_images = text_and_render(reportlab_pdf, "reportlab")
    assert_semantics(html_text)
    assert_semantics(rl_text)

    semantic_tokens = [
        "INCOMPLETE",
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
    ]
    parity = {token: (token in html_text and token in rl_text) for token in semantic_tokens}
    assert all(parity.values()), parity

    report = {
        "goal": "HTML and ReportLab render the same authoritative R17 clinical semantics and no legacy client authority",
        "success": "both PDFs render, all essential tokens present in both, all forbidden legacy tokens absent",
        "html_pdf": str(html_pdf),
        "reportlab_pdf": str(reportlab_pdf),
        "html_pages": len(html_images),
        "reportlab_pages": len(rl_images),
        "semantic_parity": parity,
        "forbidden_legacy_absent": True,
        "result": "PASS",
    }
    (OUT / "certification.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
