"""Pocket Frontdesk: paired-device boundary and tenant-safe transitions."""
from datetime import datetime, timedelta

from backend import models, schemas
from backend.tests.test_mobile_pocket_security_boundary import _claim_mobile, _user


def test_pocket_frontdesk_requires_paired_device_and_enforces_tenant(client, db, dentiste):
    assistant = _user(
        db,
        email="pocket-frontdesk-mobile@cabinet.ma",
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={"agenda": True, "patients": True, "clinical": False},
    )
    other = _user(
        db,
        email="pocket-frontdesk-other@cabinet.ma",
        role=models.UserRole.DENTISTE,
        permissions={"agenda": True, "patients": True},
    )
    own = models.Appointment(
        patient_name="Own Cabinet Request",
        datetime_start=datetime.utcnow() + timedelta(days=3),
        duration_minutes=30,
        status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
        employer_id=dentiste.id,
    )
    foreign = models.Appointment(
        patient_name="Other Cabinet Request",
        datetime_start=datetime.utcnow() + timedelta(days=3),
        duration_minutes=30,
        status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
        employer_id=other.id,
    )
    db.add_all([own, foreign])
    db.commit()
    db.refresh(own)
    db.refresh(foreign)

    # An unpaired browser cannot inspect pending names at all.
    assert client.get("/api/mobile/frontdesk/pending").status_code in (401, 422)
    jwt = _claim_mobile(client, db, dentiste, assistant)
    headers = {"Authorization": f"Bearer {jwt}"}

    # The mobile token must never gain desktop auth, even with agenda permission.
    assert client.get("/api/appointments/pending", headers=headers).status_code == 401
    pending = client.get("/api/mobile/frontdesk/pending", headers=headers)
    assert pending.status_code == 200, pending.text
    ids = {row["id"] for row in pending.json()}
    assert own.id in ids
    assert foreign.id not in ids

    assert client.post(
        f"/api/mobile/frontdesk/requests/{foreign.id}/confirm", headers=headers
    ).status_code == 404
    assert client.post(
        f"/api/mobile/frontdesk/requests/{own.id}/invalid", headers=headers
    ).status_code == 404

    confirmed = client.post(
        f"/api/mobile/frontdesk/requests/{own.id}/confirm", headers=headers
    )
    assert confirmed.status_code == 200, confirmed.text
    db.refresh(own)
    assert own.status == schemas.AppointmentStatus.CONFIRME
    assert own.confirmed_by_id == assistant.id

    # Revoked device gets a hard denial, not a desktop fallthrough.
    device = db.query(models.MobilePairedDevice).filter(
        models.MobilePairedDevice.user_id == assistant.id
    ).first()
    assert device is not None
    device.revoked_at = datetime.utcnow()
    db.commit()
    assert client.get("/api/mobile/frontdesk/pending", headers=headers).status_code == 401


def test_mobile_frontdesk_fails_closed_after_agenda_permission_revoked(client, db, dentiste):
    assistant = _user(
        db,
        email="pocket-frontdesk-revoked@cabinet.ma",
        role=models.UserRole.SECRETAIRE,
        employer_id=dentiste.id,
        permissions={"agenda": True, "patients": True},
    )
    jwt = _claim_mobile(client, db, dentiste, assistant)
    headers = {"Authorization": f"Bearer {jwt}"}
    assert client.get("/api/mobile/frontdesk/pending", headers=headers).status_code == 200

    assistant.permissions = {"agenda": False, "patients": True}
    db.commit()
    assert client.get("/api/mobile/frontdesk/pending", headers=headers).status_code == 403
    assert client.post("/api/mobile/frontdesk/requests/1/confirm", headers=headers).status_code == 403
