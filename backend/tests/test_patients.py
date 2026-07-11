"""Tests d'intégration — CRUD patients."""
import pytest


VALID_PATIENT = {
    "nom": "Benali",
    "prenom": "Sara",
    "date_naissance": "1990-05-15",
    "sexe": "F",
    "telephone": "0612345678",
}


class TestCreatePatient:
    def test_create_patient_success(self, client, auth_headers):
        resp = client.post("/api/patients/", json=VALID_PATIENT, headers=auth_headers)
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["nom"] == "BENALI"        # backend normalise en majuscules
        assert body["prenom"] == "Sara"
        assert "id" in body

    def test_create_patient_unauthenticated(self, client):
        resp = client.post("/api/patients/", json=VALID_PATIENT)
        assert resp.status_code == 401

    def test_create_patient_missing_required_field(self, client, auth_headers):
        bad = {k: v for k, v in VALID_PATIENT.items() if k != "nom"}
        resp = client.post("/api/patients/", json=bad, headers=auth_headers)
        assert resp.status_code == 422


class TestListPatients:
    def test_list_returns_empty_initially(self, client, auth_headers):
        resp = client.get("/api/patients/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_contains_created_patient(self, client, auth_headers):
        client.post("/api/patients/", json=VALID_PATIENT, headers=auth_headers)
        resp = client.get("/api/patients/", headers=auth_headers)
        noms = [p["nom"] for p in resp.json()]
        assert "BENALI" in noms

    def test_list_unauthenticated(self, client):
        resp = client.get("/api/patients/")
        assert resp.status_code == 401


class TestGetPatient:
    def _create(self, client, auth_headers):
        r = client.post("/api/patients/", json=VALID_PATIENT, headers=auth_headers)
        return r.json()["id"]

    def test_get_existing_patient(self, client, auth_headers):
        pid = self._create(client, auth_headers)
        resp = client.get(f"/api/patients/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        resp = client.get("/api/patients/999999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_unauthenticated(self, client, auth_headers):
        pid = self._create(client, auth_headers)
        client.cookies.clear()  # drop cookie set during auth_headers login
        resp = client.get(f"/api/patients/{pid}")
        assert resp.status_code == 401


class TestUpdatePatient:
    def _create(self, client, auth_headers):
        r = client.post("/api/patients/", json=VALID_PATIENT, headers=auth_headers)
        return r.json()["id"]

    def test_update_nom(self, client, auth_headers):
        pid = self._create(client, auth_headers)
        # Envoie uniquement le champ modifié (exclude_unset côté Pydantic)
        resp = client.put(
            f"/api/patients/{pid}",
            json={"nom": "Alami"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "ALAMI"   # backend normalise en majuscules

    def test_update_unauthenticated(self, client, auth_headers):
        pid = self._create(client, auth_headers)
        client.cookies.clear()  # drop cookie set during auth_headers login
        resp = client.put(f"/api/patients/{pid}", json={**VALID_PATIENT, "nom": "X"})
        assert resp.status_code == 401


class TestMultiTenantIsolation:
    """Un médecin ne doit pas voir les patients d'un autre."""

    def test_doctor_b_cannot_see_doctor_a_patient(self, client, db):
        from backend import models
        from backend.security import get_password_hash

        doc_a = models.User(email="a@x.ma", hashed_password=get_password_hash("Pass123!"), role="DENTISTE", is_active=True, is_licensed=True)
        doc_b = models.User(email="b@x.ma", hashed_password=get_password_hash("Pass123!"), role="DENTISTE", is_active=True, is_licensed=True)
        db.add_all([doc_a, doc_b])
        db.commit()

        # Use cookie-based auth: login sets access_token cookie, no explicit header needed.
        # get_current_user prioritises the cookie, so we clear between sessions.
        client.cookies.clear()
        client.post("/api/auth/login", data={"username": "a@x.ma", "password": "Pass123!"})
        r = client.post("/api/patients/", json=VALID_PATIENT)
        pid = r.json()["id"]

        client.cookies.clear()
        client.post("/api/auth/login", data={"username": "b@x.ma", "password": "Pass123!"})
        resp = client.get(f"/api/patients/{pid}")
        assert resp.status_code in (403, 404)


# --- TREATMENT JOURNEY ---

def _make_patient(db, employer_id, nom="JOURNEY"):
    from backend import models
    from datetime import datetime as _dt
    pat = models.Patient(
        nom=nom, prenom="Test", date_naissance=_dt(1990, 1, 1), sexe="M",
        employer_id=employer_id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _make_document(db, patient_id, document_type="DEVIS", created_at=None):
    from backend import models
    from datetime import datetime as _dt
    import uuid as _uuid
    doc = models.DocumentArchive(
        patient_id=patient_id,
        document_type=document_type,
        filename="test.pdf",
        original_filename="test.pdf",
        document_group_id=_uuid.uuid4().hex,
        file_hash=_uuid.uuid4().hex,
        file_size=100,
        file_path="/tmp/test.pdf",
        created_at=created_at or _dt.now(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_treatment_step(db, patient_id, status="pending"):
    from backend import models
    plan = db.query(models.TreatmentMasterPlan).filter(models.TreatmentMasterPlan.patient_id == patient_id).first()
    if plan is None:
        plan = models.TreatmentMasterPlan(patient_id=patient_id)
        db.add(plan)
        db.commit()
        db.refresh(plan)
    step = models.TreatmentPlanStep(
        plan_id=plan.id, title="Detartrage", assistant="dentiste", status=status, date_str="", order_index=0,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def _make_milestone(db, patient_id, employer_id, milestone_type="DIAGNOSTIC", milestone_date=None, note=None):
    from backend import models
    from datetime import datetime as _dt
    m = models.JourneyMilestone(
        patient_id=patient_id, employer_id=employer_id, milestone_type=milestone_type,
        milestone_date=milestone_date or _dt.now(), note=note,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


class TestPatientJourneyTenantIsolation:
    def test_cross_tenant_get_and_delete_blocked(self, client, db):
        from backend import models
        from backend.security import get_password_hash

        doc_a = models.User(email="ja@x.ma", hashed_password=get_password_hash("Pass123!"), role="DENTISTE", is_active=True, is_licensed=True)
        doc_b = models.User(email="jb@x.ma", hashed_password=get_password_hash("Pass123!"), role="DENTISTE", is_active=True, is_licensed=True)
        db.add_all([doc_a, doc_b])
        db.commit()
        db.refresh(doc_a)

        pat = _make_patient(db, doc_a.id)
        milestone = _make_milestone(db, pat.id, doc_a.id)

        client.cookies.clear()
        client.post("/api/auth/login", data={"username": "jb@x.ma", "password": "Pass123!"})
        resp = client.get(f"/api/patients/{pat.id}/journey")
        assert resp.status_code in (403, 404)

        resp = client.delete(f"/api/patients/{pat.id}/journey/milestones/{milestone.id}")
        assert resp.status_code in (403, 404)


class TestPatientJourneyAggregation:
    def test_aggregation_returns_all_sources(self, db, dentiste):
        from backend import models
        from backend.services import patient_journey_service

        pat = _make_patient(db, dentiste.id, "AGGREG")
        payment = models.Payment(patient_id=pat.id, amount=100.0, payment_method="ESPECES")
        db.add(payment)
        db.commit()
        db.refresh(payment)
        doc = _make_document(db, pat.id, "DEVIS")
        step = _make_treatment_step(db, pat.id)
        milestone = _make_milestone(db, pat.id, dentiste.id)

        result = patient_journey_service.build_journey(db, pat.id, dentiste.id)
        keys = {e.event_key for e in result.events}
        assert f"payment:{payment.id}" in keys
        assert f"document_archive:{doc.id}" in keys
        assert f"treatment_plan_step:{step.id}" in keys
        assert f"journey_milestone:{milestone.id}" in keys

    def test_deterministic_sort_stable_across_calls(self, db, dentiste):
        from backend import models
        from backend.services import patient_journey_service
        from datetime import datetime as _dt

        pat = _make_patient(db, dentiste.id, "SORT")
        same_date = _dt(2026, 1, 1, 10, 0, 0)
        _make_document(db, pat.id, "DEVIS", created_at=same_date)
        _make_milestone(db, pat.id, dentiste.id, milestone_date=same_date)

        first = [e.event_key for e in patient_journey_service.build_journey(db, pat.id, dentiste.id).events]
        second = [e.event_key for e in patient_journey_service.build_journey(db, pat.id, dentiste.id).events]
        assert first == second

    def test_window_12_months_excludes_old_unless_full_history(self, db, dentiste):
        from backend.services import patient_journey_service
        from datetime import datetime as _dt, timedelta as _td

        pat = _make_patient(db, dentiste.id, "WINDOW")
        old_date = _dt.now() - _td(days=400)  # > 12 mois
        old_doc = _make_document(db, pat.id, "DEVIS", created_at=old_date)

        default_result = patient_journey_service.build_journey(db, pat.id, dentiste.id, full_history=False)
        assert f"document_archive:{old_doc.id}" not in {e.event_key for e in default_result.events}

        full_result = patient_journey_service.build_journey(db, pat.id, dentiste.id, full_history=True)
        assert f"document_archive:{old_doc.id}" in {e.event_key for e in full_result.events}

    def test_open_items_always_included_despite_age(self, db, dentiste):
        from backend.services import patient_journey_service
        from datetime import datetime as _dt

        pat = _make_patient(db, dentiste.id, "OPEN")
        step = _make_treatment_step(db, pat.id, status="pending")
        # Le plan a été mis à jour au moment de la création — force une date ancienne
        from backend import models
        plan = db.query(models.TreatmentMasterPlan).filter(models.TreatmentMasterPlan.patient_id == pat.id).first()
        plan.updated_at = _dt.now() - __import__("datetime").timedelta(days=420)
        db.commit()

        result = patient_journey_service.build_journey(db, pat.id, dentiste.id, full_history=False)
        assert f"treatment_plan_step:{step.id}" in {e.event_key for e in result.events}

    def test_full_history_capped_at_500(self, db, dentiste):
        from backend.services import patient_journey_service

        pat = _make_patient(db, dentiste.id, "CAPPED")
        for _ in range(510):
            _make_milestone(db, pat.id, dentiste.id, milestone_type="CONTROLE")

        result = patient_journey_service.build_journey(db, pat.id, dentiste.id, full_history=True)
        assert len(result.events) == 500
        assert result.truncated is True
        assert result.total_events_available == 510

    def test_legacy_acte_does_not_crash_aggregation(self, db, dentiste):
        from backend import models
        from backend.services import patient_journey_service
        from datetime import datetime as _dt

        pat = _make_patient(db, dentiste.id, "LEGACY")
        db.add(models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN, libelle="Detartrage",
            montant=100.0, statut_paiement=models.PaiementStatut.PAYE,
            date_debut=_dt.now(),
        ))
        db.commit()

        result = patient_journey_service.build_journey(db, pat.id, dentiste.id)
        assert not any(e.source == "acte" for e in result.events)

    def test_query_count_stays_constant_regardless_of_event_volume(self, db, dentiste):
        from backend import database
        from backend.services import patient_journey_service
        from sqlalchemy import event as sa_event

        pat_small = _make_patient(db, dentiste.id, "QSMALL")
        for _ in range(3):
            _make_milestone(db, pat_small.id, dentiste.id)

        pat_big = _make_patient(db, dentiste.id, "QBIG")
        for _ in range(50):
            _make_milestone(db, pat_big.id, dentiste.id)

        # Fige les ids en entiers avant d'attacher le listener : sinon l'accès à un
        # attribut expiré (session expire_on_commit=True) déclenche un SELECT "fantôme"
        # comptabilisé à tort comme une requête du service.
        employer_id = int(dentiste.id)
        small_id = int(pat_small.id)
        big_id = int(pat_big.id)

        counts = {}

        def _make_counter(key):
            def _listener(conn, cursor, statement, parameters, context, executemany):
                counts[key] = counts.get(key, 0) + 1
            return _listener

        listener_small = _make_counter("small")
        sa_event.listen(database.engine, "before_cursor_execute", listener_small)
        try:
            patient_journey_service.build_journey(db, small_id, employer_id)
        finally:
            sa_event.remove(database.engine, "before_cursor_execute", listener_small)

        listener_big = _make_counter("big")
        sa_event.listen(database.engine, "before_cursor_execute", listener_big)
        try:
            patient_journey_service.build_journey(db, big_id, employer_id)
        finally:
            sa_event.remove(database.engine, "before_cursor_execute", listener_big)

        assert counts["small"] == counts["big"], "le nombre de requêtes ne doit pas dépendre du volume d'événements (pas de N+1)"


class TestPatientJourneyMilestones:
    def test_create_milestone_writes_audit_log(self, client, auth_headers, dentiste, db):
        pat = _make_patient(db, dentiste.id, "CREATE")
        resp = client.post(
            f"/api/patients/{pat.id}/journey/milestones",
            json={"milestone_type": "DEVIS_VALIDE", "milestone_date": "2026-07-10T10:00:00"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["milestone"]["milestone_type"] == "DEVIS_VALIDE"

        from backend import models
        log = db.query(models.AuditLog).filter(
            models.AuditLog.resource_type == "JourneyMilestone", models.AuditLog.action == "CREATE",
        ).first()
        assert log is not None
        assert "note_present" in log.details

    def test_soft_delete_excludes_from_journey_but_keeps_row(self, client, auth_headers, dentiste, db):
        pat = _make_patient(db, dentiste.id, "SOFTDEL")
        milestone = _make_milestone(db, pat.id, dentiste.id, milestone_type="CONTROLE")

        resp = client.delete(f"/api/patients/{pat.id}/journey/milestones/{milestone.id}", headers=auth_headers)
        assert resp.status_code == 200

        from backend import models
        row = db.query(models.JourneyMilestone).filter(models.JourneyMilestone.id == milestone.id).first()
        assert row is not None
        assert row.deleted_at is not None
        assert row.deleted_by is not None

        journey_resp = client.get(f"/api/patients/{pat.id}/journey", headers=auth_headers)
        keys = {e["event_key"] for e in journey_resp.json()["events"]}
        assert f"journey_milestone:{milestone.id}" not in keys

        log = db.query(models.AuditLog).filter(
            models.AuditLog.resource_type == "JourneyMilestone", models.AuditLog.action == "DELETE",
        ).first()
        assert log is not None
        assert "note_present" in log.details

    def test_permissions_secretaire_blocked_on_physician_only_types(self, client, db):
        from backend import models
        from backend.security import get_password_hash

        dentiste_owner = models.User(email="owner@x.ma", hashed_password=get_password_hash("Pass123!"), role="DENTISTE", is_active=True, is_licensed=True)
        db.add(dentiste_owner)
        db.commit()
        db.refresh(dentiste_owner)

        secretaire = models.User(
            email="sec@x.ma", hashed_password=get_password_hash("Pass123!"), role="SECRETAIRE",
            is_active=True, is_licensed=True, employer_id=dentiste_owner.id,
            permissions={"patients": True},
        )
        db.add(secretaire)
        db.commit()

        pat = _make_patient(db, dentiste_owner.id, "PERM")

        client.cookies.clear()
        client.post("/api/auth/login", data={"username": "sec@x.ma", "password": "Pass123!"})

        resp = client.get(f"/api/patients/{pat.id}/journey")
        assert resp.status_code == 200

        for milestone_type in ("DIAGNOSTIC", "CONTROLE", "CLOTURE"):
            resp = client.post(
                f"/api/patients/{pat.id}/journey/milestones",
                json={"milestone_type": milestone_type, "milestone_date": "2026-07-10T10:00:00"},
            )
            assert resp.status_code == 403, milestone_type

    def test_permissions_accounting_can_validate_devis(self, client, db):
        from backend import models
        from backend.security import get_password_hash

        dentiste_owner = models.User(email="owner2@x.ma", hashed_password=get_password_hash("Pass123!"), role="DENTISTE", is_active=True, is_licensed=True)
        db.add(dentiste_owner)
        db.commit()
        db.refresh(dentiste_owner)

        accountant = models.User(
            email="acct@x.ma", hashed_password=get_password_hash("Pass123!"), role="SECRETAIRE",
            is_active=True, is_licensed=True, employer_id=dentiste_owner.id,
            permissions={"patients": True, "accounting": True},
        )
        db.add(accountant)
        db.commit()

        pat = _make_patient(db, dentiste_owner.id, "PERMACC")

        client.cookies.clear()
        client.post("/api/auth/login", data={"username": "acct@x.ma", "password": "Pass123!"})

        resp = client.post(
            f"/api/patients/{pat.id}/journey/milestones",
            json={"milestone_type": "DEVIS_VALIDE", "milestone_date": "2026-07-10T10:00:00"},
        )
        assert resp.status_code == 201

    def test_duplicate_contract_functional(self, client, auth_headers, dentiste, db):
        pat = _make_patient(db, dentiste.id, "DUP")
        payload = {"milestone_type": "CLOTURE", "milestone_date": "2026-07-10T10:00:00", "note": "fin"}

        first = client.post(f"/api/patients/{pat.id}/journey/milestones", json=payload, headers=auth_headers)
        assert first.status_code == 201

        second = client.post(f"/api/patients/{pat.id}/journey/milestones", json=payload, headers=auth_headers)
        assert second.status_code == 200
        body = second.json()
        assert body["possible_duplicate"] is True
        assert body["milestone"] is None

        forced = client.post(
            f"/api/patients/{pat.id}/journey/milestones",
            json={**payload, "confirm_duplicate": True},
            headers=auth_headers,
        )
        assert forced.status_code == 201
        assert forced.json()["possible_duplicate"] is True

    @pytest.mark.skip(reason="Verrou SELECT...FOR UPDATE concurrent — n'a de sens que sur PostgreSQL "
                              "(rehearsal), SQLite ne sérialise pas FOR UPDATE en connexions concurrentes. "
                              "Réservé à la Phase B du gate de rollout (voir docs/TREATMENT_JOURNEY_DESIGN.md).")
    def test_concurrent_duplicate_creation_serialized_on_postgres(self):
        pass
