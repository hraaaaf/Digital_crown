from backend import models


def _payload(email: str) -> dict:
    return {
        "email": email,
        "password": "TestPass123!",
        "nom_complet": "Rejected Team User",
        "role": "SECRETAIRE",
        "permissions": {"agenda": True, "patients": True},
    }


def test_rejected_team_member_cannot_be_reactivated_or_reuse_stale_tokens(
    client, db, auth_headers, dentiste
):
    dentiste.subscription_plan = "ELITE"
    db.commit()
    db.refresh(dentiste)

    password = "TestPass123!"
    created = client.post(
        "/api/team/",
        headers=auth_headers,
        json={**_payload("lot2-rejected@example.com"), "password": password},
    )
    assert created.status_code == 201, created.text
    member_id = created.json()["id"]

    approved = client.post(
        f"/api/team/{member_id}/approve",
        headers=auth_headers,
    )
    assert approved.status_code == 200, approved.text

    client.cookies.clear()
    login = client.post(
        "/api/auth/login",
        data={"username": "lot2-rejected@example.com", "password": password},
    )
    assert login.status_code == 200, login.text
    member_access = login.json()["access_token"]
    member_refresh = login.json()["refresh_token"]

    client.cookies.clear()
    rejected = client.post(
        f"/api/team/{member_id}/reject",
        headers=auth_headers,
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["approval_status"] == "rejected"
    assert rejected.json()["is_active"] is False

    reactivate = client.put(
        f"/api/team/{member_id}",
        headers=auth_headers,
        json={"is_active": True},
    )
    assert reactivate.status_code == 409, reactivate.text

    # Defense in depth for a legacy/corrupt rejected + active row.
    member = db.query(models.User).filter(models.User.id == member_id).first()
    member.is_active = True
    db.commit()

    client.cookies.clear()
    stale_access = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {member_access}"},
    )
    assert stale_access.status_code == 401, stale_access.text

    stale_refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": member_refresh},
    )
    assert stale_refresh.status_code == 401, stale_refresh.text
