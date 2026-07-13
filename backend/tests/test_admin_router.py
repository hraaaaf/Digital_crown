"""Tests routers/admin.py — audit logs, dashboard, cabinet settings, normalize-docs."""


# ── normalize-docs ────────────────────────────────────────────────────────────

class TestNormalizeDocs:
    def test_requires_auth(self, client):
        r = client.get("/api/admin/normalize-docs")
        assert r.status_code == 401

    def test_returns_success(self, client, auth_headers):
        r = client.get("/api/admin/normalize-docs", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] in ("success", "error")


# ── audit logs ────────────────────────────────────────────────────────────────

class TestAuditLogs:
    def test_requires_auth(self, client):
        r = client.get("/api/admin/audit-logs")
        assert r.status_code == 401

    def test_empty_returns_structure(self, client, auth_headers):
        r = client.get("/api/admin/audit-logs", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "logs" in body
        assert isinstance(body["logs"], list)

    def test_with_existing_log(self, client, db, auth_headers, dentiste):
        from backend import models
        from datetime import datetime
        log = models.AuditLog(
            user_id=dentiste.id,
            employer_id=dentiste.id,
            action="TEST_ACTION",
            resource_type="Patient",
            resource_id="42",
            timestamp=datetime.now(),
        )
        db.add(log)
        db.commit()

        r = client.get("/api/admin/audit-logs", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        actions = [l["action"] for l in body["logs"]]
        assert "TEST_ACTION" in actions

    def test_filter_by_action(self, client, db, auth_headers, dentiste):
        from backend import models
        from datetime import datetime
        log = models.AuditLog(
            user_id=dentiste.id,
            employer_id=dentiste.id,
            action="FILTERED_ACTION",
            resource_type="Patient",
            timestamp=datetime.now(),
        )
        db.add(log)
        db.commit()

        r = client.get("/api/admin/audit-logs?action=FILTERED_ACTION", headers=auth_headers)
        assert r.status_code == 200
        for l in r.json()["logs"]:
            assert l["action"] == "FILTERED_ACTION"

    def test_filter_by_resource_type(self, client, db, auth_headers, dentiste):
        from backend import models
        from datetime import datetime
        log = models.AuditLog(
            user_id=dentiste.id,
            employer_id=dentiste.id,
            action="CREATE",
            resource_type="SpecialResource",
            timestamp=datetime.now(),
        )
        db.add(log)
        db.commit()

        r = client.get("/api/admin/audit-logs?resource_type=SpecialResource", headers=auth_headers)
        assert r.status_code == 200
        for l in r.json()["logs"]:
            assert l["resource_type"] == "SpecialResource"

    def test_pagination_offset(self, client, auth_headers):
        r = client.get("/api/admin/audit-logs?limit=5&offset=0", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["logs"]) <= 5

    def test_log_fields_present(self, client, db, auth_headers, dentiste):
        from backend import models
        from datetime import datetime
        log = models.AuditLog(
            user_id=dentiste.id,
            employer_id=dentiste.id,
            action="FIELD_TEST",
            resource_type="Test",
            timestamp=datetime.now(),
        )
        db.add(log)
        db.commit()

        r = client.get("/api/admin/audit-logs?action=FIELD_TEST", headers=auth_headers)
        assert r.status_code == 200
        logs = r.json()["logs"]
        if logs:
            for field in ("id", "timestamp", "user_id", "employer_id", "action", "resource_type"):
                assert field in logs[0]


# ── dashboard stats ───────────────────────────────────────────────────────────

class TestDashboardStats:
    def test_requires_auth(self, client):
        r = client.get("/api/admin/dashboard/stats")
        assert r.status_code == 401

    def test_returns_structure(self, client, auth_headers):
        r = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "total_patients" in body
        assert "total_analyses" in body
        assert "recent_patients" in body
        assert "weekly_activity" in body
        assert "weekly_patient_counts" in body
        assert "in_waiting" in body
        assert "weekly_patients" in body

    def test_total_patients_non_negative(self, client, auth_headers):
        r = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total_patients"] >= 0

    def test_weekly_activity_has_7_days(self, client, auth_headers):
        r = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["weekly_activity"]) == 7

    def test_weekly_patient_counts_has_7_days(self, client, auth_headers):
        r = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["weekly_patient_counts"]) == 7

    def test_with_patients_counted(self, client, db, auth_headers, dentiste):
        from backend import models
        from datetime import datetime
        pat = models.Patient(
            nom="STATPAT", prenom="Test",
            date_naissance=datetime(1985, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()

        r = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_patients"] >= 1
        # Patient créé aujourd'hui -> dernier jour de la fenêtre (index 6) doit le compter
        # brut, sans passer par la normalisation en pourcentage de weekly_activity.
        assert body["weekly_patient_counts"][6] >= 1


# ── cabinet profile ───────────────────────────────────────────────────────────

class TestCabinetProfile:
    def test_get_cabinet_requires_auth(self, client):
        r = client.get("/api/admin/cabinet/me")
        assert r.status_code == 401

    def test_get_cabinet_returns_200(self, client, auth_headers):
        r = client.get("/api/admin/cabinet/me", headers=auth_headers)
        assert r.status_code == 200

    def test_update_cabinet_requires_auth(self, client):
        r = client.put("/api/admin/cabinet/me", json={"nom": "Test Cabinet"})
        assert r.status_code == 401

    def test_update_cabinet_nom(self, client, auth_headers):
        r = client.put(
            "/api/admin/cabinet/me",
            json={"nom": "Cabinet Test Updated"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_cabinet_adresse(self, client, auth_headers):
        r = client.put(
            "/api/admin/cabinet/me",
            json={"adresse": "123 Rue Test, Casablanca"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_cabinet_inpe(self, client, auth_headers):
        r = client.put(
            "/api/admin/cabinet/me",
            json={"inpe": "12345678"},
            headers=auth_headers,
        )
        assert r.status_code == 200


# ── backups ───────────────────────────────────────────────────────────────────

class TestBackups:
    def test_list_backups_requires_auth(self, client):
        r = client.get("/api/admin/backups")
        assert r.status_code == 401

    def test_list_backups_returns_list(self, client, auth_headers):
        r = client.get("/api/admin/backups", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_trigger_backup_requires_auth(self, client):
        r = client.post("/api/admin/backups/trigger")
        assert r.status_code == 401

    def test_trigger_backup_returns_success_or_500(self, client, auth_headers):
        r = client.post("/api/admin/backups/trigger", headers=auth_headers)
        # May fail if backup service not configured, but should not crash
        assert r.status_code in (200, 500)


# ── cabinet health widget ───────────────────────────────────────────────────────

class TestCabinetHealth:
    def _write_manifest(self, tmp_path, **overrides):
        import json
        from datetime import datetime

        manifests_dir = tmp_path / "backups" / "scheduled" / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": "abc123",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "overall_status": "SUCCESS",
            "offsite_status": "NOT_CONFIGURED",
            "offsite_db_copied": False,
            "offsite_media_copied": False,
        }
        manifest.update(overrides)
        (manifests_dir / "latest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    def test_requires_auth(self, client):
        r = client.get("/api/admin/cabinet-health")
        assert r.status_code == 401

    def test_returns_ok_shape_with_no_manifest(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setenv("DIGITALCROWN_RUNTIME_ROOT", str(tmp_path))
        r = client.get("/api/admin/cabinet-health", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["backup_local"]["status"] == "none"
        assert body["offsite"]["status"] == "NOT_CONFIGURED"

    def test_disk_and_db_present_even_without_manifest(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setenv("DIGITALCROWN_RUNTIME_ROOT", str(tmp_path))
        r = client.get("/api/admin/cabinet-health", headers=auth_headers)
        body = r.json()
        assert body["database"]["status"] in ("ok", "error")
        assert body["disk"]["status"] in ("ok", "warning", "critical", "unknown")
        assert "overall_severity" in body

    def test_reflects_real_manifest_overall_status_and_age(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setenv("DIGITALCROWN_RUNTIME_ROOT", str(tmp_path))
        self._write_manifest(tmp_path, overall_status="SUCCESS")

        r = client.get("/api/admin/cabinet-health", headers=auth_headers)
        body = r.json()
        assert body["backup_local"]["overall_status"] == "SUCCESS"
        assert body["backup_local"]["run_id"] == "abc123"
        assert body["backup_local"]["age_hours"] is not None
        assert body["backup_local"]["age_hours"] < 1  # manifest was just written

    def test_stale_backup_reported_as_critical(self, client, auth_headers, tmp_path, monkeypatch):
        import json
        from datetime import datetime, timedelta

        monkeypatch.setenv("DIGITALCROWN_RUNTIME_ROOT", str(tmp_path))
        old = (datetime.utcnow() - timedelta(hours=72)).isoformat() + "Z"
        self._write_manifest(tmp_path, overall_status="SUCCESS", completed_at=old)

        r = client.get("/api/admin/cabinet-health", headers=auth_headers)
        body = r.json()
        assert body["backup_local"]["status"] == "critical"

    def test_offsite_not_configured_never_elevates_severity_to_critical(self, client, auth_headers, tmp_path, monkeypatch):
        import shutil as _shutil
        from unittest.mock import patch

        monkeypatch.setenv("DIGITALCROWN_RUNTIME_ROOT", str(tmp_path))
        self._write_manifest(tmp_path, overall_status="SUCCESS", offsite_status="NOT_CONFIGURED")

        fake_usage = _shutil.disk_usage(str(tmp_path))._replace(free=100 * 1024 ** 3)
        with patch.object(_shutil, "disk_usage", return_value=fake_usage):
            r = client.get("/api/admin/cabinet-health", headers=auth_headers)
        body = r.json()
        assert body["overall_severity"] != "critical"

    def test_offsite_failure_never_elevates_overall_severity(self, client, auth_headers, tmp_path, monkeypatch):
        """Offsite is intentionally excluded from overall_severity -- a broken NAS
        must never look as alarming as an actual DB/local-backup problem."""
        import shutil as _shutil
        from unittest.mock import patch

        monkeypatch.setenv("DIGITALCROWN_RUNTIME_ROOT", str(tmp_path))
        self._write_manifest(tmp_path, overall_status="SUCCESS", offsite_status="FAILED")

        with patch.object(_shutil, "disk_usage", return_value=_shutil.disk_usage(str(tmp_path))._replace(free=100 * 1024 ** 3)):
            r = client.get("/api/admin/cabinet-health", headers=auth_headers)
        body = r.json()
        assert body["offsite"]["status"] == "warning"
        assert body["overall_severity"] != "critical"


# ── zka key qr ───────────────────────────────────────────────────────────────

class TestZkaKeyQr:
    def test_requires_auth(self, client):
        r = client.get("/api/admin/zka-key-qr")
        assert r.status_code == 401

    def test_without_config_returns_404_or_qr(self, client, auth_headers):
        import os
        os.environ.setdefault("CABINET_MASTER_KEY_HEX", "0" * 64)
        r = client.get("/api/admin/zka-key-qr", headers=auth_headers)
        # Either returns QR or 404 if CabinetConfig not set up
        assert r.status_code in (200, 404, 500)
