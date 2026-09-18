from datetime import datetime, timedelta

import pytest

from backend.tests.conftest import make_user


def _make_patient(db, employer_id, nom="ORTHO"):
    from backend import models

    patient = models.Patient(
        nom=nom,
        prenom="Test",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _login(client, email, password="TestPass123!"):
    client.cookies.clear()
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_case(client, patient_id, headers, started_at=None, phase="DIAGNOSTIC"):
    started_at = started_at or datetime(2026, 9, 18, 9, 0, 0)
    return client.post(
        f"/api/patients/{patient_id}/ortho-case",
        headers=headers,
        json={
            "started_at": started_at.isoformat(),
            "initial_phase_key": phase,
        },
    )


class TestOrthoJourneyF1A:
    def test_create_get_and_start_event(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_CREATE")

        response = _create_case(client, patient.id, auth_headers)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["patient_id"] == patient.id
        assert body["lifecycle_status"] == "ACTIVE"
        assert body["current_phase_key"] == "DIAGNOSTIC"
        assert [event["event_type"] for event in body["events"]] == ["START"]
        assert body["events"][0]["phase_key"] == "DIAGNOSTIC"

        fetched = client.get(
            f"/api/patients/{patient.id}/ortho-case",
            headers=auth_headers,
        )
        assert fetched.status_code == 200
        assert fetched.json()["id"] == body["id"]

    def test_second_non_terminal_case_is_rejected(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_DUP")
        first = _create_case(client, patient.id, auth_headers)
        assert first.status_code == 201

        second = _create_case(
            client,
            patient.id,
            auth_headers,
            started_at=datetime(2026, 9, 18, 10, 0, 0),
        )
        assert second.status_code == 409

    def test_state_machine_phase_interrupt_resume_close_and_terminal_guard(
        self, client, db, dentiste, auth_headers
    ):
        patient = _make_patient(db, dentiste.id, "ORTHO_FLOW")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        phase = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "ENTER_PHASE",
                "effective_at": (start + timedelta(days=1)).isoformat(),
                "phase_key": "APPAREILLAGE",
            },
        )
        assert phase.status_code == 200, phase.text
        assert phase.json()["current_phase_key"] == "APPAREILLAGE"

        interrupted = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "INTERRUPT",
                "effective_at": (start + timedelta(days=2)).isoformat(),
            },
        )
        assert interrupted.status_code == 200
        assert interrupted.json()["lifecycle_status"] == "INTERRUPTED"

        resumed = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "RESUME",
                "effective_at": (start + timedelta(days=3)).isoformat(),
            },
        )
        assert resumed.status_code == 200
        assert resumed.json()["lifecycle_status"] == "ACTIVE"
        assert resumed.json()["current_phase_key"] == "APPAREILLAGE"

        closed = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "CLOSE",
                "effective_at": (start + timedelta(days=4)).isoformat(),
            },
        )
        assert closed.status_code == 200
        assert closed.json()["lifecycle_status"] == "CLOSED"
        assert closed.json()["closed_at"] is not None

        forbidden = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "RESUME",
                "effective_at": (start + timedelta(days=5)).isoformat(),
            },
        )
        assert forbidden.status_code == 409

    def test_transition_cannot_move_backwards_in_time(
        self, client, db, dentiste, auth_headers
    ):
        patient = _make_patient(db, dentiste.id, "ORTHO_TIME")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        ok = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "ENTER_PHASE",
                "effective_at": (start + timedelta(days=2)).isoformat(),
                "phase_key": "ALIGNEMENT",
            },
        )
        assert ok.status_code == 200

        backwards = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "INTERRUPT",
                "effective_at": (start + timedelta(days=1)).isoformat(),
            },
        )
        assert backwards.status_code == 409

    def test_cross_tenant_read_and_transition_are_blocked(self, client, db):
        doc_a = make_user(db, email="ortho-a@x.ma")
        doc_b = make_user(db, email="ortho-b@x.ma")
        patient = _make_patient(db, doc_a.id, "ORTHO_TENANT")

        headers_a = _login(client, doc_a.email)
        created = _create_case(client, patient.id, headers_a)
        assert created.status_code == 201
        case_id = created.json()["id"]

        headers_b = _login(client, doc_b.email)
        read = client.get(f"/api/patients/{patient.id}/ortho-case", headers=headers_b)
        assert read.status_code in (403, 404)

        mutate = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=headers_b,
            json={
                "event_type": "INTERRUPT",
                "effective_at": datetime(2026, 9, 19, 9, 0, 0).isoformat(),
            },
        )
        assert mutate.status_code in (403, 404)

    def test_secretary_can_read_same_tenant_but_cannot_mutate(self, client, db):
        owner = make_user(db, email="ortho-owner@x.ma")
        secretary = make_user(db, email="ortho-secretary@x.ma", role="SECRETAIRE")
        secretary.employer_id = owner.id
        db.commit()

        patient = _make_patient(db, owner.id, "ORTHO_RBAC")
        owner_headers = _login(client, owner.email)
        created = _create_case(client, patient.id, owner_headers)
        assert created.status_code == 201
        case_id = created.json()["id"]

        secretary_headers = _login(client, secretary.email)
        read = client.get(
            f"/api/patients/{patient.id}/ortho-case",
            headers=secretary_headers,
        )
        assert read.status_code == 200

        mutate = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=secretary_headers,
            json={
                "event_type": "INTERRUPT",
                "effective_at": datetime(2026, 9, 19, 9, 0, 0).isoformat(),
            },
        )
        assert mutate.status_code == 403

    def test_ortho_events_are_reused_by_existing_patient_journey(
        self, client, db, dentiste, auth_headers
    ):
        patient = _make_patient(db, dentiste.id, "ORTHO_JOURNEY")
        start = datetime.now() - timedelta(days=1)
        created = _create_case(client, patient.id, auth_headers, start)
        assert created.status_code == 201
        case_id = created.json()["id"]

        transitioned = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "ENTER_PHASE",
                "effective_at": datetime.now().isoformat(),
                "phase_key": "PREPARATION",
            },
        )
        assert transitioned.status_code == 200

        journey = client.get(
            f"/api/patients/{patient.id}/journey?full_history=true",
            headers=auth_headers,
        )
        assert journey.status_code == 200, journey.text
        ortho_events = [
            event for event in journey.json()["events"]
            if event["source"] == "ortho_phase_event"
        ]
        assert {event["type"] for event in ortho_events} >= {"START", "ENTER_PHASE"}
        assert any(event["phase_hint"] == "preparation" for event in ortho_events)

    def test_database_enforces_one_non_terminal_case(self, db, dentiste):
        from sqlalchemy.exc import IntegrityError
        from backend import models

        patient = _make_patient(db, dentiste.id, "ORTHO_DB_UNIQUE")
        first = models.OrthoCase(
            employer_id=dentiste.id,
            patient_id=patient.id,
            started_at=datetime(2026, 9, 18, 9, 0, 0),
            lifecycle_status="ACTIVE",
            created_by=dentiste.id,
        )
        db.add(first)
        db.commit()

        duplicate = models.OrthoCase(
            employer_id=dentiste.id,
            patient_id=patient.id,
            started_at=datetime(2026, 9, 19, 9, 0, 0),
            lifecycle_status="INTERRUPTED",
            created_by=dentiste.id,
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_database_rejects_invalid_lifecycle_status(self, db, dentiste):
        from sqlalchemy.exc import IntegrityError
        from backend import models

        patient = _make_patient(db, dentiste.id, "ORTHO_DB_CHECK")
        invalid = models.OrthoCase(
            employer_id=dentiste.id,
            patient_id=patient.id,
            started_at=datetime(2026, 9, 18, 9, 0, 0),
            lifecycle_status="IMPROVED",
            created_by=dentiste.id,
        )
        db.add(invalid)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_invalid_phase_contract_is_rejected_by_schema(
        self, client, db, dentiste, auth_headers
    ):
        patient = _make_patient(db, dentiste.id, "ORTHO_SCHEMA")
        created = _create_case(client, patient.id, auth_headers)
        case_id = created.json()["id"]

        missing_phase = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "ENTER_PHASE",
                "effective_at": datetime(2026, 9, 19, 9, 0, 0).isoformat(),
            },
        )
        assert missing_phase.status_code == 422

        stray_phase = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "INTERRUPT",
                "effective_at": datetime(2026, 9, 19, 9, 0, 0).isoformat(),
                "phase_key": "ALIGNEMENT",
            },
        )
        assert stray_phase.status_code == 422


