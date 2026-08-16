import pytest
from pydantic import ValidationError

from backend.schemas.honoraires import DocumentRequest, HonorairesData, PaymentItem


def _payment(**overrides):
    value = {
        "acte": "Composite 2 faces",
        "dent": "texte libre obsolète",
        "dents": [16],
        "montant": 700,
        "mode_reglement": "Espèces",
    }
    value.update(overrides)
    return value


def _teeth_data(**overrides):
    value = {
        "tooth_number": 16,
        "treatments": [{"code": "COMP2", "name": "Composite 2 faces", "price": 700}],
        "surfaces": ["M", "O"],
        "notes": "Carie profonde",
    }
    value.update(overrides)
    return value


def test_payment_requires_real_act():
    with pytest.raises(ValidationError):
        PaymentItem(**_payment(acte="  "))
    with pytest.raises(ValidationError):
        PaymentItem(**_payment(acte="--- PHASE 1 ---"))


def test_payment_amount_is_fail_closed():
    with pytest.raises(ValidationError):
        PaymentItem(**_payment(montant=-1))
    with pytest.raises(ValidationError):
        PaymentItem(**_payment(montant=1_000_001))
    with pytest.raises(ValidationError):
        PaymentItem(**_payment(montant=float("nan")))


def test_structured_dents_are_validated_sorted_and_deduplicated():
    item = PaymentItem(**_payment(dents=[16, "14", 16]))
    assert item.dents == [14, 16]
    assert item.dent == "14, 16"

    pediatric = PaymentItem(**_payment(dents=[55]))
    assert pediatric.dent == "55"

    with pytest.raises(ValidationError):
        PaymentItem(**_payment(dents=[10]))


def test_payment_method_aliases_are_normalized_and_unknown_rejected():
    assert PaymentItem(**_payment(mode_reglement="CARTE")).mode_reglement == "TPE"
    assert PaymentItem(**_payment(mode_reglement="CHEQUE")).mode_reglement == "Chèque"
    assert PaymentItem(**_payment(mode_reglement="cash")).mode_reglement == "Espèces"
    with pytest.raises(ValidationError):
        PaymentItem(**_payment(mode_reglement="Crypto"))


def test_honoraires_requires_at_least_one_real_line():
    with pytest.raises(ValidationError):
        HonorairesData(payments=[])


def test_honoraires_teeth_data_must_match_tooth_act_and_price():
    valid = HonorairesData(payments=[_payment()], teeth_data=[_teeth_data()])
    assert valid.teeth_data[0].tooth_number == 16

    with pytest.raises(ValidationError):
        HonorairesData(payments=[_payment()], teeth_data=[_teeth_data(tooth_number=17)])

    with pytest.raises(ValidationError):
        HonorairesData(
            payments=[_payment()],
            teeth_data=[_teeth_data(treatments=[{"code": "ENDO", "name": "Endodontie", "price": 700}])],
        )

    with pytest.raises(ValidationError):
        HonorairesData(
            payments=[_payment()],
            teeth_data=[_teeth_data(treatments=[{"code": "COMP2", "name": "Composite 2 faces", "price": 701}])],
        )


def test_unique_honoraires_drops_stale_installments_before_rendering():
    data = HonorairesData(
        payments=[_payment()],
        is_global_note=False,
        installments=[{"label": "Ancienne échéance", "date": "2026-01-01", "amount": 700}],
    )
    assert data.installments == []
    assert data.is_global_note is False


def test_global_honoraires_preserves_and_reconciles_installments():
    data = HonorairesData(
        payments=[_payment(montant=700)],
        is_global_note=True,
        installments=[{"label": "Versement 1", "date": "2026-09-01", "amount": 700}],
    )
    assert data.is_global_note is True
    assert len(data.installments) == 1

    with pytest.raises(ValidationError):
        HonorairesData(
            payments=[_payment(montant=700)],
            is_global_note=True,
            installments=[{"label": "Versement 1", "date": "2026-09-01", "amount": 600}],
        )


def test_document_request_drops_stale_installments_for_unique_note():
    req = DocumentRequest(
        type="note",
        patient_id=1,
        payment_status="EN_ATTENTE",
        data={
            "payments": [_payment()],
            "is_global_note": False,
            "installments": [{"label": "Ancien plan", "date": "2026-01-01", "amount": 700}],
        },
    )
    assert req.data["installments"] == []


def test_document_request_keeps_global_installments_for_existing_reconciliation_guard():
    req = DocumentRequest(
        type="honoraires",
        patient_id=1,
        payment_status="EN_ATTENTE",
        data={
            "payments": [_payment(montant=700)],
            "is_global_note": True,
            "installments": [{"label": "Versement 1", "date": "2026-09-01", "amount": 700}],
        },
    )
    assert len(req.data["installments"]) == 1

    with pytest.raises(ValidationError):
        DocumentRequest(
            type="honoraires",
            patient_id=1,
            payment_status="EN_ATTENTE",
            data={
                "payments": [_payment(montant=700)],
                "is_global_note": True,
                "installments": [{"label": "Versement 1", "date": "2026-09-01", "amount": 600}],
            },
        )
