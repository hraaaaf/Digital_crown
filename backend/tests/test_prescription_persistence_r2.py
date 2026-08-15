"""R2 regression tests for doctor prescription protocol persistence."""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend import models
from backend.services.prescription_service import PrescriptionService


class TestPrescriptionPreferenceRoundTrip:
    def test_save_list_delete_is_normalized_and_deterministic(self, client, auth_headers):
        payload = {
            "act_code": "   post   extraction   ",
            "drugs": [
                {
                    "name": "AMOXICILLINE",
                    "dosage": "500 mg",
                    "forme": "Gélule",
                    "posologie": "Selon prescription",
                }
            ],
        }

        saved = client.post("/api/prescriptions/preferences", json=payload, headers=auth_headers)
        assert saved.status_code == 200
        assert saved.json()["status"] == "success"

        listed = client.get("/api/prescriptions/habits/presets", headers=auth_headers)
        assert listed.status_code == 200
        matching = [item for item in listed.json() if item["act_context"] == "POST EXTRACTION"]
        assert len(matching) == 1
        assert matching[0]["drugs"][0]["name"] == "AMOXICILLINE"

        deleted = client.delete(
            "/api/prescriptions/preferences/post%20extraction",
            headers=auth_headers,
        )
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "success"

        listed_after = client.get("/api/prescriptions/habits/presets", headers=auth_headers)
        assert listed_after.status_code == 200
        assert all(item["act_context"] != "POST EXTRACTION" for item in listed_after.json())

        missing = client.delete(
            "/api/prescriptions/preferences/post%20extraction",
            headers=auth_headers,
        )
        assert missing.status_code == 404
        assert missing.json()["detail"] == "Preset introuvable"


class TestPrescriptionPreferenceFailures:
    def test_learn_habit_rolls_back_and_propagates_commit_failure(self):
        service = PrescriptionService()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit.side_effect = RuntimeError("db unavailable")

        with pytest.raises(RuntimeError, match="db unavailable"):
            service.learn_habit(
                db,
                doctor_id=42,
                act_code="  endodontie  ",
                drugs=[{"name": "TEST"}],
            )

        db.rollback.assert_called_once()
        added = db.add.call_args.args[0]
        assert isinstance(added, models.DoctorPrescriptionPreference)
        assert added.doctor_id == 42
        assert added.act_code == "ENDODONTIE"

    def test_delete_targets_prescription_preference_and_returns_404_when_absent(self):
        service = PrescriptionService()
        db = MagicMock()
        filtered = db.query.return_value.filter.return_value
        filtered.delete.return_value = 0

        with pytest.raises(HTTPException) as exc:
            service.delete_doctor_preset(db, doctor_id=42, act_code="implant")

        assert exc.value.status_code == 404
        assert exc.value.detail == "Preset introuvable"
        db.query.assert_called_once_with(models.DoctorPrescriptionPreference)
        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_delete_rolls_back_and_propagates_commit_failure(self):
        service = PrescriptionService()
        db = MagicMock()
        db.query.return_value.filter.return_value.delete.return_value = 1
        db.commit.side_effect = RuntimeError("commit failed")

        with pytest.raises(RuntimeError, match="commit failed"):
            service.delete_doctor_preset(db, doctor_id=42, act_code="implant")

        db.rollback.assert_called_once()

    def test_empty_act_code_fails_before_database_mutation(self):
        service = PrescriptionService()
        db = MagicMock()

        with pytest.raises(ValueError, match="Code acte vide"):
            service.learn_habit(db, doctor_id=42, act_code="   ", drugs=[{"name": "TEST"}])

        db.query.assert_not_called()
        db.commit.assert_not_called()
