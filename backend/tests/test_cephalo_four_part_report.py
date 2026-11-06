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