class TestOrthoJourneyF1B:
    def test_create_and_list_structured_control(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_CONTROL")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        assert created.status_code == 201
        case_id = created.json()["id"]

        control = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
            json={
                "occurred_at": (start + timedelta(days=7)).isoformat(),
                "phase_key": "APPAREILLAGE",
                "note": "Arc contrôlé, note factuelle.",
                "next_control_at": (start + timedelta(days=35)).isoformat(),
            },
        )
        assert control.status_code == 201, control.text
        body = control.json()
        assert body["ortho_case_id"] == case_id
        assert body["phase_key"] == "APPAREILLAGE"
        assert body["note"] == "Arc contrôlé, note factuelle."

        listed = client.get(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
        )
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [body["id"]]

    def test_control_does_not_change_current_phase(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_CONTROL_PHASE")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start, phase="DIAGNOSTIC")
        case_id = created.json()["id"]

        control = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
            json={
                "occurred_at": (start + timedelta(days=1)).isoformat(),
                "phase_key": "ALIGNEMENT",
            },
        )
        assert control.status_code == 201

        fetched = client.get(
            f"/api/patients/{patient.id}/ortho-case",
            headers=auth_headers,
        )
        assert fetched.status_code == 200
        assert fetched.json()["current_phase_key"] == "DIAGNOSTIC"

    def test_terminal_case_rejects_new_control(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_CONTROL_TERMINAL")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        closed = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/transitions",
            headers=auth_headers,
            json={
                "event_type": "CLOSE",
                "effective_at": (start + timedelta(days=1)).isoformat(),
            },
        )
        assert closed.status_code == 200

        control = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
            json={
                "occurred_at": (start + timedelta(days=2)).isoformat(),
            },
        )
        assert control.status_code == 409

    def test_control_rejects_foreign_patient_appointment(self, client, db, dentiste, auth_headers):
        from backend import models

        patient = _make_patient(db, dentiste.id, "ORTHO_CONTROL_APPT_A")
        other = _make_patient(db, dentiste.id, "ORTHO_CONTROL_APPT_B")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        appointment = models.Appointment(
            patient_id=other.id,
            patient_name="Other",
            datetime_start=start + timedelta(days=1),
            duration_minutes=30,
            status=models.AppointmentStatus.PREVU,
            scheduling_type=models.SchedulingType.EXACT_TIME,
            employer_id=dentiste.id,
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        control = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
            json={
                "occurred_at": (start + timedelta(days=1)).isoformat(),
                "appointment_id": appointment.id,
            },
        )
        assert control.status_code == 422

    def test_control_next_date_cannot_precede_control(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_CONTROL_DATE")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        control = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
            json={
                "occurred_at": (start + timedelta(days=2)).isoformat(),
                "next_control_at": (start + timedelta(days=1)).isoformat(),
            },
        )
        assert control.status_code == 422

    def test_control_is_reused_by_existing_patient_journey(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_CONTROL_JOURNEY")
        start = datetime.now() - timedelta(days=3)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        control = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/controls",
            headers=auth_headers,
            json={
                "occurred_at": datetime.now().isoformat(),
                "phase_key": "FINITION",
            },
        )
        assert control.status_code == 201

        journey = client.get(
            f"/api/patients/{patient.id}/journey?full_history=true",
            headers=auth_headers,
        )
        assert journey.status_code == 200
        events = [
            event for event in journey.json()["events"]
            if event["source"] == "ortho_control"
        ]
        assert len(events) == 1
        assert events[0]["type"] == "CONTROLE"
        assert events[0]["phase_hint"] == "finition"


