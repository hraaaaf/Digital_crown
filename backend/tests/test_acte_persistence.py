"""
Tests d'intégration pour UNIFY-ACT-PERSISTENCE-1 : génération automatique d'un `Acte`
par ligne facturée lors de la génération d'une note d'honoraires
(backend/routers/documents.py::generate_document). Fixtures réelles de conftest.py
(client, db, auth_headers). Exécuter avec : pytest backend/tests/test_acte_persistence.py -v
"""
import pytest
from backend import models

VALID_PATIENT = {
    "nom": "Actepat",
    "prenom": "Test",
    "date_naissance": "1988-04-20",
    "sexe": "M",
    "telephone": "0612345679",
}


def _make_patient(client, auth_headers, nom="Actepat"):
    payload = dict(VALID_PATIENT, nom=nom)
    resp = client.post("/api/patients/", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


@pytest.mark.anyio
class TestActePersistenceOnNoteHonoraires:
    def test_multi_items_paye_creates_one_acte_per_line(self, client, auth_headers, db):
        patient_id = _make_patient(client, auth_headers, "MULTIITEM")
        req_data = {
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [
                    {"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 400.0, "mode_reglement": "ESPECES"},
                    {"date": "2026-05-18", "acte": "Couronne céramique", "dent": "36", "montant": 2500.0, "mode_reglement": "ESPECES"},
                ],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp.status_code == 200, resp.text

        doc = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        ).first()
        assert doc is not None

        actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).order_by(models.Acte.montant).all()
        assert len(actes) == 2

        detartrage, couronne = actes
        assert detartrage.libelle == "Détartrage"
        assert detartrage.montant == 400.0
        assert detartrage.type_acte == models.ActeType.SOIN
        assert detartrage.statut_paiement == models.PaiementStatut.PAYE
        assert detartrage.document_archive_id == doc.id

        assert couronne.libelle == "Couronne céramique"
        assert couronne.montant == 2500.0
        assert couronne.type_acte == models.ActeType.PROTHESE
        assert couronne.statut_paiement == models.PaiementStatut.PAYE
        assert couronne.document_archive_id == doc.id

    def test_partiel_status_propagated_payment_lump_sum_unchanged(self, client, auth_headers, db):
        patient_id = _make_patient(client, auth_headers, "PARTIELPAT")
        req_data = {
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "PARTIEL",
            "data": {
                "payments": [
                    {"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 1000.0, "mode_reglement": "ESPECES"},
                ],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp.status_code == 200, resp.text

        acte = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).first()
        assert acte is not None
        assert acte.statut_paiement == models.PaiementStatut.PARTIEL
        assert acte.is_collected is False

        # Le Payment lump-sum existant reste inchangé (comportement pré-mission : total/2.0)
        payment = db.query(models.Payment).filter(models.Payment.patient_id == patient_id).first()
        assert payment is not None
        assert payment.amount == 500.0
        assert payment.acte_id is None  # décision Option B : pas de rattachement Payment<->Acte

    def test_devis_creates_no_acte(self, client, auth_headers, db):
        patient_id = _make_patient(client, auth_headers, "DEVISPAT")
        req_data = {
            "type": "devis",
            "patient_id": patient_id,
            "is_accounted": True,
            "data": {
                "items": [
                    {"acte": "Couronne céramique", "dent": "36", "prix_unitaire": 2500.0},
                ],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp.status_code == 200, resp.text

        assert db.query(models.Acte).filter(models.Acte.patient_id == patient_id).count() == 0

    def test_global_note_with_installments_creates_actes_en_attente(self, client, auth_headers, db):
        patient_id = _make_patient(client, auth_headers, "GLOBALPAT")
        req_data = {
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
            "data": {
                "is_global_note": True,
                "payments": [
                    {"date": "2026-05-18", "acte": "Semestre ODF multibagues", "dent": "-", "montant": 1500.0, "mode_reglement": "ESPECES"},
                ],
                "installments": [
                    {"date": "2026-06-01", "amount": 750.0, "label": "Versement 1"},
                    {"date": "2026-07-01", "amount": 750.0, "label": "Versement 2"},
                ],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp.status_code == 200, resp.text

        acte = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).first()
        assert acte is not None
        assert acte.statut_paiement == models.PaiementStatut.EN_ATTENTE
        assert acte.type_acte == models.ActeType.ORTHO_SEMESTRE

        # Non-régression : le plan d'échéances est toujours créé comme avant
        plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.patient_id == patient_id).first()
        assert plan is not None
        assert plan.total_amount == 1500.0
        installments = db.query(models.Installment).filter(models.Installment.plan_id == plan.id).all()
        assert len(installments) == 2

    def test_forced_regeneration_creates_second_acte_set(self, client, auth_headers, db):
        patient_id = _make_patient(client, auth_headers, "REGENPAT")
        req_data = {
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [
                    {"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 400.0, "mode_reglement": "TPE"},
                ],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp1 = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp1.status_code == 200, resp1.text

        resp2 = client.post("/api/documents/generate?force=true", json=req_data, headers=auth_headers)
        assert resp2.status_code == 200, resp2.text

        docs = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        ).order_by(models.DocumentArchive.version_number).all()
        assert len(docs) == 2

        actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).all()
        assert len(actes) == 2  # un Acte par version, pas de fusion
        actes_doc_ids = sorted(a.document_archive_id for a in actes)
        assert actes_doc_ids == sorted(d.id for d in docs)
