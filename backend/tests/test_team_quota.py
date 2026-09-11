"""
Tests unitaires pour la politique de quotas d'equipe.
Aucune connexion DB — on teste les helpers purs.
"""
from unittest.mock import MagicMock

from backend.routers.team import (
    ALLOWED_TEAM_PERMISSIONS,
    _get_plan,
    sanitize_permissions,
)
from backend.services.subscription_policy import (
    TEAM_LIMITS,
    TeamUsage,
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
