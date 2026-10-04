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


def test_steiner_protocol_renderer_preserves_display_only_reference_contract(tmp_path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    projection = _projection()
    projection["protocol_profiles"] = {
        "steiner": {
            "protocol_profile_id": "STEINER_STATIC_PROTOCOL_PROFILE_V1",
            "source_lock_gate": {"status": "SATISFIED"},
            "final_gate": {"status": "OPEN"},
            "norm_set": {
                "authority": "REFERENCE_DISPLAY_ONLY",
                "applicability": "NOT_VALIDATED_FOR_UNIVERSAL_MODERN_USE",
            },
            "rows": [{
                "canonical_measurement_id": "M_SNA_DEG_V1",
                "label": "SNA",
                "layer": "STEINER_1953_BASE",
                "value": 83.5,
                "unit": "\u00b0",
                "availability_status": "AVAILABLE",
                "historical_reference": 82.0,
                "reference_delta": 1.5,
                "reference_authority": "REFERENCE_DISPLAY_ONLY",
                "interpretation_status": "REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION",
            }],
        }
    }
    context = generator._shared_context(_vm(), projection)
    steiner = context["steiner_protocol"]
    assert steiner["protocol_profile_id"] == "STEINER_STATIC_PROTOCOL_PROFILE_V1"
    assert steiner["norm_set"]["authority"] == "REFERENCE_DISPLAY_ONLY"
    assert steiner["rows"][0]["value"].startswith("83.5")
    assert steiner["rows"][0]["reference"].startswith("82")
    assert steiner["rows"][0]["delta"].startswith("1.5")
    html = generator.jinja_env.get_template("bilan_ortho_authoritative.html").render(context)
    assert "Analyse protocolaire Steiner" in html
    assert "classification clinique universelle" in html
    assert "REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION" not in html
    assert "aucune classification clinique" in html


def test_reportlab_renderer_contains_steiner_protocol_section():
    import inspect
    source = inspect.getsource(BilanOrthoPDFGenerator._generate_reportlab)
    assert 'context["steiner_protocol"]' in source
    assert 'Analyse protocolaire Steiner' in source
    assert 'protocol_table = Table' in source


def test_reportlab_steiner_wording_preserves_clinical_safety_semantics():
    import inspect
    row = BilanOrthoPDFGenerator._protocol_row_display({
        "availability_status": "AVAILABLE",
        "value": 83.5,
        "unit": "°",
        "historical_reference": 82.0,
        "reference_delta": 1.5,
        "interpretation_status": "REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION",
    })
    assert row["interpretation_status"] == "Référence historique — aucune classification clinique"
    source = inspect.getsource(BilanOrthoPDFGenerator._generate_reportlab)
    assert "Références historiques affichées à titre comparatif uniquement" in source
    assert "non vérifié" in source
    assert "Réf. hist." in source
    assert "Écart réf." in source
    assert "R?f" not in source
    assert "v?rifi" not in source


def test_tweed_merrifield_renderer_preserves_dc_variant_without_fake_norms(tmp_path):
    generator = BilanOrthoPDFGenerator(str(tmp_path))
    projection = _projection()
    projection["protocol_profiles"] = {
        "tweed_merrifield": {
            "protocol_profile_id": "TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1",
            "source_lock_gate": {"status": "SATISFIED"},
            "final_gate": {"status": "OPEN"},
            "reference_contexts": [{"authority": "HISTORICAL_CONTEXT_ONLY"}],
            "rows": [{
                "canonical_measurement_id": "M_FH_GOME_DEG_V1",
                "label": "FMA",
                "profile_section": "TWEED_DC_DIAGNOSTIC_TRIANGLE_V1",
                "value": 24.5,
                "unit": "deg",
                "availability_status": "AVAILABLE",
                "reference_authority": "CONTEXT_ONLY_NO_RUNTIME_DELTA",
                "classification_authority": False,
                "interpretation_status": "RAW_MEASUREMENT_WITH_SOURCE_CONTEXT_ONLY",
            }],
        }
    }
    context = generator._shared_context(_vm(), projection)
    tweed = context["tweed_merrifield_protocol"]
    assert tweed["protocol_profile_id"] == "TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1"
    assert tweed["rows"][0]["value"] == "24.5 deg"
    assert tweed["rows"][0]["reference_authority"] == "CONTEXT_ONLY_NO_RUNTIME_DELTA"
    html = generator.jinja_env.get_template("bilan_ortho_authoritative.html").render(context)
    assert "Analyse protocolaire Tweed–Merrifield" in html
    assert "Variante Digital Crown Po-Or/Go-Me" in html
    assert "Aucune équivalence géométrique stricte avec Tweed 1954" in html
    assert "non classificatoires" in html.lower()


def test_reportlab_tweed_merrifield_wording_preserves_variant_and_clinician_authority():
    import inspect
    source = inspect.getsource(BilanOrthoPDFGenerator._generate_reportlab)
    assert 'context["tweed_merrifield_protocol"]' in source
    assert "Analyse protocolaire Tweed–Merrifield" in source
    assert "Variante Digital Crown Po-Or/Go-Me" in source
    assert "aucune équivalence géométrique stricte avec Tweed 1954" in source
    assert "aucune classification automatique" in source
