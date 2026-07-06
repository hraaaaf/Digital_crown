"""Tests routers/stats.py — financial & operational stats endpoints."""
from datetime import datetime, timedelta


class TestFinancialStats:
    def test_requires_auth(self, client):
        r = client.get("/api/stats/financial")
        assert r.status_code == 401

    def test_empty_db_returns_zeros(self, client, auth_headers):
        r = client.get("/api/stats/financial", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "revenu_mois" in body
        assert "latent_cash" in body
        assert "top_relances" in body
        assert body["revenu_mois"] == 0.0
        assert body["latent_cash"] == 0.0
        assert isinstance(body["top_relances"], list)

    def test_with_paid_actes(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="STATSTEST", prenom="Paid",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        acte = models.Acte(
            patient_id=pat.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN,
            libelle="Consultation",
            montant=3000.0,
            statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now(),
            is_accounted=True,
        )
        db.add(acte)
        db.commit()

        r = client.get("/api/stats/financial", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["revenu_mois"] >= 3000.0

    def test_latent_cash_from_pending_actes(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="LATENTTEST", prenom="Cash",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        acte = models.Acte(
            patient_id=pat.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.PROTHESE,
            libelle="Devis Couronne",
            montant=8000.0,
            statut_paiement=models.PaiementStatut.EN_ATTENTE,
            date_debut=datetime.now(),
            is_accounted=False,
        )
        db.add(acte)
        db.commit()

        r = client.get("/api/stats/financial", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["latent_cash"] >= 8000.0

    def test_top_relances_populated(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="TOPRELANCE", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            telephone="0600000001",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        db.add(models.Acte(
            patient_id=pat.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.PROTHESE,
            libelle="Implant",
            montant=15000.0,
            statut_paiement=models.PaiementStatut.EN_ATTENTE,
            date_debut=datetime.now(),
            is_accounted=False,
        ))
        db.commit()

        r = client.get("/api/stats/financial", headers=auth_headers)
        assert r.status_code == 200
        relances = r.json()["top_relances"]
        assert len(relances) >= 1
        assert "nom" in relances[0]
        assert "montant" in relances[0]


class TestOperationalStats:
    def test_requires_auth(self, client):
        r = client.get("/api/stats/operational")
        assert r.status_code == 401

    def test_empty_db_returns_fields(self, client, auth_headers):
        r = client.get("/api/stats/operational", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "no_show_rate" in body
        assert "total_appts_week" in body
        assert "estimated_wait_time_minutes" in body
        assert "patients_en_salle" in body
        assert "flux_today" in body

    def test_no_show_rate_with_cancelled(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="NOSHOWTEST", prenom="Op",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        # 1 annulé + 1 confirmé dans la semaine glissante
        dt = datetime.now() - timedelta(days=2)
        db.add(models.Appointment(
            patient_id=pat.id,
            patient_name="NOSHOWTEST Op",
            datetime_start=dt,
            duration_minutes=30,
            status=models.AppointmentStatus.ANNULE,
            employer_id=dentiste.id,
        ))
        db.add(models.Appointment(
            patient_id=pat.id,
            patient_name="NOSHOWTEST Op",
            datetime_start=dt + timedelta(hours=2),
            duration_minutes=30,
            status=models.AppointmentStatus.TERMINE,
            employer_id=dentiste.id,
        ))
        db.commit()

        r = client.get("/api/stats/operational", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_appts_week"] >= 2
        assert body["no_show_rate"] > 0

    def test_wait_time_minimum_five_minutes(self, client, auth_headers):
        r = client.get("/api/stats/operational", headers=auth_headers)
        assert r.status_code == 200
        # estimated_wait_time = max(5, en_salle * 10), so always >= 5
        assert r.json()["estimated_wait_time_minutes"] >= 5
