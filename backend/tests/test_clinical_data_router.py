"""Tests routers/clinical_data.py — contraindications, drugs, protocols CRUD."""
import pytest


BASE = "/api/clinical-data"


class TestContraindications:
    def test_list_requires_auth(self, client):
        r = client.get(f"{BASE}/contraindications")
        assert r.status_code == 401

    def test_list_empty(self, client, auth_headers):
        r = client.get(f"{BASE}/contraindications", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_contraindication(self, client, auth_headers):
        r = client.post(
            f"{BASE}/contraindications",
            json={"antecedent": "DIABETE", "molecule": "METFORMINE"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["antecedent"] == "DIABETE"
        assert body["molecule"] == "METFORMINE"
        assert body["is_active"] is True

    def test_create_normalizes_uppercase(self, client, auth_headers):
        r = client.post(
            f"{BASE}/contraindications",
            json={"antecedent": "penicilline_allergy", "molecule": "amoxicilline"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["antecedent"] == "PENICILLINE_ALLERGY"
        assert body["molecule"] == "AMOXICILLINE"

    def test_delete_contraindication(self, client, auth_headers):
        r = client.post(
            f"{BASE}/contraindications",
            json={"antecedent": "TODELETE", "molecule": "MOL"},
            headers=auth_headers,
        )
        ci_id = r.json()["id"]
        r2 = client.delete(f"{BASE}/contraindications/{ci_id}", headers=auth_headers)
        assert r2.status_code == 204

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete(f"{BASE}/contraindications/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_create_requires_auth(self, client):
        r = client.post(f"{BASE}/contraindications", json={"antecedent": "X", "molecule": "Y"})
        assert r.status_code == 401


class TestDrugs:
    def test_list_requires_auth(self, client):
        r = client.get(f"{BASE}/drugs")
        assert r.status_code == 401

    def test_list_drugs(self, client, auth_headers):
        r = client.get(f"{BASE}/drugs", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_drug(self, client, auth_headers):
        r = client.post(
            f"{BASE}/drugs",
            json={
                "molecule": "IBUPROFENE_TEST",
                "brand_names": ["Brufen", "Nurofen"],
                "dosages": ["200mg", "400mg"],
                "form": "Comprimé",
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["molecule"] == "IBUPROFENE_TEST"
        assert body["is_active"] is True

    def test_create_duplicate_drug_returns_409(self, client, auth_headers):
        client.post(
            f"{BASE}/drugs",
            json={"molecule": "DUPTEST_DRUG"},
            headers=auth_headers,
        )
        r2 = client.post(
            f"{BASE}/drugs",
            json={"molecule": "DUPTEST_DRUG"},
            headers=auth_headers,
        )
        assert r2.status_code == 409

    def test_update_drug(self, client, auth_headers):
        r = client.post(
            f"{BASE}/drugs",
            json={"molecule": "UPDATABLE_DRUG", "brand_names": ["OldBrand"]},
            headers=auth_headers,
        )
        drug_id = r.json()["id"]
        r2 = client.put(
            f"{BASE}/drugs/{drug_id}",
            json={"molecule": "UPDATABLE_DRUG", "brand_names": ["NewBrand"], "dosages": ["100mg"]},
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert "NewBrand" in r2.json()["brand_names"]

    def test_update_nonexistent_drug_returns_404(self, client, auth_headers):
        r = client.put(
            f"{BASE}/drugs/999999",
            json={"molecule": "X", "brand_names": []},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_delete_drug(self, client, auth_headers):
        r = client.post(f"{BASE}/drugs", json={"molecule": "TODELETE_DRUG"}, headers=auth_headers)
        drug_id = r.json()["id"]
        r2 = client.delete(f"{BASE}/drugs/{drug_id}", headers=auth_headers)
        assert r2.status_code == 204

    def test_delete_nonexistent_drug_returns_404(self, client, auth_headers):
        r = client.delete(f"{BASE}/drugs/999999", headers=auth_headers)
        assert r.status_code == 404


class TestProtocols:
    def test_list_requires_auth(self, client):
        r = client.get(f"{BASE}/protocols")
        assert r.status_code == 401

    def test_list_protocols(self, client, auth_headers):
        r = client.get(f"{BASE}/protocols", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_protocol(self, client, auth_headers):
        r = client.post(
            f"{BASE}/protocols",
            json={
                "procedure": "DETARTRAGE_TEST",
                "molecules": ["Chlorhexidine"],
                "advice": "Rincer abondamment",
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["procedure"] == "DETARTRAGE_TEST"
        assert body["is_active"] is True

    def test_create_duplicate_protocol_returns_409(self, client, auth_headers):
        client.post(f"{BASE}/protocols", json={"procedure": "DUP_PROTO"}, headers=auth_headers)
        r2 = client.post(f"{BASE}/protocols", json={"procedure": "DUP_PROTO"}, headers=auth_headers)
        assert r2.status_code == 409

    def test_update_protocol(self, client, auth_headers):
        r = client.post(
            f"{BASE}/protocols",
            json={"procedure": "UPDATABLE_PROTO", "molecules": ["OldMol"]},
            headers=auth_headers,
        )
        proto_id = r.json()["id"]
        r2 = client.put(
            f"{BASE}/protocols/{proto_id}",
            json={"procedure": "UPDATABLE_PROTO", "molecules": ["NewMol"], "advice": "New advice"},
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert "NewMol" in r2.json()["molecules"]

    def test_update_nonexistent_protocol_returns_404(self, client, auth_headers):
        r = client.put(
            f"{BASE}/protocols/999999",
            json={"procedure": "X", "molecules": []},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_delete_protocol(self, client, auth_headers):
        r = client.post(f"{BASE}/protocols", json={"procedure": "TODELETE_PROTO"}, headers=auth_headers)
        proto_id = r.json()["id"]
        r2 = client.delete(f"{BASE}/protocols/{proto_id}", headers=auth_headers)
        assert r2.status_code == 204

    def test_delete_nonexistent_protocol_returns_404(self, client, auth_headers):
        r = client.delete(f"{BASE}/protocols/999999", headers=auth_headers)
        assert r.status_code == 404
