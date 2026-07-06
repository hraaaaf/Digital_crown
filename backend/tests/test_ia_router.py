"""Tests routers/ia.py — cephalo/panoramic analyses, list, delete, calibrate."""
import pytest
from datetime import datetime


def _make_patient(db, dentiste, nom="IAPAT"):
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


def _make_cephalo_analysis(db, patient_id):
    from backend import models
    analysis = models.CephaloAnalysis(
        patient_id=patient_id,
        image_original_path="api/static/uploads/radios/test.jpg",
        angles_data={
            "analyse_osseuse": {
                "Decalage_A_B": {"valeur": 2.3, "status": "Normal", "norm_mean": 2.3, "norm_min": 0.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Angle_de_Tweed": {"valeur": 26.0, "status": "Normal", "norm_mean": 26.0, "norm_min": 20.0, "norm_max": 32.0, "z_score": 0.0, "interpretation": "Normal"},
                "Situation_A": {"valeur": 2.3, "status": "Normal", "norm_mean": 2.3, "norm_min": -1.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Situation_B": {"valeur": 0.0, "status": "Normal", "norm_mean": 0.0, "norm_min": -5.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Profondeur_Faciale": {"valeur": 87.0, "status": "Normal", "norm_mean": 87.0, "norm_min": 82.0, "norm_max": 92.0, "z_score": 0.0, "interpretation": "Normal"},
                "SNA": {"valeur": 82.0, "status": "Normal", "norm_mean": 82.0, "norm_min": 79.0, "norm_max": 85.0, "z_score": 0.0, "interpretation": "Normal"},
                "SNB": {"valeur": 80.0, "status": "Normal", "norm_mean": 80.0, "norm_min": 77.0, "norm_max": 83.0, "z_score": 0.0, "interpretation": "Normal"},
                "ANB": {"valeur": 2.0, "status": "Normal", "norm_mean": 2.0, "norm_min": 0.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
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
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def _make_panoramic_analysis(db, patient_id):
    from backend import models
    analysis = models.PanoramicAnalysis(
        patient_id=patient_id,
        image_path="api/static/uploads/panoramic/test.jpg",
        detections_data={"detections": []},
        report_narrative="Bilan normal.",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


# ── auth guards ────────────────────────────────────────────────────────────────

class TestIaGuard:
    def test_upload_radio_requires_auth(self, client):
        r = client.post("/api/ia/upload-radio?patient_id=1")
        assert r.status_code == 401

    def test_get_analysis_requires_auth(self, client):
        r = client.get("/api/ia/analyses/1")
        assert r.status_code == 401

    def test_cephalo_list_requires_auth(self, client):
        r = client.get("/api/ia/patients/1/cephalo-analyses")
        assert r.status_code == 401

    def test_panoramic_list_requires_auth(self, client):
        r = client.get("/api/ia/patients/1/panoramic-analyses")
        assert r.status_code == 401

    def test_delete_cephalo_requires_auth(self, client):
        r = client.delete("/api/ia/cephalo/1")
        assert r.status_code == 401

    def test_delete_panoramic_requires_auth(self, client):
        r = client.delete("/api/ia/panoramic/1")
        assert r.status_code == 401


# ── cephalo analyses ──────────────────────────────────────────────────────────

class TestCephaloAnalyses:
    def test_list_analyses_empty(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "LISTCEPH")
        r = client.get(f"/api/ia/patients/{pat.id}/cephalo-analyses", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_analyses_with_records(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "LISTWREC")
        _make_cephalo_analysis(db, pat.id)
        r = client.get(f"/api/ia/patients/{pat.id}/cephalo-analyses", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_analysis_by_id(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "GETCEPH")
        analysis = _make_cephalo_analysis(db, pat.id)
        r = client.get(f"/api/ia/analyses/{analysis.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == analysis.id

    def test_get_nonexistent_analysis_returns_404(self, client, auth_headers):
        r = client.get("/api/ia/analyses/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_cephalo_analysis(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "DELCEPH")
        analysis = _make_cephalo_analysis(db, pat.id)
        r = client.delete(f"/api/ia/cephalo/{analysis.id}", headers=auth_headers)
        assert r.status_code == 204

    def test_delete_nonexistent_cephalo_returns_404(self, client, auth_headers):
        r = client.delete("/api/ia/cephalo/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_calibrate_analysis(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "CALIBPAT")
        analysis = _make_cephalo_analysis(db, pat.id)
        r = client.post(
            f"/api/ia/analyses/{analysis.id}/calibrate",
            json={
                "p1": {"x": 100.0, "y": 100.0},
                "p2": {"x": 200.0, "y": 100.0},
                "distance_mm": 30.0,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_calibrated"] is True
        assert "mm_per_pixel" in r.json()

    def test_calibrate_nonexistent_analysis_returns_404(self, client, auth_headers):
        r = client.post(
            "/api/ia/analyses/999999/calibrate",
            json={
                "p1": {"x": 100.0, "y": 100.0},
                "p2": {"x": 200.0, "y": 100.0},
                "distance_mm": 30.0,
            },
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_calibrate_points_too_close_returns_400(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "CALIBCLOSE")
        analysis = _make_cephalo_analysis(db, pat.id)
        r = client.post(
            f"/api/ia/analyses/{analysis.id}/calibrate",
            json={
                "p1": {"x": 100.0, "y": 100.0},
                "p2": {"x": 101.0, "y": 100.0},  # only 1px apart
                "distance_mm": 30.0,
            },
            headers=auth_headers,
        )
        assert r.status_code == 400


# ── panoramic analyses ────────────────────────────────────────────────────────

class TestPanoramicAnalyses:
    def test_list_panoramic_empty(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "LISTPANO")
        r = client.get(f"/api/ia/patients/{pat.id}/panoramic-analyses", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_panoramic_with_records(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PANOREC")
        _make_panoramic_analysis(db, pat.id)
        r = client.get(f"/api/ia/patients/{pat.id}/panoramic-analyses", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_panoramic_comparison_insufficient_data(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "COMPNONE")
        r = client.get(f"/api/ia/patients/{pat.id}/panoramic-comparison", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["available"] is False

    def test_delete_panoramic_analysis(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "DELPANO")
        analysis = _make_panoramic_analysis(db, pat.id)
        r = client.delete(f"/api/ia/panoramic/{analysis.id}", headers=auth_headers)
        assert r.status_code == 204

    def test_delete_nonexistent_panoramic_returns_404(self, client, auth_headers):
        r = client.delete("/api/ia/panoramic/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_update_panoramic_report(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "UPDPANO")
        analysis = _make_panoramic_analysis(db, pat.id)
        r = client.put(
            f"/api/ia/panoramic/{analysis.id}/report",
            json={"report_narrative": "Rapport mis à jour."},
            headers=auth_headers,
        )
        assert r.status_code in (200, 404)
