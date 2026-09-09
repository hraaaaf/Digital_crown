import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.services.clinical_intelligence import (
    ClinicalIntelligenceService,
    MOTIF_CATALOG,
    _resolve_motifs,
)


def _orthodontic_motif_ids():
    return [
        motif_id
        for motif_id, config in MOTIF_CATALOG.items()
        if "ORTHODONTIE" in config.get("specialties", [])
    ]


def test_orthodontic_motif_catalog_contains_no_automatic_acts():
    motif_ids = _orthodontic_motif_ids()
    assert motif_ids
    for motif_id in motif_ids:
        assert not MOTIF_CATALOG[motif_id].get("acts"), motif_id


def test_resolved_orthodontic_motifs_expose_routing_metadata_only():
    resolved = _resolve_motifs(json.dumps(_orthodontic_motif_ids()))
    assert resolved
    assert all("ORTHODONTIE" in motif.get("specialties", []) for motif in resolved)
    assert all(not motif.get("acts") for motif in resolved)


def test_patient_summary_keeps_ortho_specialty_but_emits_no_treatment_hint():
    patient = SimpleNamespace(
        antecedents_medicaux=None,
        motif_consultation=json.dumps(["malocclusion", "aligneurs"]),
        dossier=None,
    )

    db = MagicMock()
    filtered = db.query.return_value.filter.return_value
    filtered.first.return_value = patient
    filtered.order_by.return_value.first.return_value = None
    filtered.order_by.return_value.limit.return_value.all.return_value = []
    filtered.count.return_value = 0

    summary = ClinicalIntelligenceService().get_patient_summary(db, patient_id=1)

    assert "ORTHODONTIE" in summary["motif_specialties"]
    assert summary["motif_treatment_hints"] == []
    serialized = json.dumps(summary, ensure_ascii=False)
    assert "Semestre ODF multibagues" not in serialized
    assert "Gouttière aligneur" not in serialized
