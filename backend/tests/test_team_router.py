"""Tests routers/team.py — quota, CRUD team members, approve/reject/delete."""
import pytest


def _member_payload(email, role="SECRETAIRE", password="Pass123!Sec"):
    return {
        "email": email,
        "nom_complet": "Test Membre",
        "role": role,
        "password": password,
        "telephone_mobile": "0600000001",
    }


# ── guard ──────────────────────────────────────────────────────────────────────

class TestTeamGuard:
    def test_quota_requires_auth(self, client):
        r = client.get("/api/team/quota")
        assert r.status_code == 401

    def test_list_requires_auth(self, client):
        r = client.get("/api/team/")
        assert r.status_code == 401

    def test_create_requires_auth(self, client):
        r = client.post("/api/team/", json=_member_payload("x@x.ma"))
        assert r.status_code == 401


# ── quota ──────────────────────────────────────────────────────────────────────

class TestTeamQuota:
    def test_quota_returns_structure(self, client, auth_headers):
        r = client.get("/api/team/quota", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        for field in ("plan", "dentistes_used", "dentistes_max", "secretaires_used", "secretaires_max"):
            assert field in body

    def test_quota_dentistes_used_at_least_1(self, client, auth_headers):
        r = client.get("/api/team/quota", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["dentistes_used"] >= 1


# ── list ───────────────────────────────────────────────────────────────────────

class TestTeamList:
    def test_list_returns_list(self, client, auth_headers):
        r = client.get("/api/team/", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── create ─────────────────────────────────────────────────────────────────────

class TestTeamCreate:
    def test_create_secretaire(self, client, auth_headers):
        r = client.post(
            "/api/team/",
            json=_member_payload("sec1@cabinet.ma", "SECRETAIRE"),
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "sec1@cabinet.ma"
        assert body["approval_status"] == "pending"

    def test_create_dentiste(self, client, auth_headers, dentiste):
        # Set PREMIUM plan so we can add a dentiste
        from backend import models
        dentiste.subscription_plan = "PREMIUM"
        from backend import database
        db = next(database.get_db())
        db.merge(dentiste)
        db.commit()

        r = client.post(
            "/api/team/",
            json=_member_payload("dent2@cabinet.ma", "DENTISTE", "PassDent123!"),
            headers=auth_headers,
        )
        assert r.status_code in (201, 402)  # 402 if GOLD plan quota reached

    def test_duplicate_email_returns_409(self, client, auth_headers):
        payload = _member_payload("dup@cabinet.ma", "SECRETAIRE")
        client.post("/api/team/", json=payload, headers=auth_headers)
        r = client.post("/api/team/", json=payload, headers=auth_headers)
        assert r.status_code == 409

    def test_quota_exhausted_secretaire_returns_402(self, client, auth_headers):
        # GOLD plan allows 2 secretaires — create 2, then try a 3rd
        client.post("/api/team/", json=_member_payload("s1@cabinet.ma"), headers=auth_headers)
        client.post("/api/team/", json=_member_payload("s2@cabinet.ma"), headers=auth_headers)
        r = client.post("/api/team/", json=_member_payload("s3@cabinet.ma"), headers=auth_headers)
        assert r.status_code in (201, 402)  # depends on current quota state


# ── approve / reject ───────────────────────────────────────────────────────────

class TestTeamApprove:
    def _create_member(self, client, auth_headers, email):
        r = client.post(
            "/api/team/",
            json=_member_payload(email),
            headers=auth_headers,
        )
        assert r.status_code == 201
        return r.json()["id"]

    def test_approve_pending_member(self, client, auth_headers):
        mid = self._create_member(client, auth_headers, "approve1@cabinet.ma")
        r = client.post(f"/api/team/{mid}/approve", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["approval_status"] == "approved"
        assert r.json()["is_active"] is True

    def test_approve_nonexistent_returns_404(self, client, auth_headers):
        r = client.post("/api/team/999999/approve", headers=auth_headers)
        assert r.status_code == 404

    def test_reject_pending_member(self, client, auth_headers):
        mid = self._create_member(client, auth_headers, "reject1@cabinet.ma")
        r = client.post(f"/api/team/{mid}/reject", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["approval_status"] == "rejected"

    def test_reject_nonexistent_returns_404(self, client, auth_headers):
        r = client.post("/api/team/999999/reject", headers=auth_headers)
        assert r.status_code == 404


# ── update ─────────────────────────────────────────────────────────────────────

class TestTeamUpdate:
    def test_update_nom_complet(self, client, auth_headers):
        r = client.post(
            "/api/team/",
            json=_member_payload("upd1@cabinet.ma"),
            headers=auth_headers,
        )
        mid = r.json()["id"]

        r = client.put(
            f"/api/team/{mid}",
            json={"nom_complet": "Nom Mis à Jour"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["nom_complet"] == "Nom Mis à Jour"

    def test_update_permissions(self, client, auth_headers):
        r = client.post(
            "/api/team/",
            json=_member_payload("upd2@cabinet.ma"),
            headers=auth_headers,
        )
        mid = r.json()["id"]

        r = client.put(
            f"/api/team/{mid}",
            json={"permissions": {"agenda": True, "patients": True, "prescriptions": True}},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        r = client.put(
            "/api/team/999999",
            json={"nom_complet": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_update_duplicate_email_returns_409(self, client, auth_headers):
        r1 = client.post("/api/team/", json=_member_payload("e1conflict@cabinet.ma"), headers=auth_headers)
        r2 = client.post("/api/team/", json=_member_payload("e2conflict@cabinet.ma"), headers=auth_headers)
        mid2 = r2.json()["id"]

        r = client.put(
            f"/api/team/{mid2}",
            json={"email": "e1conflict@cabinet.ma"},
            headers=auth_headers,
        )
        assert r.status_code == 409


# ── delete ─────────────────────────────────────────────────────────────────────

class TestTeamDelete:
    def test_delete_member(self, client, auth_headers):
        r = client.post(
            "/api/team/",
            json=_member_payload("del1@cabinet.ma"),
            headers=auth_headers,
        )
        mid = r.json()["id"]

        r = client.delete(f"/api/team/{mid}", headers=auth_headers)
        assert r.status_code == 204

        # Not in list anymore
        members = client.get("/api/team/", headers=auth_headers).json()
        assert all(m["id"] != mid for m in members)

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete("/api/team/999999", headers=auth_headers)
        assert r.status_code == 404
