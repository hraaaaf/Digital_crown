"""
Tests unitaires pour la politique de quotas d'equipe.
"""
from unittest.mock import MagicMock, patch

from backend import models
from backend.routers.team import (
    ALLOWED_TEAM_PERMISSIONS,
    _build_quota,
    _get_plan,
    sanitize_permissions,
)
from backend.services.subscription_policy import (
    TEAM_LIMITS,
    TeamUsage,
    count_reserved_team_usage,
    exceeds_limit,
    get_team_limits,
    is_limit_reached,
    plan_can_accommodate,
)


class TestPlanQuotas:
    def test_all_plans_present(self):
        for plan in ("GOLD", "PREMIUM", "ELITE"):
            assert plan in TEAM_LIMITS

    def test_gold_limits(self):
        limits = get_team_limits("GOLD")
        assert limits.dentists == 1
        assert limits.secretaries == 2

    def test_premium_limits(self):
        limits = get_team_limits("PREMIUM")
        assert limits.dentists == 2
        assert limits.secretaries == 6

    def test_elite_is_semantically_unlimited(self):
        limits = get_team_limits("ELITE")
        assert limits.dentists is None
        assert limits.secretaries is None
        assert is_limit_reached(10_000, limits.dentists) is False
        assert exceeds_limit(10_000, limits.secretaries) is False

    def test_finite_plan_rejects_reserved_overage(self):
        assert plan_can_accommodate("GOLD", TeamUsage(dentists=2, secretaries=2, pending=1)) is False
        assert plan_can_accommodate("PREMIUM", TeamUsage(dentists=2, secretaries=6, pending=3)) is True

    def test_build_quota_exposes_real_unlimited_semantics(self):
        owner = MagicMock()
        owner.id = 42
        owner.subscription_plan = "ELITE"
        usage = TeamUsage(dentists=17, secretaries=28, pending=4)

        with patch("backend.routers.team.count_reserved_team_usage", return_value=usage):
            quota = _build_quota(owner, MagicMock())

        assert quota.plan == "ELITE"
        assert quota.dentistes_used == 17
        assert quota.dentistes_max is None
        assert quota.secretaires_used == 28
        assert quota.secretaires_max is None
        assert quota.pending_count == 4
        assert quota.can_add_dentiste is True
        assert quota.can_add_secretaire is True

    def test_approved_and_pending_reserve_quota_but_rejected_does_not(self, db):
        owner = models.User(
            email="quota-owner@example.com",
            hashed_password="x",
            role=models.UserRole.DENTISTE,
            approval_status=models.ApprovalStatus.APPROVED.value,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        db.add_all([
            models.User(
                email="quota-approved-dentist@example.com",
                hashed_password="x",
                role=models.UserRole.DENTISTE,
                employer_id=owner.id,
                approval_status=models.ApprovalStatus.APPROVED.value,
                is_active=True,
            ),
            models.User(
                email="quota-pending-assistant@example.com",
                hashed_password="x",
                role=models.UserRole.SECRETAIRE,
                employer_id=owner.id,
                approval_status=models.ApprovalStatus.PENDING.value,
                is_active=False,
            ),
            models.User(
                email="quota-rejected-assistant@example.com",
                hashed_password="x",
                role=models.UserRole.SECRETAIRE,
                employer_id=owner.id,
                approval_status=models.ApprovalStatus.REJECTED.value,
                is_active=False,
            ),
        ])
        db.commit()

        usage = count_reserved_team_usage(db, owner.id)

        assert usage.dentists == 2  # owner + approved associate
        assert usage.secretaries == 1  # pending reserves the seat
        assert usage.pending == 1


class TestGetPlan:
    def _user(self, plan):
        user = MagicMock()
        user.subscription_plan = plan
        return user

    def test_returns_uppercase(self):
        assert _get_plan(self._user("gold")) == "GOLD"
        assert _get_plan(self._user("premium")) == "PREMIUM"

    def test_none_defaults_to_gold(self):
        assert _get_plan(self._user(None)) == "GOLD"

    def test_missing_attr_defaults_to_gold(self):
        user = MagicMock(spec=[])
        assert _get_plan(user) == "GOLD"


class TestSanitizePermissions:
    def test_keeps_only_allowed_keys(self):
        perms = sanitize_permissions({"agenda": True, "root": True}, {})
        assert "root" not in perms
        assert set(perms.keys()) == ALLOWED_TEAM_PERMISSIONS

    def test_coerces_to_bool(self):
        perms = sanitize_permissions({"agenda": 1, "patients": 0}, {})
        assert perms["agenda"] is True
        assert perms["patients"] is False

    def test_none_uses_defaults(self):
        defaults = {key: True for key in ALLOWED_TEAM_PERMISSIONS}
        perms = sanitize_permissions(None, defaults)
        assert all(perms[key] is True for key in ALLOWED_TEAM_PERMISSIONS)

    def test_missing_key_defaults_false(self):
        perms = sanitize_permissions({}, {})
        assert all(value is False for value in perms.values())

    def test_all_allowed_permissions_present_in_output(self):
        perms = sanitize_permissions({}, {})
        assert set(perms.keys()) == ALLOWED_TEAM_PERMISSIONS
