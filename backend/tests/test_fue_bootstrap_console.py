"""FUE bootstrap contract: expected absence must stay HTTP 200, not console-noisy 401/404."""


def test_workstation_bootstrap_is_quiet_when_anonymous(client):
    client.cookies.clear()
    response = client.get("/api/workstation/bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is False
    assert body["hasClinicConfig"] is False


def test_workstation_bootstrap_reports_missing_then_present_clinic(client, db, auth_headers, dentiste):
    from backend import models

    missing = client.get("/api/workstation/bootstrap", headers=auth_headers)
    assert missing.status_code == 200
    assert missing.json()["authenticated"] is True
    assert missing.json()["hasClinicConfig"] is False

    db.add(models.CabinetConfig(
        owner_id=dentiste.id,
        nom_cabinet="Cabinet FUE",
        nom_praticien="Dr FUE",
        is_initialized=False,
    ))
    db.commit()

    present = client.get("/api/workstation/bootstrap", headers=auth_headers)
    assert present.status_code == 200
    assert present.json()["authenticated"] is True
    assert present.json()["hasClinicConfig"] is True
