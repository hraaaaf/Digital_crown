"""
Tests unitaires pour la logique quota/approbation d'équipe.
Aucune connexion DB — on teste les helpers purs de routers/team.py.
Exécuter avec : pytest backend/tests/test_team_quota.py -v
"""
import pytest
from unittest.mock import MagicMock
from backend.routers.team import (
    PLAN_QUOTAS,
    sanitize_permissions,
    ALLOWED_TEAM_PERMISSIONS,
    _get_plan,
)


# ── PLAN_QUOTAS structure ─────────────────────────────────────────────────────

class TestPlanQuotas:
    def test_all_plans_present(self):
        for plan in ("GOLD", "PREMIUM", "ELITE"):
            assert plan in PLAN_QUOTAS

    def test_gold_limits(self):
        assert PLAN_QUOTAS["GOLD"]["dentistes"] == 1
        assert PLAN_QUOTAS["GOLD"]["secretaires"] == 2

    def test_premium_limits(self):
        assert PLAN_QUOTAS["PREMIUM"]["dentistes"] == 2
        assert PLAN_QUOTAS["PREMIUM"]["secretaires"] == 6

    def test_elite_is_permissive(self):
        assert PLAN_QUOTAS["ELITE"]["dentistes"] >= 100
        assert PLAN_QUOTAS["ELITE"]["secretaires"] >= 100


# ── _get_plan ─────────────────────────────────────────────────────────────────

class TestGetPlan:
    def _user(self, plan):
        u = MagicMock()
        u.subscription_plan = plan
        return u

    def test_returns_uppercase(self):
        assert _get_plan(self._user("gold")) == "GOLD"
        assert _get_plan(self._user("premium")) == "PREMIUM"

    def test_none_defaults_to_gold(self):
        assert _get_plan(self._user(None)) == "GOLD"

    def test_missing_attr_defaults_to_gold(self):
        u = MagicMock(spec=[])  # no subscription_plan attribute
        assert _get_plan(u) == "GOLD"


# ── sanitize_permissions ──────────────────────────────────────────────────────

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
        defaults = {k: True for k in ALLOWED_TEAM_PERMISSIONS}
        perms = sanitize_permissions(None, defaults)
        assert all(perms[k] is True for k in ALLOWED_TEAM_PERMISSIONS)

    def test_missing_key_defaults_false(self):
        perms = sanitize_permissions({}, {})
        assert all(v is False for v in perms.values())

    def test_all_allowed_permissions_present_in_output(self):
        perms = sanitize_permissions({}, {})
        assert set(perms.keys()) == ALLOWED_TEAM_PERMISSIONS
