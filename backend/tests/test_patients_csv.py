"""Tests import patients CSV — POST /api/patients/import-csv."""
import io


def _csv(rows: list[list[str]], delimiter=";", header=True) -> bytes:
    lines = []
    if header:
        lines.append(delimiter.join(["nom", "prenom", "date_naissance", "sexe", "telephone", "email"]))
    for row in rows:
        lines.append(delimiter.join(row))
    return "\n".join(lines).encode("utf-8")


class TestCsvImport:
    def test_import_valid_rows(self, client, auth_headers):
        data = _csv([
            ["ALAMI", "Sara", "1990-05-15", "F", "0612345678", "sara@test.dz"],
            ["BENALI", "Omar", "1985-03-22", "M", "", ""],
        ])
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("patients.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["created"] == 2
        assert body["skipped_duplicates"] == 0
        assert body["errors"] == []

    def test_import_detects_duplicates(self, client, auth_headers):
        data = _csv([["DUPTEST", "Lila", "1992-07-10", "F", "", ""]])
        r1 = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r1.json()["created"] == 1
        r2 = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r2.json()["created"] == 0
        assert r2.json()["skipped_duplicates"] == 1

    def test_import_invalid_date_reported_as_error(self, client, auth_headers):
        data = _csv([["ERREUR", "Test", "not-a-date", "M", "", ""]])
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["created"] == 0
        assert len(body["errors"]) == 1
        assert "date" in body["errors"][0]["reason"].lower()

    def test_import_missing_required_fields(self, client, auth_headers):
        data = b"nom;prenom;date_naissance;sexe\nALI;;1990-01-01;M\n"
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert len(r.json()["errors"]) >= 1

    def test_import_comma_delimiter(self, client, auth_headers):
        data = _csv([["COMMA", "Test", "1995-01-01", "M", "", ""]], delimiter=",")
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["created"] == 1

    def test_import_french_date_format(self, client, auth_headers):
        data = _csv([["DATEFR", "Alice", "15/08/1988", "F", "", ""]])
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["created"] == 1

    def test_import_unauthenticated_returns_401(self, client):
        data = _csv([["TEST", "User", "1990-01-01", "M", "", ""]])
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
        )
        assert r.status_code == 401

    def test_import_latin1_encoding(self, client, auth_headers):
        content = "nom;prenom;date_naissance;sexe\nDÉMO;René;1980-06-01;M\n"
        data = content.encode("latin-1")
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["created"] == 1

    def test_import_creates_dossier_clinique(self, client, db, auth_headers):
        """Each imported patient should have a DossierClinique record."""
        from backend import models

        data = _csv([["DOSSIER", "Check", "2000-01-01", "M", "", ""]])
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(data), "text/csv")},
            headers=auth_headers,
        )
        assert r.json()["created"] == 1

        pat = db.query(models.Patient).filter(
            models.Patient.nom == "DOSSIER",
            models.Patient.prenom == "Check",
        ).first()
        assert pat is not None
        dossier = db.query(models.DossierClinique).filter(
            models.DossierClinique.patient_id == pat.id
        ).first()
        assert dossier is not None
