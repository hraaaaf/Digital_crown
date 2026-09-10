"""P5 runtime certification — installment financial invariants.

Isolated from Cephalo work: this file exercises only the canonical installment API
and the shared SQLite test harness.
"""
from datetime import datetime

import pytest


def _make_patient(db, dentiste, nom="P5RUNTIME"):
    from backend import models

    patient = models.Patient(
        nom=nom,
        prenom="Test",
        date_naissance=datetime(1980, 3, 15),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _financial_snapshot(db):
    from backend import models

    return {
        "plans": [
            (row.id, row.patient_id, row.acte_id, row.title, float(row.total_amount), row.created_at, row.updated_at)
            for row in db.query(models.InstallmentPlan).order_by(models.InstallmentPlan.id).all()
        ],
        "installments": [
            (row.id, row.plan_id, row.label, float(row.amount), row.due_date, row.paid_date, row.status, row.notes)
            for row in db.query(models.Installment).order_by(models.Installment.id).all()
        ],
        "payments": [
            (
                row.id,
                row.patient_id,
                float(row.amount),
                row.payment_method,
                row.payment_date,
                row.acte_id,
                row.installment_id,
                row.notes,
                row.validated_by,
            )
            for row in db.query(models.Payment).order_by(models.Payment.id).all()
        ],
    }


def test_preview_is_financially_non_persistent(client, db, auth_headers, dentiste, monkeypatch):
    """Generating a preview must not create or mutate plan/payment state."""
    patient = _make_patient(db, dentiste, "P5PREVIEW")

    # Seed existing financial state so the test detects mutation, not only creation.
    from backend import models

    plan = models.InstallmentPlan(
        patient_id=patient.id,
        title="Existing plan",
        total_amount=300.0,
    )
    db.add(plan)
    db.flush()
    db.add(
        models.Installment(
            plan_id=plan.id,
            label="Existing installment",
            amount=300.0,
            due_date=datetime(2026, 10, 1),
            status="EN_ATTENTE",
        )
    )
    db.commit()

    before = _financial_snapshot(db)

    monkeypatch.setattr(
        "backend.services.generators.installment_receipt_gen.generate_installment_receipt",
        lambda **_: "/tmp/p5-runtime-preview.pdf",
    )

    response = client.post(
        "/api/installments/generate-preview",
        headers=auth_headers,
        json={
            "patient_id": patient.id,
            "title": "Preview only",
            "total_amount": 300.0,
            "items": [
                {
                    "label": "Versement 1",
                    "amount": 300.0,
                    "due_date": "2026-11-01",
                    "paid": False,
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["pdf_url"].endswith("/p5-runtime-preview.pdf")
    db.expire_all()
    assert _financial_snapshot(db) == before


def test_latest_plan_is_deterministic_with_created_at_and_id_tiebreak(client, db, auth_headers, dentiste):
    """latest = created_at DESC, then id DESC when timestamps are equal."""
    patient = _make_patient(db, dentiste, "P5LATEST")
    from backend import models

    plans = [
        models.InstallmentPlan(
            patient_id=patient.id,
            title="Older",
            total_amount=100.0,
            created_at=datetime(2026, 9, 10, 9, 0, 0),
        ),
        models.InstallmentPlan(
            patient_id=patient.id,
            title="Newest tie A",
            total_amount=200.0,
            created_at=datetime(2026, 9, 10, 10, 0, 0),
        ),
        models.InstallmentPlan(
            patient_id=patient.id,
            title="Newest tie B",
            total_amount=300.0,
            created_at=datetime(2026, 9, 10, 10, 0, 0),
        ),
    ]
    db.add_all(plans)
    db.commit()
    for plan in plans:
        db.refresh(plan)

    assert plans[2].id > plans[1].id

    response = client.get(
        f"/api/installments/patient/{patient.id}/latest",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == plans[2].id
    assert body["title"] == "Newest tie B"
    assert body["total_amount"] == 300.0


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": 125.0},
        {"status": "EN_ATTENTE"},
    ],
    ids=["repricing", "reopen"],
)
def test_paid_installment_cannot_be_repriced_or_reopened(client, db, auth_headers, dentiste, payload):
    """A PAYE installment remains immutable without an explicit accounting reversal."""
    patient = _make_patient(db, dentiste, "P5PAID")
    from backend import models

    plan = models.InstallmentPlan(
        patient_id=patient.id,
        title="Paid plan",
        total_amount=100.0,
    )
    db.add(plan)
    db.flush()
    installment = models.Installment(
        plan_id=plan.id,
        label="Paid installment",
        amount=100.0,
        due_date=datetime(2026, 9, 1),
        paid_date=datetime(2026, 9, 2),
        status="PAYE",
        notes="immutable baseline",
    )
    db.add(installment)
    db.commit()
    db.refresh(installment)

    before = (
        float(installment.amount),
        installment.status,
        installment.due_date,
        installment.paid_date,
        installment.label,
        installment.notes,
    )

    response = client.put(
        f"/api/installments/{installment.id}",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 409, response.text
    db.expire_all()
    persisted = db.query(models.Installment).filter(models.Installment.id == installment.id).one()
    after = (
        float(persisted.amount),
        persisted.status,
        persisted.due_date,
        persisted.paid_date,
        persisted.label,
        persisted.notes,
    )
    assert after == before
