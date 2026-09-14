"""R17 PDF renderer semantic parity / fail-closed contracts."""
from backend import schemas
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator


def _vm():
    return schemas.CephaloViewModel(
        patient_nom="TEST",
        patient_prenom="Patient",
        patient_age="12",
        patient_id=7,
        analysis=schemas.CephaloAnalysisResult(
            analysis_metadata=schemas.AnalysisMetadata(cohort="test"),
            metrics=schemas.AnalysisMetrics(),
            visual_debug={},
            t1_projection={},
            t2_projection={},
            ai_diagnostic=schemas.DiagnosticSLM(
                diagnostic_squelettique="CLIENT_DIAG",
                analyse_moulages="CLIENT_MOULAGES",
                synthese_diagnostique="CLIENT_SYNTHESIS",
                strategie_therapeutique="Damon CLIENT_PLAN",
            ),
            clinical_data=schemas.ClinicalData(
                denture_type="MIXTE",
                preference_technique="DAMON",
                plan_traitement="CLIENT_PLAN",
            ),
        ),
    )


def _projection():
    return {
        "contract_version": "CEPHALO_PDF_PROJECTION_V1",
        "document_state": "INCOMPLETE",
        "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
        "active_runtime_chain_verified": True,
        "evidence_graph_present": True,
        "clinical_validation_available": False,
        "clinical_validation_reason": "R14 awaiting authority",
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "measurements": [{
            "measurement_id": "measurement:test:Situation_A",
            "value": None,
            "unit": "mm",
            "availability_status": "NOT_COMPUTABLE",
            "method_id": "CRANIOM",
            "method_version": "1",
            "scientific_source": "EVIDENCE_GRAPH_V1",
            "requires_calibration": True,
            "calibration_ref": None,
        }],
        "stages": [{
            "stage_id": "R13",
            "title": "Options thérapeutiques",
            "presentation_state": "BLOCKED",
            "authoritative_status": None,
            "summary": "Évaluable n'est jamais une prescription.",
            "blocking_gates": ["r13_authoritative_snapshot_not_persisted"],
            "missing_data_refs": ["source:missing"],
            "contradictions": ["synthetic contradiction"],
            "contraindications": ["synthetic contraindication"],
            "provenance": [{"label": "source", "value": "EVIDENCE_GRAPH_V1"}],
        }],
    }


def test_shared_renderer_context_uses_projection_not_legacy_narrative(tmp_path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    context = generator._shared_context(_vm(), _projection())

    serialized = str(context)
    assert "CLIENT_DIAG" not in serialized
    assert "CLIENT_SYNTHESIS" not in serialized
    assert "CLIENT_PLAN" not in serialized
    assert "Damon" not in serialized
    assert "DAMON" not in serialized
    assert "Interceptive" not in serialized
    assert context["document_state"] == "INCOMPLETE"
    assert context["measurements"][0]["value"] == "NOT_COMPUTABLE"
    assert context["stages"][0]["presentation_state"] == "BLOCKED"
    assert context["stages"][0]["missing_data_refs"] == ["source:missing"]
    assert context["stages"][0]["contradictions"] == ["synthetic contradiction"]
    assert context["stages"][0]["contraindications"] == ["synthetic contraindication"]


def test_missing_projection_fails_closed_in_generate_contract(tmp_path, monkeypatch):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    captured = {}

    def fake_reportlab(vm, path, *, projection=None):
        captured.update(projection or {})
        return path

    monkeypatch.setattr("backend.services.generators.bilan_ortho_gen.WEASYPRINT_AVAILABLE", False)
    monkeypatch.setattr(generator, "_generate_reportlab", fake_reportlab)

    generator.generate(_vm(), filename="test.pdf")

    assert captured["document_state"] == "INCOMPLETE"
    assert captured["clinical_validation_available"] is False
    assert captured["blocking_gates"] == ["authoritative_pdf_projection_missing"]


def test_html_renderer_autoescapes_authoritative_text(tmp_path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    projection = _projection()
    projection["clinical_validation_reason"] = "<reason&unsafe>"
    projection["stages"][0]["summary"] = "<summary&unsafe>"
    projection["stages"][0]["provenance"] = [
        {"label": "<source>", "value": "<value&unsafe>"}
    ]

    context = generator._shared_context(_vm(), projection)
    html = generator.jinja_env.get_template("bilan_ortho_authoritative.html").render(context)

    assert "<reason&unsafe>" not in html
    assert "<summary&unsafe>" not in html
    assert "<value&unsafe>" not in html
    assert "&lt;reason&amp;unsafe&gt;" in html
    assert "&lt;summary&amp;unsafe&gt;" in html
    assert "&lt;value&amp;unsafe&gt;" in html
