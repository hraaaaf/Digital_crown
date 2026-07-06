"""Tests routers/catalog.py — specialties, pathologies, catalog acts."""


class TestSpecialties:
    def test_list_requires_auth(self, client):
        r = client.get("/api/catalog/specialties")
        assert r.status_code == 401

    def test_list_specialties(self, client, auth_headers):
        r = client.get("/api/catalog/specialties", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_specialty(self, client, auth_headers):
        r = client.post(
            "/api/catalog/specialties",
            json={"name": "Orthodontie Test", "color": "#FF5733"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Orthodontie Test"
        assert "id" in body

    def test_update_specialty(self, client, auth_headers):
        # Create first
        r = client.post(
            "/api/catalog/specialties",
            json={"name": "Implantologie Test"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        spec_id = r.json()["id"]

        r = client.put(
            f"/api/catalog/specialties/{spec_id}",
            json={"name": "Implantologie Updated"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Implantologie Updated"

    def test_update_nonexistent_specialty(self, client, auth_headers):
        r = client.put(
            "/api/catalog/specialties/999999",
            json={"name": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestPathologies:
    def _create_specialty(self, client, auth_headers, name="Endodontie Test"):
        r = client.post(
            "/api/catalog/specialties",
            json={"name": name},
            headers=auth_headers,
        )
        assert r.status_code == 201
        return r.json()["id"]

    def test_create_pathology(self, client, auth_headers):
        spec_id = self._create_specialty(client, auth_headers, "Endodontie B")
        r = client.post(
            f"/api/catalog/specialties/{spec_id}/pathologies",
            json={"name": "Pulpite irréversible"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Pulpite irréversible"

    def test_create_pathology_nonexistent_specialty(self, client, auth_headers):
        r = client.post(
            "/api/catalog/specialties/999999/pathologies",
            json={"name": "Carie"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_update_pathology(self, client, auth_headers):
        from backend import models

        spec_id = self._create_specialty(client, auth_headers, "Chirurgie C")
        r = client.post(
            f"/api/catalog/specialties/{spec_id}/pathologies",
            json={"name": "Carie amélaire"},
            headers=auth_headers,
        )
        path_id = r.json()["id"]

        r = client.put(
            f"/api/catalog/pathologies/{path_id}",
            json={"name": "Carie amélaire sévère"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Carie amélaire sévère"

    def test_update_nonexistent_pathology(self, client, auth_headers):
        r = client.put(
            "/api/catalog/pathologies/999999",
            json={"name": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestCatalogActs:
    def _create_specialty(self, client, auth_headers, name="Pédiatrie D"):
        r = client.post(
            "/api/catalog/specialties",
            json={"name": name},
            headers=auth_headers,
        )
        return r.json()["id"]

    def test_create_act(self, client, auth_headers):
        spec_id = self._create_specialty(client, auth_headers)
        r = client.post(
            f"/api/catalog/specialties/{spec_id}/acts",
            json={"name": "Scellement sillon", "base_price": 1200.0},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Scellement sillon"

    def test_create_act_nonexistent_specialty(self, client, auth_headers):
        r = client.post(
            "/api/catalog/specialties/999999/acts",
            json={"name": "Scellement"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_update_act(self, client, auth_headers):
        spec_id = self._create_specialty(client, auth_headers, "Prothèse E")
        r = client.post(
            f"/api/catalog/specialties/{spec_id}/acts",
            json={"name": "Couronne zircone", "base_price": 8000.0},
            headers=auth_headers,
        )
        act_id = r.json()["id"]

        r = client.put(
            f"/api/catalog/acts/{act_id}",
            json={"base_price": 9000.0},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["base_price"] == 9000.0

    def test_update_nonexistent_act(self, client, auth_headers):
        r = client.put(
            "/api/catalog/acts/999999",
            json={"name": "X"},
            headers=auth_headers,
        )
        assert r.status_code == 404
