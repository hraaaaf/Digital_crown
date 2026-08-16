from backend.schemas.documents import DocumentRequest


def test_devis_strips_shared_installments_before_generation_and_archive():
    request = DocumentRequest(
        type="devis",
        patient_id=42,
        data={
            "items": [
                {
                    "acte": "Couronne",
                    "dent": "16",
                    "prix_unitaire": 3500.0,
                }
            ],
            "installments": [
                {
                    "label": "Ancien plan patient",
                    "date": "2026-09-01",
                    "amount": 3500.0,
                }
            ],
            "is_global_note": True,
        },
    )

    assert request.data["installments"] == []
    assert request.data["is_global_note"] is False


def test_honoraires_keeps_explicit_installments_contract():
    installments = [
        {
            "label": "Versement 1",
            "date": "2026-09-01",
            "amount": 3500.0,
        }
    ]
    request = DocumentRequest(
        type="note",
        patient_id=42,
        data={
            "payments": [
                {
                    "acte": "Couronne",
                    "dent": "16",
                    "montant": 3500.0,
                }
            ],
            "installments": installments,
            "is_global_note": True,
        },
    )

    assert request.data["installments"] == installments
    assert request.data["is_global_note"] is True
