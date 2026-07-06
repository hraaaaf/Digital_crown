from datetime import datetime, timedelta


def test_preview_trial_code_success(client, db):
    from backend import models

    code = models.TrialActivationCode(
        code="DC-PREVIEW-01",
        email="preview@cabinet.ma",
        nom_complet="Dr Preview",
        cabinet_name="Cabinet Preview",
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(code)
    db.commit()

    r = client.get("/api/public/trial-code/DC-PREVIEW-01")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "preview@cabinet.ma"
    assert body["trial_days"] == 30


def test_activate_trial_code_creates_active_user_and_uninitialized_cabinet(client, db):
    from backend import models

    code = models.TrialActivationCode(
        code="DC-ACT-0001",
        email="activate@cabinet.ma",
        nom_complet="Dr Activate",
        cabinet_name="Cabinet Activate",
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(code)
    db.commit()

    r = client.post(
        "/api/public/activate-trial",
        json={
            "code": "DC-ACT-0001",
            "email": "activate@cabinet.ma",
            "password": "Pass1234",
            "nom_complet": "Dr Activate",
            "cabinet_name": "Cabinet Activate",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert r.status_code == 200

    user = db.query(models.User).filter(models.User.email == "activate@cabinet.ma").first()
    assert user is not None
    assert user.is_active is True
    assert user.is_licensed is True

    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    assert cabinet is not None
    assert cabinet.is_initialized is False

    db.refresh(code)
    assert code.consumed_at is not None


def test_activate_trial_code_rejects_email_mismatch(client, db):
    from backend import models

    code = models.TrialActivationCode(
        code="DC-MISMATCH-01",
        email="expected@cabinet.ma",
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(code)
    db.commit()

    r = client.post(
        "/api/public/activate-trial",
        json={
            "code": "DC-MISMATCH-01",
            "email": "other@cabinet.ma",
            "password": "Pass1234",
            "nom_complet": "Dr Other",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert r.status_code == 400
