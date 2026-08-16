import pytest
from backend import models
from backend.routers import documents as documents_router

VALID_PATIENT = {
    "nom": "Ait",
    "prenom": "Yassine",
    "date_naissance": "1988-04-20",
    "sexe": "M",
    "telephone": "0612345678",
}


@pytest.mark.anyio
class TestHonorairesArchive:

    def test_note_honoraires_tpe_mapping_and_archiving(
        self,
        client,
        auth_headers,
        db,
        monkeypatch,
        tmp_path,
    ):
        # Isoler les PDF du test et garantir un nom unique à chaque génération.
        # Le test cible ainsi le conflit métier d'archive, pas une collision
        # de fichier liée à deux générations exécutées dans la même seconde.
        sequence = iter(range(1, 10))

        def unique_test_path(patient, prefix, data, doc_id=None):
            return str(tmp_path / f"{prefix}_{patient.id}_{next(sequence)}.pdf")

        monkeypatch.setattr(
            documents_router.doc_factory.acc_gen,
            "_get_save_path",
            unique_test_path,
        )

        # 1. Créer un patient
        resp_patient = client.post("/api/patients/", json=VALID_PATIENT, headers=auth_headers)
        assert resp_patient.status_code in (200, 201), resp_patient.text
        patient_id = resp_patient.json()["id"]

        # 2. Préparer les données pour la note d'honoraires avec règlement "TPE"
        req_data = {
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [
                    {
                        "date": "2026-05-18",
                        "acte": "Détartrage",
                        "dent": "-",
                        "montant": 400.0,
                        "mode_reglement": "TPE",
                    }
                ],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }

        # 3. Appeler /api/documents/generate pour générer et archiver
        resp_gen = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_gen.status_code == 200, resp_gen.text
        assert "pdf_url" in resp_gen.json()

        # 4. Vérifier que l'encaissement a bien été créé avec le mode CARTE
        payment_db = db.query(models.Payment).filter(models.Payment.patient_id == patient_id).first()
        assert payment_db is not None
        assert payment_db.amount == 400.0
        assert payment_db.payment_method == models.PaymentMethod.CARTE

        # 5. Sans force, le doublon est un conflit métier HTTP 409.
        resp_conflict = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_conflict.status_code == 409, resp_conflict.text
        assert resp_conflict.json()["detail"]["code"] == "DOUBLE_DETECTED"

        docs_before_force = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        ).all()
        assert len(docs_before_force) == 1

        # 6. Avec force=True, créer explicitement une nouvelle version.
        resp_forced = client.post("/api/documents/generate?force=true", json=req_data, headers=auth_headers)
        assert resp_forced.status_code == 200, resp_forced.text
        assert "pdf_url" in resp_forced.json()

        # 7. Une régénération forcée préserve l'historique et incrémente la version.
        docs = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        ).order_by(models.DocumentArchive.version_number).all()
        assert len(docs) == 2
        assert [d.version_number for d in docs] == [1, 2]
        assert docs[0].is_latest_version is False
        assert docs[1].is_latest_version is True