class TestOrthoJourneyF2:
    def test_create_list_t0_t1_and_unique_ordinal(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_TP")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        t0 = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 0, "occurred_at": start.isoformat(), "note": "Bilan initial"},
        )
        assert t0.status_code == 201, t0.text
        assert t0.json()["ordinal"] == 0

        t1 = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 1, "occurred_at": (start + timedelta(days=90)).isoformat()},
        )
        assert t1.status_code == 201, t1.text

        duplicate = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 1, "occurred_at": (start + timedelta(days=91)).isoformat()},
        )
        assert duplicate.status_code == 409

        listed = client.get(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
        )
        assert listed.status_code == 200
        assert [item["ordinal"] for item in listed.json()] == [0, 1]

    def test_timepoint_cannot_precede_case_start(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_TP_DATE")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        response = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 0, "occurred_at": (start - timedelta(days=1)).isoformat()},
        )
        assert response.status_code == 409

    def test_bind_clinical_asset_without_copying_or_relabeling(self, client, db, dentiste, auth_headers):
        from backend.models_media_core import ClinicalAsset

        patient = _make_patient(db, dentiste.id, "ORTHO_TP_ASSET")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        asset = ClinicalAsset(
            employer_id=dentiste.id,
            patient_id=patient.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
            original_filename="face.jpg",
            timepoint="T0",
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        tp = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 0, "occurred_at": start.isoformat()},
        )
        assert tp.status_code == 201
        timepoint_id = tp.json()["id"]

        link = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints/{timepoint_id}/evidences",
            headers=auth_headers,
            json={"clinical_asset_id": asset.id},
        )
        assert link.status_code == 201, link.text
        assert link.json()["clinical_asset_id"] == asset.id

        db.refresh(asset)
        assert asset.original_filename == "face.jpg"
        assert asset.timepoint == "T0"

    def test_reject_asset_with_conflicting_media_timepoint(self, client, db, dentiste, auth_headers):
        from backend.models_media_core import ClinicalAsset

        patient = _make_patient(db, dentiste.id, "ORTHO_TP_ASSET_CONFLICT")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        asset = ClinicalAsset(
            employer_id=dentiste.id,
            patient_id=patient.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
            timepoint="T2",
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        tp = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 1, "occurred_at": (start + timedelta(days=30)).isoformat()},
        )
        timepoint_id = tp.json()["id"]

        link = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints/{timepoint_id}/evidences",
            headers=auth_headers,
            json={"clinical_asset_id": asset.id},
        )
        assert link.status_code == 409

    def test_bind_cephalo_and_panoramic_by_reference(self, client, db, dentiste, auth_headers):
        from backend import models

        patient = _make_patient(db, dentiste.id, "ORTHO_TP_RADIO")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        ceph = models.CephaloAnalysis(
            patient_id=patient.id,
            image_original_path="cephalo.png",
            landmarks_data={},
            angles_data={"SNA": 82.0},
            is_calibrated=True,
            mm_per_pixel=0.2,
        )
        pano = models.PanoramicAnalysis(
            patient_id=patient.id,
            image_path="pano.png",
            detections_data={"teeth": []},
        )
        db.add_all([ceph, pano])
        db.commit()
        db.refresh(ceph)
        db.refresh(pano)

        tp = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 0, "occurred_at": start.isoformat()},
        )
        timepoint_id = tp.json()["id"]

        ceph_link = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints/{timepoint_id}/evidences",
            headers=auth_headers,
            json={"cephalo_analysis_id": ceph.id},
        )
        pano_link = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints/{timepoint_id}/evidences",
            headers=auth_headers,
            json={"panoramic_analysis_id": pano.id},
        )
        assert ceph_link.status_code == 201, ceph_link.text
        assert pano_link.status_code == 201, pano_link.text

        db.refresh(ceph)
        db.refresh(pano)
        assert ceph.angles_data == {"SNA": 82.0}
        assert pano.detections_data == {"teeth": []}

    def test_reject_cross_patient_evidence(self, client, db, dentiste, auth_headers):
        from backend.models_media_core import ClinicalAsset

        patient = _make_patient(db, dentiste.id, "ORTHO_TP_OWNER")
        other = _make_patient(db, dentiste.id, "ORTHO_TP_OTHER")
        start = datetime(2026, 9, 18, 9, 0, 0)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        foreign_asset = ClinicalAsset(
            employer_id=dentiste.id,
            patient_id=other.id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
        )
        db.add(foreign_asset)
        db.commit()
        db.refresh(foreign_asset)

        tp = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 0, "occurred_at": start.isoformat()},
        )
        timepoint_id = tp.json()["id"]

        link = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints/{timepoint_id}/evidences",
            headers=auth_headers,
            json={"clinical_asset_id": foreign_asset.id},
        )
        assert link.status_code == 422

    def test_timepoint_is_reused_by_existing_patient_journey(self, client, db, dentiste, auth_headers):
        patient = _make_patient(db, dentiste.id, "ORTHO_TP_JOURNEY")
        start = datetime.now() - timedelta(days=1)
        created = _create_case(client, patient.id, auth_headers, start)
        case_id = created.json()["id"]

        tp = client.post(
            f"/api/patients/{patient.id}/ortho-case/{case_id}/timepoints",
            headers=auth_headers,
            json={"ordinal": 0, "occurred_at": start.isoformat()},
        )
        assert tp.status_code == 201

        journey = client.get(
            f"/api/patients/{patient.id}/journey?full_history=true",
            headers=auth_headers,
        )
        assert journey.status_code == 200
        events = [e for e in journey.json()["events"] if e["source"] == "ortho_timepoint"]
        assert len(events) == 1
        assert events[0]["type"] == "T0"
