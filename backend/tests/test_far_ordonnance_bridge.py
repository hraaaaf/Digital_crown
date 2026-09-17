from backend.schemas.documents import MedicationItem, OrdonnanceData
from backend.services.far_ordonnance_bridge import (
    build_far_ordonnance_payload,
    patient_requires_far_ordonnance,
)


def test_only_explicit_far_patient_routes_to_far_output():
    assert patient_requires_far_ordonnance(assurance="MUTUELLE_FAR") is True
    assert patient_requires_far_ordonnance(assurance="far") is True
    assert patient_requires_far_ordonnance(assurance="CNSS") is False
    assert patient_requires_far_ordonnance(assurance=None) is False


def test_bridge_copies_explicit_ordonnance_without_inference():
    ordonnance = OrdonnanceData(
        medications=[MedicationItem(
            nom="AMOXICILLINE",
            dosage="1 g",
            forme="comprimé",
            posologie="1 comprimé matin et soir pendant 7 jours",
        )]
    )
    payload = build_far_ordonnance_payload(
        patient_id=12,
        source_ordonnance_document_id=98,
        ordonnance=ordonnance,
    )
    assert payload.patient_id == 12
    assert payload.source_ordonnance_document_id == 98
    assert len(payload.lines) == 1
    assert payload.lines[0].name == "AMOXICILLINE"
    assert payload.lines[0].dosage == "1 g"
    assert payload.lines[0].form == "comprimé"
    assert payload.lines[0].posology == "1 comprimé matin et soir pendant 7 jours"


def test_bridge_requires_archived_source_ordonnance():
    ordonnance = OrdonnanceData(medications=[MedicationItem(nom="PARACETAMOL")])
    try:
        build_far_ordonnance_payload(
            patient_id=12,
            source_ordonnance_document_id=0,
            ordonnance=ordonnance,
        )
    except ValueError as exc:
        assert "archived source ordonnance" in str(exc)
    else:
        raise AssertionError("unarchived ordonnance must fail closed")
