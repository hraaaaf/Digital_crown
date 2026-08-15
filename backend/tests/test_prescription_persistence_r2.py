"""R2 regression tests for deterministic, local-first prescription persistence."""

import pytest

from backend import models
from backend.services.prescription_service import prescription_service


class TestPersonalPresetLifecycle:
    def test_api_save_load_delete_cycle(self, client, db, auth_headers, dentiste):
        act_code = "R2_EXTRACTION"
        payload = {
            "act_code": act_code,
            "drugs": [
                {
                    "name": "AMOXICILLINE",
                    "dosage": "500 mg",
                    "forme": "Gélule",
                    "posologie": "3 fois/jour",
                }
            ],
        }

        saved = client.post(
            "/api/prescriptions/preferences",
            json=payload,
            headers=auth_headers,
        )
        assert saved.status_code == 200
        assert saved.json()["status"] == "success"

        persisted = (
            db.query(models.DoctorPrescriptionPreference)
            .filter(
                models.DoctorPrescriptionPreference.doctor_id == dentiste.id,
                models.DoctorPrescriptionPreference.act_code == act_code,
            )
            .first()
        )
        assert persisted is not None
        assert persisted.drugs_json[0]["name"] == "AMOXICILLINE"

        loaded = client.get(
            "/api/prescriptions/habits/presets",
            headers=auth_headers,
        )
        assert loaded.status_code == 200
        assert any(item["act_context"] == act_code for item in loaded.json())

        deleted = client.delete(
            f"/api/prescriptions/preferences/{act_code}",
            headers=auth_headers,
        )
        assert deleted.status_code == 200

        db.expire_all()
        remaining = (
            db.query(models.DoctorPrescriptionPreference)
            .filter(
                models.DoctorPrescriptionPreference.doctor_id == dentiste.id,
                models.DoctorPrescriptionPreference.act_code == act_code,
            )
            .count()
        )
        assert remaining == 0

        reloaded = client.get(
            "/api/prescriptions/habits/presets",
            headers=auth_headers,
        )
        assert reloaded.status_code == 200
        assert all(item["act_context"] != act_code for item in reloaded.json())

    def test_delete_is_scoped_to_current_doctor(self, db, dentiste):
        act_code = "R2_SCOPED"
        prescription_service.learn_habit(
            db,
            dentiste.id,
            act_code,
            [{"name": "PARACETAMOL", "dosage": "1 g"}],
        )

        deleted = prescription_service.delete_doctor_preset(
            db,
            dentiste.id + 999999,
            act_code,
        )
        assert deleted == 0
        assert (
            db.query(models.DoctorPrescriptionPreference)
            .filter(
                models.DoctorPrescriptionPreference.doctor_id == dentiste.id,
                models.DoctorPrescriptionPreference.act_code == act_code,
            )
            .count()
            == 1
        )


class TestPersistenceFailureVisibility:
    def test_learn_habit_propagates_commit_failure(self, db, dentiste, monkeypatch):
        rollback_called = False
        original_rollback = db.rollback

        def tracked_rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()

        def fail_commit():
            raise RuntimeError("forced R2 commit failure")

        monkeypatch.setattr(db, "rollback", tracked_rollback)
        monkeypatch.setattr(db, "commit", fail_commit)

        with pytest.raises(RuntimeError, match="forced R2 commit failure"):
            prescription_service.learn_habit(
                db,
                dentiste.id,
                "R2_FAIL",
                [{"name": "AMOXICILLINE"}],
            )

        assert rollback_called is True

    def test_record_usage_propagates_commit_failure(self, db, dentiste, monkeypatch):
        rollback_called = False
        original_rollback = db.rollback

        def tracked_rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()

        def fail_commit():
            raise RuntimeError("forced R2 usage failure")

        monkeypatch.setattr(db, "rollback", tracked_rollback)
        monkeypatch.setattr(db, "commit", fail_commit)

        with pytest.raises(RuntimeError, match="forced R2 usage failure"):
            prescription_service.record_medication_usage(
                db,
                dentiste.id,
                "AMOXICILLINE",
                "500 mg",
                "3 fois/jour",
            )

        assert rollback_called is True


class TestLocalFirstSuggestions:
    def test_unknown_query_does_not_use_network(self, db, dentiste, monkeypatch):
        import urllib.request

        def network_forbidden(*args, **kwargs):
            raise AssertionError("R2 local-first path attempted a network request")

        monkeypatch.setattr(urllib.request, "urlopen", network_forbidden)

        result = prescription_service.get_personalized_suggestions(
            db,
            dentiste.id,
            "R2-NO-NETWORK-MATCH",
        )

        assert result == {"medications": [], "dosages": [], "posologies": []}
