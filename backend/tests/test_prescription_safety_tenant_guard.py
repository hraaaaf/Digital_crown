from datetime import date
from unittest.mock import patch

from backend import models
from backend.tests.conftest import make_user


def test_prescription_safety_rejects_cross_tenant_before_service_call(
    client, db, dentiste, auth_headers
):
    other_owner = make_user(db, email="other-tenant-safety@cabinet.ma")
    patient = models.Patient(
        nom="Tenant",
        prenom="Interdit",
        date_naissance=date(1990, 1, 1),
        sexe="M",
        employer_id=other_owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    with patch(
        "backend.routers.prescriptions.prescription_service.check_safety"
    ) as check_safety:
        response = client.post(
            "/api/prescriptions/safety/check",
            json={"patient_id": patient.id, "drug_names": ["Amoxicilline"]},
            headers=auth_headers,
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Accès refusé"
    check_safety.assert_not_called()
