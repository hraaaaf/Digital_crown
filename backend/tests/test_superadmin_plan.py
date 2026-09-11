from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.routers import superadmin
from backend.services.subscription_policy import TeamUsage


def _context(current_plan="ELITE"):
    user = MagicMock()
    user.id = 42
    user.email = "cabinet@example.com"
    user.subscription_plan = current_plan

    admin = MagicMock()
    admin.id = 1

    query = MagicMock()
    query.filter.return_value.first.return_value = user
    db = MagicMock()
    db.query.return_value = query
    return db, user, admin


def test_downgrade_is_blocked_when_reserved_team_exceeds_target():
    db, user, admin = _context("ELITE")
    usage = TeamUsage(dentists=2, secretaries=3, pending=1)

    with patch.object(superadmin, "count_reserved_team_usage", return_value=usage):
        with pytest.raises(HTTPException) as exc:
            superadmin.set_client_plan(42, "GOLD", db, admin)

    assert exc.value.status_code == 409
    assert user.subscription_plan == "ELITE"
    db.commit.assert_not_called()


def test_upgrade_to_elite_accepts_large_team_without_device_side_effects():
    db, user, admin = _context("PREMIUM")
    usage = TeamUsage(dentists=50, secretaries=200, pending=10)

    with (
        patch.object(superadmin, "count_reserved_team_usage", return_value=usage),
        patch.object(superadmin, "invalidate_license_cache") as invalidate,
    ):
        result = superadmin.set_client_plan(42, "ELITE", db, admin)

    assert user.subscription_plan == "ELITE"
    assert result == {"status": "success", "subscription_plan": "ELITE"}
    db.commit.assert_called_once()
    invalidate.assert_called_once_with(user.email)
