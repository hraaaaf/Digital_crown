"""Tests routers/ai_feedback.py — submit feedback, stats, ghost insights."""
from datetime import datetime


def _make_patient(db, dentiste, nom="FBPAT"):
    from backend import models
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1988, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


# ── submit feedback ───────────────────────────────────────────────────────────

class TestSubmitFeedback:
    def test_requires_auth(self, client):
        r = client.post("/api/ai/feedback", json={
            "patient_id": 1,
            "insight_type": "carie",
            "insight_content": "Carie détectée",
            "action": "accept",
        })
        assert r.status_code == 401

    def test_invalid_action_returns_422(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "FBINV")
        r = client.post(
            "/api/ai/feedback",
            json={
                "patient_id": pat.id,
                "insight_type": "carie",
                "insight_content": "Carie",
                "action": "invalid_action",
            },
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_submit_accept(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "FBACCEPT")
        r = client.post(
            "/api/ai/feedback",
            json={
                "patient_id": pat.id,
                "insight_type": "carie",
                "insight_content": "Carie détectée sur 46",
                "action": "accept",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "recorded"
        assert "id" in body

    def test_submit_reject(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "FBREJECT")
        r = client.post(
            "/api/ai/feedback",
            json={
                "patient_id": pat.id,
                "insight_type": "tartre",
                "insight_content": "Tartre visible",
                "action": "reject",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_submit_edit_with_corrected_text(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "FBEDIT")
        r = client.post(
            "/api/ai/feedback",
            json={
                "patient_id": pat.id,
                "insight_type": "implant",
                "insight_content": "Implant suggéré",
                "action": "edit",
                "corrected_text": "Prothèse partielle recommandée",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_submit_resolved(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "FBRESOLVED")
        r = client.post(
            "/api/ai/feedback",
            json={
                "patient_id": pat.id,
                "insight_type": "rappel",
                "insight_content": "Rappel 6 mois",
                "action": "resolved",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200


# ── feedback stats ────────────────────────────────────────────────────────────

class TestFeedbackStats:
    def test_requires_auth(self, client):
        r = client.get("/api/ai/feedback/stats")
        assert r.status_code == 401

    def test_empty_stats_returns_dict(self, client, auth_headers):
        r = client.get("/api/ai/feedback/stats", headers=auth_headers)
        assert r.status_code == 200
        assert "stats" in r.json()

    def test_stats_after_feedback(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "FBSTATS")
        # Submit some feedback
        for action in ("accept", "accept", "reject"):
            client.post(
                "/api/ai/feedback",
                json={
                    "patient_id": pat.id,
                    "insight_type": "carie_stats",
                    "insight_content": "Test",
                    "action": action,
                },
                headers=auth_headers,
            )

        r = client.get("/api/ai/feedback/stats", headers=auth_headers)
        assert r.status_code == 200
        stats = r.json()["stats"]
        if "carie_stats" in stats:
            assert "accept" in stats["carie_stats"] or "reject" in stats["carie_stats"]


# ── ghost insights ─────────────────────────────────────────────────────────────

class TestGhostSnapshotDiff:
    def test_same_unread_count_with_replaced_id_broadcasts_new_patient_alert(self):
        """A read + B arrives while total remains 1: WebSocket must send B."""
        from types import SimpleNamespace
        from backend.routers.ai_feedback import _ghost_snapshot_if_changed

        date = datetime(2026, 10, 17, 12, 0, 0)
        a = SimpleNamespace(id=101, patient_id=10, insight_type="AGENDA",
                            content="Ancienne alerte", created_at=date)
        b = SimpleNamespace(id=102, patient_id=20, insight_type="AGENDA",
                            content="Nouvelle alerte", created_at=date)

        first, signature_a = _ghost_snapshot_if_changed([a], 1, None)
        assert first["unread_count"] == 1
        assert [item["id"] for item in first["insights"]] == [101]
        unchanged, same_signature = _ghost_snapshot_if_changed([a], 1, signature_a)
        assert unchanged is None
        assert same_signature == signature_a

        replacement, signature_b = _ghost_snapshot_if_changed([b], 1, signature_a)
        assert replacement is not None
        assert replacement["unread_count"] == 1
        assert [item["id"] for item in replacement["insights"]] == [102]
        assert signature_b != signature_a

        # An edited alert must also refresh even if its ID and count do not.
        changed = SimpleNamespace(id=102, patient_id=20, insight_type="AGENDA",
                                  content="Alerte mise à jour", created_at=date)
        updated, signature_c = _ghost_snapshot_if_changed([changed], 1, signature_b)
        assert updated["insights"][0]["content"] == "Alerte mise à jour"
        assert signature_c != signature_b


class TestGhostInsights:
    def test_requires_auth(self, client):
        r = client.get("/api/ai/ghost-insights")
        assert r.status_code == 401

    def test_empty_returns_structure(self, client, auth_headers):
        r = client.get("/api/ai/ghost-insights", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "unread_count" in body
        assert "insights" in body
        assert isinstance(body["insights"], list)

    def test_mark_nonexistent_insight_returns_404(self, client, auth_headers):
        r = client.post("/api/ai/ghost-insights/999999/read", headers=auth_headers)
        assert r.status_code == 404

    def test_mark_insight_read(self, client, db, auth_headers, dentiste):
        from backend import models
        pat = _make_patient(db, dentiste, "GHOSTPAT")
        log = models.GhostMemoryLog(
            employer_id=dentiste.id,
            patient_id=pat.id,
            insight_type="TEST",
            content="Test insight",
            context_hash="testhash123",
            is_read=False,
            created_at=datetime.now(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        r = client.post(f"/api/ai/ghost-insights/{log.id}/read", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "read"
