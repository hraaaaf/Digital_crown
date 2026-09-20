from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionConsentRequest,
    PatientCompanionIdentity,
    PatientCompanionQuestionnaireAssignment,
    PatientCompanionQuestionnaireDefinition,
    PatientCompanionQuestionnaireSubmission,
    PatientCompanionShareGrant,
)
from backend.models_patient_companion_notifications import (
    PatientCompanionNotificationPreference,
    PatientCompanionNotificationReceipt,
)
from backend.services.patient_companion_notifications import (
    handle_notification_preferences,
    handle_notification_read,
    handle_notification_snooze,
    project_notifications,
)


def _patient_access(db, dentiste, suffix: str):
    patient = models.Patient(
        numero_dossier=f"PC05-{suffix}-{uuid.uuid4().hex[:6]}",
        nom=f"Patient-{suffix}",
        prenom="Aya",
        date_naissance=datetime(2012, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{suffix}:{uuid.uuid4()}",
    )
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()
    return patient, identity, access


def _document_share(db, dentiste, patient, tmp_path, title: str):
    raw = b"%PDF-1.4\nPC05 fixture\n%%EOF\n"
    path = tmp_path / f"{uuid.uuid4()}.pdf"
    path.write_bytes(raw)
    document = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.DOCUMENT_LIBRE,
        filename=path.name,
        original_filename=path.name,
        document_group_id=uuid.uuid4().hex,
        version_number=1,
        is_latest_version=True,
        file_hash=hashlib.sha256(raw).hexdigest(),
        file_size=len(raw),
        file_path=str(path),
        title=title,
        status=models.DocumentStatus.ACTIF,
    )
    db.add(document)
    db.flush()
    share = PatientCompanionShareGrant(
        employer_id=dentiste.id,
        patient_id=patient.id,
        resource_type="document",
        resource_id=document.id,
        granted_by_user_id=dentiste.id,
    )
    db.add(share)
    db.flush()
    return document, share


def test_pc05_projection_is_deterministic_and_uses_canonical_sources(db, dentiste, tmp_path):
    patient, _identity, access = _patient_access(db, dentiste, "A")
    now = datetime.utcnow()

    appointment = models.Appointment(
        patient_id=patient.id,
        employer_id=dentiste.id,
        datetime_start=now + timedelta(days=1),
        duration_minutes=30,
        status=models.AppointmentStatus.CONFIRME,
        motif="Contrôle",
    )
    db.add(appointment)

    document, share = _document_share(db, dentiste, patient, tmp_path, "Consentement traitement")
    consent = PatientCompanionConsentRequest(
        employer_id=dentiste.id,
        patient_id=patient.id,
        document_id=document.id,
        share_grant_id=share.id,
        document_group_id=str(document.document_group_id),
        document_version=1,
        document_file_hash=str(document.file_hash),
        document_file_size=int(document.file_size),
        created_by_user_id=dentiste.id,
        status="PENDING",
    )
    definition = PatientCompanionQuestionnaireDefinition(
        employer_id=dentiste.id,
        lineage_key=str(uuid.uuid4()),
        version=1,
        title="Questionnaire médical",
        questions_json="[]",
        status="ACTIVE",
    )
    db.add_all([consent, definition])
    db.flush()
    assignment = PatientCompanionQuestionnaireAssignment(
        employer_id=dentiste.id,
        patient_id=patient.id,
        questionnaire_id=definition.id,
        created_by_user_id=dentiste.id,
        status="ASSIGNED",
    )
    db.add(assignment)
    db.commit()

    first = project_notifications(db, access, now=now)
    second = project_notifications(db, access, now=now)

    assert first == second
    assert len(first["items"]) == 3
    assert {item["kind"] for item in first["items"]} == {
        "APPOINTMENT_REMINDER",
        "CONSENT_PENDING",
        "QUESTIONNAIRE_PENDING",
    }
    assert all("source_key" not in item for item in first["items"])
    assert len({item["notification_id"] for item in first["items"]}) == 3
    # The shared document is represented once as the more specific pending consent,
    # never as a second generic document alert.
    assert not any(item["kind"] == "DOCUMENT_SHARED" for item in first["items"])


def test_pc05_projection_is_isolated_per_patient_and_access(db, dentiste):
    patient_a, _identity_a, access_a = _patient_access(db, dentiste, "A")
    patient_b, _identity_b, access_b = _patient_access(db, dentiste, "B")
    now = datetime.utcnow()
    db.add_all([
        models.Appointment(
            patient_id=patient_a.id,
            employer_id=dentiste.id,
            datetime_start=now + timedelta(hours=12),
            status=models.AppointmentStatus.CONFIRME,
        ),
        models.Appointment(
            patient_id=patient_b.id,
            employer_id=dentiste.id,
            datetime_start=now + timedelta(hours=18),
            status=models.AppointmentStatus.CONFIRME,
        ),
    ])
    db.commit()

    items_a = project_notifications(db, access_a, now=now)["items"]
    items_b = project_notifications(db, access_b, now=now)["items"]
    assert len(items_a) == 1
    assert len(items_b) == 1
    assert items_a[0]["notification_id"] != items_b[0]["notification_id"]


