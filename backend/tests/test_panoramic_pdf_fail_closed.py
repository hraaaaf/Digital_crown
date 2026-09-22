"""Fail-closed contract for panoramic PDF presentation."""

from pathlib import Path
from types import SimpleNamespace

from backend.services.generators.panoramic_elite_gen import PanoramicEliteGenerator


def _generator_without_io():
    return object.__new__(PanoramicEliteGenerator)


def test_denture_is_not_inferred_from_missing_annotations():
    generator = _generator_without_io()
    analysis = SimpleNamespace(detections_data={})

    assert generator._documented_denture_type(analysis) == "Non documenté"


def test_explicit_mixed_dentition_is_preserved_as_documented():
    generator = _generator_without_io()
    analysis = SimpleNamespace(detections_data={"global_findings": ["denture_mixte"]})

    assert generator._documented_denture_type(analysis) == "Denture mixte (documentée)"


def test_incomplete_cephalo_metric_is_not_fabricated_with_zeroes():
    generator = _generator_without_io()

    assert generator._prepare_metrics({"SNA": {"valeur": 82.0}}) == []


def test_missing_cephalo_status_is_non_evaluated():
    generator = _generator_without_io()
    metrics = generator._prepare_metrics(
        {"SNA": {"valeur": 82.0, "norm_min": 79.0, "norm_max": 85.0}}
    )

    assert len(metrics) == 1
    assert metrics[0]["status"] == "Unverified"
    assert metrics[0]["status_label"] == "Non évalué"
    assert metrics[0]["valeur"] == "82.0"


def test_explicit_reference_status_is_preserved_without_harmony_claim():
    generator = _generator_without_io()
    metrics = generator._prepare_metrics(
        {
            "SNA": {
                "valeur": 82.0,
                "norm_min": 79.0,
                "norm_max": 85.0,
                "status": "Normal",
            }
        }
    )

    assert metrics[0]["status"] == "Normal"
    assert metrics[0]["status_label"] == "Dans la plage de référence"
    assert "Harmonieux" not in metrics[0]["status_label"]


def test_rendered_pdf_copy_removes_unsupported_clinical_claims():
    generator = _generator_without_io()
    source = """
    <h1>Bilan Radiographique & Clinique</h1>
    <div>Intelligence Artificielle Loki-Silvres v4.0</div>
    <div>Analyse IA Multi-Quadrant</div>
    <h2>Analyse Clinique & Diagnostics</h2>
    <div>Spécialiste en Orthodontie</div>
    <div class="confidentiality-note" style="font-style: italic;">
      Analyse radiologique assistée par ordinateur : aide au diagnostic.
    </div>
    """

    rendered = generator._sanitize_rendered_html(source)

    forbidden = (
        "Bilan Radiographique & Clinique",
        "Intelligence Artificielle Loki-Silvres v4.0",
        "Analyse IA Multi-Quadrant",
        "Analyse Clinique & Diagnostics",
        "Spécialiste en Orthodontie",
        "aide au diagnostic",
        "cryptographiquement signé",
        "Rapport validé numériquement par",
        "Sceau d'Authenticité",
        "Digital Crown Elite Compliance v4.0",
    )
    for token in forbidden:
        assert token not in rendered

    assert "Bilan radiographique panoramique" in rendered
    assert "Repérage dentaire assisté" in rendered
    assert "Observations radiographiques documentées" in rendered
    assert ">Praticien<" in rendered
    assert "L'absence d'annotation ne constitue pas une conclusion de normalité" in rendered
    assert "Aucun diagnostic ni traitement n'est généré automatiquement" in rendered


def test_empty_markdown_fallback_is_observational_not_diagnostic():
    generator = _generator_without_io()
    categories = generator._categorize_findings("")

    assert categories == [
        {
            "name": "Observations radiographiques",
            "findings": ["Aucune observation documentée."],
        }
    ]


def test_raw_template_uses_document_verification_without_signature_overclaim():
    template = Path("backend/templates/panoramic_elite.html").read_text(encoding="utf-8")

    assert "Vérification documentaire" in template
    assert "Praticien associé au dossier" in template
    assert "référence de vérification" in template
    assert "cryptographiquement signé" not in template
    assert "Rapport validé numériquement par" not in template
    assert "Sceau d'Authenticité" not in template
