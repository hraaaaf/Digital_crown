"""Regression guards for Document Studio prescription local-first consolidation."""

import pytest

from backend.services.prescription_service import prescription_service


def test_record_usage_propagates_commit_failure(db, dentiste, monkeypatch):
    rollback_called = False
    original_rollback = db.rollback

    def tracked_rollback():
        nonlocal rollback_called
        rollback_called = True
        original_rollback()

    def fail_commit():
        raise RuntimeError("forced usage commit failure")

    monkeypatch.setattr(db, "rollback", tracked_rollback)
    monkeypatch.setattr(db, "commit", fail_commit)

    with pytest.raises(RuntimeError, match="forced usage commit failure"):
        prescription_service.record_medication_usage(
            db,
            dentiste.id,
            "AMOXICILLINE",
            "500 mg",
            "3 fois/jour",
        )

    assert rollback_called is True


def test_unknown_query_never_uses_network(db, dentiste, monkeypatch):
    import urllib.request

    def network_forbidden(*args, **kwargs):
        raise AssertionError("local-first prescription path attempted a network request")

    monkeypatch.setattr(urllib.request, "urlopen", network_forbidden)

    result = prescription_service.get_personalized_suggestions(
        db,
        dentiste.id,
        "R2-NO-NETWORK-MATCH",
    )

    assert result == {"medications": [], "dosages": [], "posologies": []}
