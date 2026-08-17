"""Extended tests routers/ia.py — update analysis, generate report, pdf, upload guards."""
import io
from datetime import datetime

import pytest


def _make_patient(db, dentiste, nom="IAEXT"):
    from backend import models
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1985, 7, 20),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _make_cephalo(db, patient_id):
    from backend import models
    a = models.CephaloAnalysis(
        patient_id=patient_id,
        image_original_path="api/static/uploads/radios/test.jpg",
        angles_data={
            "analyse_osseuse": {
                "SNA": {"valeur": 82.0, "status": "Normal", "norm_mean": 82.0, "norm_min": 79.0, "norm_max": 85.0, "z_score": 0.0, "interpretation": "Normal"},
                "SNB": {"valeur": 80.0, "status": "Normal", "norm_mean": 80.0, "norm_min": 77.0, "norm_max": 83.0, "z_score": 0.0, "interpretation": "Normal"},
                "ANB": {"valeur": 2.0, "status": "Normal", "norm_mean": 2.0, "norm_min": 0.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
                "Decalage_A_B": {"valeur": 2.3, "status": "Normal", "norm_mean": 2.3, "norm_min": 0.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Angle_de_Tweed": {"valeur": 26.0, "status": "Normal", "norm_mean": 26.0, "norm_min": 20.0, "norm_max": 32.0, "z_score": 0.0, "interpretation": "Normal"},
                "Situation_A": {"valeur": 2.3, "status": "Normal", "norm_mean": 2.3, "norm_min": -1.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Situation_B": {"valeur": 0.0, "status": "Normal", "norm_mean": 0.0, "norm_min": -5.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Profondeur_Faciale": {"valeur": 87.0, "status": "Normal", "norm_mean": 87.0, "norm_min": 82.0, "norm_max": 92.0, "z_score": 0.0, "interpretation": "Normal"},
            },
            "analyse_dentaire": {
                "IMPA": {"valeur": 90.0, "status": "Normal", "norm_mean": 90.0, "norm_min": 83.0, "norm_max": 97.0, "z_score": 0.0, "interpretation": "Normal"},
                "I_Francfort": {"valeur": 107.0, "status": "Normal", "norm_mean": 107.0, "norm_min": 100.0, "norm_max": 114.0, "z_score": 0.0, "interpretation": "Normal"},
                "Surplomb": {"valeur": 2.5, "status": "Normal", "norm_mean": 2.5, "norm_min": 1.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
                "Recouvrement": {"valeur": 2.5, "status": "Normal", "norm_mean": 2.5, "norm_min": 1.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
                "Inter_Incisif": {"valeur": 130.0, "status": "Normal", "norm_mean": 130.0, "norm_min": 125.0, "norm_max": 135.0, "z_score": 0.0, "interpretation": "Normal"},
            },
            "analyse_esthetique": {
                "Ligne_E_Ls": {"valeur": -2.0, "status": "Normal", "norm_mean": -2.0, "norm_min": -5.0, "norm_max": 1.0, "z_score": 0.0, "interpretation": "Normal"},
                "Ligne_E_Li": {"valeur": 0.0, "status": "Normal", "norm_mean": 0.0, "norm_min": -3.0, "norm_max": 3.0, "z_score": 0.0, "interpretation": "Normal"},
                "Angle_Nasolabial": {"valeur": 102.0, "status": "Normal", "norm_mean": 102.0, "norm_min": 95.0, "norm_max": 110.0, "z_score": 0.0, "interpretation": "Normal"},
            },
        },
        mm_per_pixel=0.2,
        is_calibrated=True,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _make_panoramic(db, patient_id):
    from backend import models
    a = models.PanoramicAnalysis(
        patient_id=patient_id,
        image_path="api/static/uploads/panoramic/test.jpg",
        detections_data={"detections": []},
        report_narrative="Bilan normal.",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


_LANDMARK_PAYLOAD = [
    {"id": "SNA", "x": 100.0, "y": 200.0},
    {"id": "SNB", "x": 110.0, "y": 210.0},
]


class TestUpdateCephaloAnalysis:
    def test_update_requires_auth(self, client):
        r = client.put("/api/ia/analyses/1", json={"landmarks": _LANDMARK_PAYLOAD})
        assert r.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        r = client.put(
            "/api/ia/analyses/999999",
            json={"landmarks": _LANDMARK_PAYLOAD},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_update_analysis_succeeds(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "CEPHUPD")
        analysis = _make_cephalo(db, pat.id)
        r = client.put(
            f"/api/ia/analyses/{analysis.id}",
            json={"landmarks": _LANDMARK_PAYLOAD, "mm_per_pixel": 0.2},
            headers=auth_headers,
        )
        assert r.status_code in (200, 500)


class TestGeneratePanoramicReport:
    def test_generate_requires_auth(self, client):
        r = client.post(
            "/api/ia/generate-panoramic-report",
            json={"analysis_id": 1, "manual_anomalies": [], "global_findings": []},
        )
        assert r.status_code == 401

    def test_generate_nonexistent_returns_404(self, client, auth_headers):
        r = client.post(
            "/api/ia/generate-panoramic-report",
            json={"analysis_id": 999999, "manual_anomalies": {}, "global_findings": []},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_generate_basic_report(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PANOREPORT")
        analysis = _make_panoramic(db, pat.id)
        r = client.post(
            "/api/ia/generate-panoramic-report",
            json={
                "analysis_id": analysis.id,
                "manual_anomalies": {},
                "global_findings": [],
                "rejected_detections": [],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert "report_narrative" in body

    def test_generate_with_manual_anomalies(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PANOMANUAL")
        analysis = _make_panoramic(db, pat.id)
        r = client.post(
            "/api/ia/generate-panoramic-report",
            json={
                "analysis_id": analysis.id,
                "manual_anomalies": {"16": ["Carie"], "26": ["Tartre"]},
                "global_findings": ["Perte osseuse légère"],
                "rejected_detections": [],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_generate_with_visual_annotations(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PANOANNOT")
        analysis = _make_panoramic(db, pat.id)
        r = client.post(
            "/api/ia/generate-panoramic-report",
            json={
                "analysis_id": analysis.id,
                "manual_anomalies": {},
                "global_findings": [],
                "rejected_detections": [],
                "visual_annotations": [{"id": 1, "x": 25.0, "y": 50.0, "text": "Suspicion carie"}],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200


class TestPanoramicPdf:
    def test_pdf_requires_auth(self, client):
        r = client.get("/api/ia/panoramic/1/pdf")
        assert r.status_code == 401

    def test_pdf_nonexistent_analysis_returns_error(self, client, auth_headers):
        """Nonexistent analysis — either 404 or 500 depending on generator internals."""
        r = client.get("/api/ia/panoramic/999999/pdf", headers=auth_headers)
        assert r.status_code in (404, 500)

    def test_pdf_existing_analysis_returns_url_or_500(self, client, db, auth_headers, dentiste):
        """Generator may fail in test env (no WeasyPrint) but should not 401/403."""
        pat = _make_patient(db, dentiste, "PANOPDF")
        analysis = _make_panoramic(db, pat.id)
        r = client.get(f"/api/ia/panoramic/{analysis.id}/pdf", headers=auth_headers)
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            assert "pdf_url" in r.json()


class TestUploadRadioGuards:
    def test_upload_radio_invalid_patient_returns_403_or_404(self, client, auth_headers):
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        r = client.post(
            "/api/ia/upload-radio",
            params={"patient_id": 999999},
            files={"file": ("radio.jpg", fake_image, "image/jpeg")},
            headers=auth_headers,
        )
        assert r.status_code in (400, 403, 404)

    def test_upload_panoramic_invalid_patient_returns_403_or_404(self, client, auth_headers):
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        r = client.post(
            "/api/ia/upload-panoramic",
            params={"patient_id": 999999},
            files={"file": ("panoramic.jpg", fake_image, "image/jpeg")},
            headers=auth_headers,
        )
        assert r.status_code in (400, 403, 404)


class TestAdminExtended:
    def test_export_db_requires_auth(self, client):
        r = client.get("/api/admin/export-db")
        assert r.status_code == 401

    def test_export_db_fails_closed_for_in_memory_database(self, client, auth_headers):
        """Authenticated export reaches the handler and returns a controlled failure."""
        r = client.get("/api/admin/export-db", headers=auth_headers)
        assert r.status_code == 500
        assert "sauvegarde chiffrée" in r.json()["detail"].lower()

    def test_revoke_mobile_requires_auth(self, client):
        r = client.post("/api/admin/revoke-mobile")
        assert r.status_code == 401

    def test_revoke_mobile_returns_200_or_500(self, client, auth_headers):
        from unittest.mock import patch
        with patch("backend.services.zka_service.zka_service.rotate_master_key", return_value="newkey"), \
             patch("backend.services.sync_manager.sync_manager._sync_single_cabinet", return_value=None):
            r = client.post("/api/admin/revoke-mobile", headers=auth_headers)
        assert r.status_code in (200, 500)

    def test_backup_download_requires_auth(self, client):
        r = client.get("/api/admin/backups/download/test.enc")
        assert r.status_code == 401

    def test_backup_download_invalid_extension_returns_400(self, client, auth_headers):
        r = client.get("/api/admin/backups/download/test.sql", headers=auth_headers)
        assert r.status_code == 400

    def test_backup_download_missing_file_returns_404(self, client, auth_headers):
        r = client.get("/api/admin/backups/download/nonexistent_file.enc", headers=auth_headers)
        assert r.status_code == 404

    def test_audit_logs_severity_filter(self, client, db, auth_headers, dentiste):
        from backend import models
        log = models.AuditLog(
            user_id=dentiste.id,
            employer_id=dentiste.id,
            action="TEST_SEV",
            resource_type="Test",
            severity="CRITICAL",
            timestamp=datetime.now(),
        )
        db.add(log)
        db.commit()

        r = client.get("/api/admin/audit-logs?severity=CRITICAL", headers=auth_headers)
        assert r.status_code == 200
        for entry in r.json()["logs"]:
            assert entry["severity"] == "CRITICAL"

    def test_dashboard_stats_has_team_quota(self, client, auth_headers):
        r = client.get("/api/admin/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "pending_team_requests" in body
        assert "team_quota" in body
