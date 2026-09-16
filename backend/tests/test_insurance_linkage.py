from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from backend import models
from backend.models_insurance_linkage import (
    migrate_insurance_linkage_columns,
    rollback_insurance_linkage_columns,
)


def _make_patient(client, auth_headers, name):
    response = client.post(
        "/api/patients/",
        json={
            "nom": name,
            "prenom": "Insurance",
            "date_naissance": "1990-01-01",
            "sexe": "M",
            "telephone": "0612345678",
        },
        headers=auth_headers,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def test_new_honoraires_line_persists_same_uid_in_archive_and_acte(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers, "LINKUID")
    response = client.post(
        "/api/documents/generate",
        json={
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
            "data": {
                "payments": [{
                    "date": "2026-09-14",
                    "acte": "Detartrage",
                    "dent": "11",
                    "montant": 500.0,
                }],
                "doc_date": "2026-09-14",
                "teeth_data": [],
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text

    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).one()
    acte = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).one()
    snapshot_uid = doc.clinical_data["payments"][0]["source_line_uid"]

    assert snapshot_uid
    assert acte.source_line_uid == snapshot_uid
    assert acte.catalog_act_id is None


def test_unknown_catalog_act_fails_closed_and_rolls_back(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers, "BADCAT")
    response = client.post(
        "/api/documents/generate",
        json={
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
            "data": {
                "payments": [{
                    "date": "2026-09-14",
                    "acte": "Detartrage",
                    "dent": "11",
                    "montant": 500.0,
                    "catalog_act_id": 999999,
                }],
                "doc_date": "2026-09-14",
                "teeth_data": [],
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 422, response.text
    assert "CatalogAct introuvable ou inactif" in response.text
    assert db.query(models.Acte).filter(models.Acte.patient_id == patient_id).count() == 0
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id
    ).count() == 0


def test_additive_migration_and_physical_rollback_preserve_existing_row():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE catalog_acts (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE actes (id INTEGER PRIMARY KEY, libelle VARCHAR(255))"))
        connection.execute(text("INSERT INTO actes (id, libelle) VALUES (7, 'Legacy')"))

    migrate_insurance_linkage_columns(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("actes")}
    assert {"source_line_uid", "catalog_act_id"}.issubset(columns)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT id FROM actes")).scalar_one() == 7

    rollback_insurance_linkage_columns(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("actes")}
    assert "source_line_uid" not in columns
    assert "catalog_act_id" not in columns
    with engine.connect() as connection:
        assert connection.execute(text("SELECT id FROM actes")).scalar_one() == 7
