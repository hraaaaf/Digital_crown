import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

# Import the application graph before importing superadmin directly. The
# superadmin router imports invalidate_license_cache from backend.main.
import backend.main  # noqa: F401
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
        "nom_complet": f"Lot1 {role}",
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
def test_pack_role_capacity_matrix(
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
    """Commercial seat semantics must be exact for every pack and role."""
    _set_plan(db, dentiste, plan)

    for index in range(successful_creates):
        response = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"lot1-{plan.lower()}-{role.lower()}-{index}@example.com", role),
        )
        assert response.status_code == 201, response.text
        assert response.json()["approval_status"] == "pending"
        assert response.json()["is_active"] is False

    quota_response = client.get("/api/team/quota", headers=auth_headers)
    assert quota_response.status_code == 200, quota_response.text
    quota = quota_response.json()

    if role == "DENTISTE":
        assert quota["dentistes_used"] == expected_used
        assert quota["dentistes_max"] == expected_max
    else:
        assert quota["secretaires_used"] == expected_used
        assert quota["secretaires_max"] == expected_max

    if expected_max is None:
        extra = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"lot1-{plan.lower()}-{role.lower()}-extra@example.com", role),
        )
        assert extra.status_code == 201, extra.text
        refreshed = client.get("/api/team/quota", headers=auth_headers).json()
        assert refreshed["can_add_dentiste"] is True
        assert refreshed["can_add_secretaire"] is True
    else:
        blocked = client.post(
            "/api/team/",
            headers=auth_headers,
            json=_payload(f"lot1-{plan.lower()}-{role.lower()}-blocked@example.com", role),
        )
        assert blocked.status_code == 402, blocked.text
        assert f"plan {plan}" in blocked.json()["detail"]


def test_pending_rejection_and_delete_release_reserved_capacity(
    client, db, auth_headers, dentiste
):
    _set_plan(db, dentiste, "GOLD")

    first = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("lot1-gold-assistant-1@example.com"),
    )
    second = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("lot1-gold-assistant-2@example.com"),
    )
    assert first.status_code == second.status_code == 201

    blocked = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("lot1-gold-assistant-3@example.com"),
    )
    assert blocked.status_code == 402

    rejected = client.post(
        f"/api/team/{second.json()['id']}/reject",
        headers=auth_headers,
    )
    assert rejected.status_code == 200, rejected.text

    replacement = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("lot1-gold-assistant-3@example.com"),
    )
    assert replacement.status_code == 201, replacement.text

    deleted = client.delete(
        f"/api/team/{first.json()['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 204, deleted.text

    next_replacement = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload("lot1-gold-assistant-4@example.com"),
    )
    assert next_replacement.status_code == 201, next_replacement.text

    quota = client.get("/api/team/quota", headers=auth_headers).json()
    assert quota["secretaires_used"] == 2
    assert quota["pending_count"] == 2
    assert quota["can_add_secretaire"] is False


@pytest.mark.parametrize("plan", ["GOLD", "PREMIUM", "ELITE"])
def test_approval_and_active_state_changes_preserve_reserved_usage(
    client, db, auth_headers, dentiste, plan
):
    _set_plan(db, dentiste, plan)
    created = client.post(
        "/api/team/",
        headers=auth_headers,
        json=_payload(f"lot1-{plan.lower()}-lifecycle@example.com"),
    )
    assert created.status_code == 201, created.text
    member_id = created.json()["id"]

    before = client.get("/api/team/quota", headers=auth_headers).json()

    approved = client.post(
        f"/api/team/{member_id}/approve",
        headers=auth_headers,
    )
    assert approved.status_code == 200, approved.text

    after_approve = client.get("/api/team/quota", headers=auth_headers).json()
    assert after_approve["secretaires_used"] == before["secretaires_used"]
    assert after_approve["pending_count"] == before["pending_count"] - 1

    suspended = client.put(
        f"/api/team/{member_id}",
        headers=auth_headers,
        json={"is_active": False},
    )
    assert suspended.status_code == 200, suspended.text

    after_suspend = client.get("/api/team/quota", headers=auth_headers).json()
    assert after_suspend["secretaires_used"] == before["secretaires_used"]

    reactivated = client.put(
        f"/api/team/{member_id}",
        headers=auth_headers,
        json={"is_active": True},
    )
    assert reactivated.status_code == 200, reactivated.text

    after_reactivate = client.get("/api/team/quota", headers=auth_headers).json()
    assert after_reactivate["secretaires_used"] == before["secretaires_used"]


def _superadmin_context(current_plan: str):
    user = MagicMock()
    user.id = 42
    user.email = "lot1-pack-matrix@example.com"
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
def test_plan_change_capacity_matrix_is_non_mutating_on_refusal(
    usage, target_plan, expected_status
):
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


def test_unknown_plan_is_rejected_without_mutation():
    db, user, admin = _superadmin_context("PREMIUM")

    with pytest.raises(HTTPException) as exc:
        superadmin.set_client_plan(42, "PLATINUM", db, admin)

    assert exc.value.status_code == 400
    assert user.subscription_plan == "PREMIUM"
    db.commit.assert_not_called()
