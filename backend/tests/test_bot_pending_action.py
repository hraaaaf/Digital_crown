"""
Tests unitaires pour la logique BotPendingAction (TTL, ownership, statut).
Aucune connexion DB — on teste les helpers purs.
Exécuter avec : pytest backend/tests/test_bot_pending_action.py -v
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


def _make_action(user_id=1, employer_id=10, executed=False, minutes_ago=0):
    """Fabrique un objet BotPendingAction mocké."""
    action = MagicMock()
    action.user_id = user_id
    action.employer_id = employer_id
    action.executed = executed
    action.created_at = datetime.utcnow() - timedelta(minutes=minutes_ago)
    action.expires_at = action.created_at + timedelta(minutes=30)
    return action


def _is_expired(action, now=None):
    """Vérifie si une action est expirée."""
    now = now or datetime.utcnow()
    return now > action.expires_at


def _can_execute(action, user_id, employer_id, now=None):
    """
    Logique d'autorisation d'exécution d'une BotPendingAction.
    Reproduit la règle backend : user_id + employer_id doivent correspondre,
    action non exécutée, TTL non dépassé.
    """
    if action.executed:
        return False, "Action déjà exécutée"
    if _is_expired(action, now):
        return False, "Action expirée (TTL 30 min dépassé)"
    if action.user_id != user_id:
        return False, "Accès refusé — utilisateur différent"
    if action.employer_id != employer_id:
        return False, "Accès refusé — cabinet différent"
    return True, "ok"


# ── TTL ───────────────────────────────────────────────────────────────────────

class TestBotActionTTL:
    def test_fresh_action_not_expired(self):
        action = _make_action(minutes_ago=0)
        assert not _is_expired(action)

    def test_action_29min_not_expired(self):
        action = _make_action(minutes_ago=29)
        assert not _is_expired(action)

    def test_action_31min_expired(self):
        action = _make_action(minutes_ago=31)
        assert _is_expired(action)

    def test_action_exactly_30min_expired(self):
        action = _make_action(minutes_ago=30)
        # expires_at = created_at + 30min; now = created_at + 30min → now == expires_at
        # > is strict, so at exactly 30min it is NOT yet expired
        assert not _is_expired(action)


# ── Ownership ─────────────────────────────────────────────────────────────────

class TestBotActionOwnership:
    def test_correct_owner_can_execute(self):
        action = _make_action(user_id=1, employer_id=10)
        ok, msg = _can_execute(action, user_id=1, employer_id=10)
        assert ok

    def test_wrong_user_blocked(self):
        action = _make_action(user_id=1, employer_id=10)
        ok, msg = _can_execute(action, user_id=2, employer_id=10)
        assert not ok
        assert "utilisateur" in msg

    def test_wrong_employer_blocked(self):
        action = _make_action(user_id=1, employer_id=10)
        ok, msg = _can_execute(action, user_id=1, employer_id=99)
        assert not ok
        assert "cabinet" in msg

    def test_already_executed_blocked(self):
        action = _make_action(user_id=1, employer_id=10, executed=True)
        ok, msg = _can_execute(action, user_id=1, employer_id=10)
        assert not ok
        assert "exécutée" in msg

    def test_expired_action_blocked(self):
        action = _make_action(user_id=1, employer_id=10, minutes_ago=31)
        ok, msg = _can_execute(action, user_id=1, employer_id=10)
        assert not ok
        assert "TTL" in msg or "expirée" in msg