def test_pc05_read_and_snooze_only_change_receipt_after_domain_acceptance(db, dentiste):
    patient, _identity, access = _patient_access(db, dentiste, "R")
    now = datetime.utcnow()
    db.add(models.Appointment(
        patient_id=patient.id,
        employer_id=dentiste.id,
        datetime_start=now + timedelta(hours=8),
        status=models.AppointmentStatus.CONFIRME,
    ))
    db.commit()

    item = project_notifications(db, access, now=now)["items"][0]
    snoozed = handle_notification_snooze(
        db,
        access,
        {"notification_id": item["notification_id"]},
    )
    assert snoozed.status == "ACCEPTED"
    db.commit()
    assert project_notifications(db, access, now=datetime.utcnow())["items"] == []

    receipt = db.query(PatientCompanionNotificationReceipt).one()
    assert receipt.access_id == access.id
    assert receipt.patient_id == patient.id
    assert receipt.read_at is None
    assert receipt.snoozed_until is not None

    # Move the clock beyond snooze; canonical source appears again.
    later = receipt.snoozed_until + timedelta(seconds=1)
    resurfaced = project_notifications(db, access, now=later)["items"]
    assert len(resurfaced) == 1

    read = handle_notification_read(
        db,
        access,
        {"notification_id": item["notification_id"]},
    )
    assert read.status == "ACCEPTED"
    db.commit()
    assert db.query(PatientCompanionNotificationReceipt).count() == 1
    assert db.query(PatientCompanionNotificationReceipt).one().read_at is not None
    assert project_notifications(db, access, now=later)["items"] == []


def test_pc05_preferences_are_access_scoped_and_do_not_mutate_business_truth(db, dentiste):
    patient, _identity, access = _patient_access(db, dentiste, "P")
    now = datetime.utcnow()
    appointment = models.Appointment(
        patient_id=patient.id,
        employer_id=dentiste.id,
        datetime_start=now + timedelta(hours=6),
        status=models.AppointmentStatus.CONFIRME,
    )
    db.add(appointment)
    db.commit()

    result = handle_notification_preferences(
        db,
        access,
        {
            "appointments": False,
            "documents": True,
            "questionnaires": True,
            "consents": True,
        },
    )
    assert result.status == "ACCEPTED"
    db.commit()

    prefs = db.query(PatientCompanionNotificationPreference).one()
    assert prefs.access_id == access.id
    assert prefs.appointments is False
    assert project_notifications(db, access, now=now)["items"] == []
    db.refresh(appointment)
    assert appointment.status == models.AppointmentStatus.CONFIRME


def test_pc05_completed_questionnaire_is_not_projected(db, dentiste):
    patient, _identity, access = _patient_access(db, dentiste, "Q")
    definition = PatientCompanionQuestionnaireDefinition(
        employer_id=dentiste.id,
        lineage_key=str(uuid.uuid4()),
        version=1,
        title="Antécédents",
        questions_json="[]",
        status="ACTIVE",
    )
    db.add(definition)
    db.flush()
    assignment = PatientCompanionQuestionnaireAssignment(
        employer_id=dentiste.id,
        patient_id=patient.id,
        questionnaire_id=definition.id,
        created_by_user_id=dentiste.id,
        status="ASSIGNED",
    )
    db.add(assignment)
    db.flush()
    db.add(PatientCompanionQuestionnaireSubmission(
        assignment_id=assignment.id,
        access_id=access.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        questionnaire_id=definition.id,
        answers_json="{}",
        status="PENDING_REVIEW",
    ))
    db.commit()

    assert project_notifications(db, access)["items"] == []


def test_pc05_handlers_reject_unknown_or_malformed_notification(db, dentiste):
    _patient, _identity, access = _patient_access(db, dentiste, "X")
    malformed = handle_notification_read(db, access, {"notification_id": "x", "extra": True})
    missing = handle_notification_snooze(db, access, {"notification_id": "does-not-exist"})
    bad_prefs = handle_notification_preferences(db, access, {"appointments": True})

    assert malformed.status == "REJECTED"
    assert malformed.response["code"] == "INVALID_REQUEST"
    assert missing.status == "REJECTED"
    assert missing.response["code"] == "NOTIFICATION_NOT_FOUND"
    assert bad_prefs.status == "REJECTED"
    assert db.query(PatientCompanionNotificationReceipt).count() == 0
