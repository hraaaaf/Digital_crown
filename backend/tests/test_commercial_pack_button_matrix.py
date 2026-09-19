import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from backend import models
from backend.routers import superadmin
from backend.services.subscription_policy import TeamUsage


def _set_plan(db, owner, plan: str) -> None:
    owner.subscription_plan = plan
    db.commit()
    db.refresh(owner)


def _payload(email: str, role: str = "SECRETAIRE") -> dict:
    return {
        "email": email,
        "password": "TestPass123!",
        "nom_complet": f"Test {role}",
        "role": role,
        "permissions": {"agenda": True, "patients": True},
    }


@pytest.mark.parametrize(
    "plan,role,successful_creates,expected_used,expected_max",
    [
        ("GOLD", "DENTISTE", 0, 1, 1),
        ("GOLD", "SECRETAIRE", 2, 2, 2),
        ("PREMIUM", "DENTISTE", 1, 2, 2),
        ("PREMIUM", "SECRETAIRE", 6, 6, 6),
        ("ELITE", "DENTISTE", 5, 6, None),
        ("ELITE", "SECRETAIRE", 8, 8, None),
    ],
)
def test_add_member_button_pack_role_matrix(
    client,
    db,
    auth_headers,
    dentiste,
    plan,
    role,
    successful_creates,
    expected_used,
    expected_max,
):
    """The create-member CTA must obey the exact commercial seat semantics."""

    _set_plan(db, dentiste, plan)

    baseline = client.get("/api/team/quota", headers=auth_headers)
    assert baseline.status_code == 200, baseline.text

    for index in range(successful_creates):
        response = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"{plan.lower()}-{role.lower()}-{index}@example.com", role),
        )
        assert response.status_code == 201, response.text
        assert response.json()["approval_status"] == "pending"
        assert response.json()["is_active"] is False

    quota = client.get("/api/team/quota", headers=auth_headers)
    assert quota.status_code == 200, quota.text
    data = quota.json()

    if role == "DENTISTE":
        assert data["dentistes_used"] == expected_used
        assert data["dentistes_max"] == expected_max
    else:
        assert data["secretaires_used"] == expected_used
        assert data["secretaires_max"] == expected_max

    if expected_max is None:
        extra = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"{plan.lower()}-{role.lower()}-extra@example.com", role),
        )
        assert extra.status_code == 201, extra.text
        refreshed = client.get("/api/team/quota", headers=auth_headers).json()
        assert refreshed["can_add_dentiste"] is True
        assert refreshed["can_add_secretaire"] is True
    else:
        blocked = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"{plan.lower()}-{role.lower()}-blocked@example.com", role),
        )
        assert blocked.status_code == 402, blocked.text
        assert f"plan {plan}" in blocked.json()["detail"]


def test_gold_assistant_reject_button_frees_reserved_seat(
    client, db, auth_headers, dentiste
):
    _set_plan(db, dentiste, "GOLD")

    first = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("gold-assistant-1@example.com"),
    )
    second = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("gold-assistant-2@example.com"),
    )
    assert first.status_code == second.status_code == 201

    blocked = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("gold-assistant-3@example.com"),
    )
    assert blocked.status_code == 402

    rejected = client.post(
        f"/api/team/{second.json()['id']}/reject",
        headers=auth_headers,
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["approval_status"] == "rejected"
    assert rejected.json()["is_active"] is False

    replacement = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("gold-assistant-3@example.com"),
    )
    assert replacement.status_code == 201, replacement.text

    quota = client.get("/api/team/quota", headers=auth_headers).json()
    assert quota["secretaires_used"] == 2
    assert quota["pending_count"] == 2
    assert quota["can_add_secretaire"] is False


def test_premium_delete_button_frees_reserved_seat(
    client, db, auth_headers, dentiste
):
    _set_plan(db, dentiste, "PREMIUM")

    created = []
    for index in range(6):
        response = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"premium-assistant-{index}@example.com"),
        )
        assert response.status_code == 201, response.text
        created.append(response.json())

    blocked = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("premium-assistant-replacement@example.com"),
    )
    assert blocked.status_code == 402

    deleted = client.delete(
        f"/api/team/{created[0]['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 204, deleted.text

    replacement = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("premium-assistant-replacement@example.com"),
    )
    assert replacement.status_code == 201, replacement.text

    quota = client.get("/api/team/quota", headers=auth_headers).json()
    assert quota["secretaires_used"] == 6
    assert quota["can_add_secretaire"] is False


@pytest.mark.parametrize("plan", ["GOLD", "PREMIUM", "ELITE"])
def test_validate_suspend_reactivate_and_permissions_buttons_preserve_reserved_usage(
    client, db, auth_headers, dentiste, plan
):
    _set_plan(db, dentiste, plan)

    created = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload(f"{plan.lower()}-lifecycle@example.com"),
    )
    assert created.status_code == 201, created.text
    member_id = created.json()["id"]

    before = client.get("/api/team/quota", headers=auth_headers).json()

    approved = client.post(
        f"/api/team/{member_id}/approve",
        headers=auth_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["is_active"] is True
    assert approved.json()["approval_status"] == "approved"

    after_approve = client.get("/api/team/quota", headers=auth_headers).json()
    assert after_approve["secretaires_used"] == before["secretaires_used"]
    assert after_approve["pending_count"] == before["pending_count"] - 1

    suspended = client.put(
        f"/api/team/{member_id}",
        headers=auth_headers,
        json={"is_active": False},
    )
    assert suspended.status_code == 200, suspended.text
    assert suspended.json()["is_active"] is False

    after_suspend = client.get("/api/team/quota", headers=auth_headers).json()
    assert after_suspend["secretaires_used"] == before["secretaires_used"]

    reactivated = client.put(
        f"/api/team/{member_id}",
        headers=auth_headers,
        json={"is_active": True},
    )
    assert reactivated.status_code == 200, reactivated.text
    assert reactivated.json()["is_active"] is True

    permissions = client.put(
        f"/api/team/{member_id}",
        headers=auth_headers,
        json={"permissions": {"agenda": False, "patients": True, "root": True}},
    )
    assert permissions.status_code == 200, permissions.text
    assert permissions.json()["permissions"]["agenda"] is False
    assert permissions.json()["permissions"]["patients"] is True
    assert "root" not in permissions.json()["permissions"]


def test_duplicate_create_button_is_fail_closed_and_non_mutating(
    client, db, auth_headers, dentiste
):
    _set_plan(db, dentiste, "ELITE")
    payload = _payload("duplicate-team-member@example.com")

    first = client.post("/api/team/", headers=auth_headers, json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/api/team/", headers=auth_headers, json=payload)
    assert second.status_code == 409, second.text

    quota = client.get("/api/team/quota", headers=auth_headers).json()
    assert quota["secretaires_used"] == 1
    assert quota["pending_count"] == 1


def _superadmin_context(current_plan: str):
    user = MagicMock()
    user.id = 42
    user.email = "pack-matrix@example.com"
    user.subscription_plan = current_plan

    admin = MagicMock()
    admin.id = 1

    query = MagicMock()
    query.filter.return_value.first.return_value = user
    db = MagicMock()
    db.query.return_value = query
    return db, user, admin


@pytest.mark.parametrize(
    "usage,target_plan,expected_status",
    [
        (TeamUsage(dentists=1, secretaries=0, pending=0), "GOLD", 200),
        (TeamUsage(dentists=1, secretaries=2, pending=1), "GOLD", 200),
        (TeamUsage(dentists=2, secretaries=2, pending=1), "GOLD", 409),
        (TeamUsage(dentists=2, secretaries=6, pending=3), "PREMIUM", 200),
        (TeamUsage(dentists=2, secretaries=7, pending=3), "PREMIUM", 409),
        (TeamUsage(dentists=50, secretaries=200, pending=10), "ELITE", 200),
    ],
)
def test_change_pack_button_capacity_matrix(usage, target_plan, expected_status):
    db, user, admin = _superadmin_context("ELITE")

    with (
        patch.object(superadmin, "count_reserved_team_usage", return_value=usage),
        patch.object(superadmin, "invalidate_license_cache"),
        patch.object(superadmin, "add_license_history"),
    ):
        if expected_status == 200:
            result = superadmin.set_client_plan(42, target_plan, db, admin)
            assert result == {"status": "success", "subscription_plan": target_plan}
            assert user.subscription_plan == target_plan
            db.commit.assert_called_once()
        else:
            with pytest.raises(HTTPException) as exc:
                superadmin.set_client_plan(42, target_plan, db, admin)
            assert exc.value.status_code == expected_status
            assert user.subscription_plan == "ELITE"
            db.commit.assert_not_called()


def test_change_pack_button_rejects_unknown_pack_without_mutation():
    db, user, admin = _superadmin_context("PREMIUM")

    with pytest.raises(HTTPException) as exc:
        superadmin.set_client_plan(42, "PLATINUM", db, admin)

    assert exc.value.status_code == 400
    assert user.subscription_plan == "PREMIUM"
    db.commit.assert_not_called()



def test_rejected_team_member_cannot_be_reactivated_or_reuse_stale_tokens(
    client, db, auth_headers, dentiste
):
    """Rejected team identities must stay fail-closed even with stale tokens."""

    _set_plan(db, dentiste, "ELITE")
    password = "TestPass123!"
    created = client.post(
        "/api/team/",
        headers=auth_headers,
        json={
            **_payload("rejected-stale-token@example.com"),
            "password": password,
        },
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
        data={"username": "rejected-stale-token@example.com", "password": password},
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

    # Defense in depth for a legacy/corrupt row that already has the
    # contradictory rejected + active state.
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



def test_renewal_button_without_phone_is_not_reported_as_success():
    db, user, admin = _superadmin_context("GOLD")
    user.telephone_mobile = None
    user.telephone_fixe = None
    user.nom_complet = "Pack Test"

    with (
        patch.object(superadmin, "add_license_history") as history,
        patch.object(superadmin.notification_service, "send_whatsapp_via_whatsmate") as send,
    ):
        with pytest.raises(HTTPException) as exc:
            superadmin.send_renewal_email(
                42,
                superadmin.SendRenewalEmailRequest(message="Renouvellement"),
                db,
                admin,
            )

    assert exc.value.status_code == 409
    assert "Aucun numéro" in exc.value.detail
    send.assert_not_called()
    history.assert_called_once_with(db, 42, 1, "renewal_whatsapp_skipped_no_phone")
    db.commit.assert_called_once()


def test_renewal_button_transport_failure_is_not_reported_as_success():
    db, user, admin = _superadmin_context("PREMIUM")
    user.telephone_mobile = "0600000000"
    user.telephone_fixe = None
    user.nom_complet = "Pack Test"

    with (
        patch.object(superadmin, "add_license_history") as history,
        patch.object(
            superadmin.notification_service,
            "send_whatsapp_via_whatsmate",
            return_value=False,
        ) as send,
    ):
        with pytest.raises(HTTPException) as exc:
            superadmin.send_renewal_email(
                42,
                superadmin.SendRenewalEmailRequest(message="Renouvellement"),
                db,
                admin,
            )

    assert exc.value.status_code == 502
    send.assert_called_once()
    history.assert_called_once_with(db, 42, 1, "renewal_whatsapp_failed")
    db.commit.assert_called_once()


def test_renewal_button_success_requires_confirmed_whatsapp_send():
    db, user, admin = _superadmin_context("ELITE")
    user.telephone_mobile = "0600000000"
    user.telephone_fixe = None
    user.nom_complet = "Pack Test"

    with (
        patch.object(superadmin, "add_license_history") as history,
        patch.object(
            superadmin.notification_service,
            "send_whatsapp_via_whatsmate",
            return_value=True,
        ) as send,
    ):
        result = superadmin.send_renewal_email(
            42,
            superadmin.SendRenewalEmailRequest(message="Renouvellement"),
            db,
            admin,
        )

    assert result["status"] == "success"
    assert "WhatsApp de relance envoyé avec succès" in result["message"]
    send.assert_called_once()
    history.assert_called_once_with(db, 42, 1, "renewal_whatsapp_sent")
    db.commit.assert_called_once()
