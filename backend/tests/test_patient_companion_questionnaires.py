from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException, Response

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionQuestionnaireAssignment,
    PatientCompanionQuestionnaireDefinition,
    PatientCompanionQuestionnaireSubmission,
)
from backend.routers.patient_companion_questionnaires import (
    QuestionnaireSubmitRequest,
    _validate_answers,
    list_patient_questionnaires,
    submit_patient_questionnaire,
)


def _context(db, dentiste):
    patient = models.Patient(
        numero_dossier=f"PC03-{uuid.uuid4().hex[:8]}",
        nom="Questionnaire",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
        antecedents_medicaux="Historique cabinet inchangé",
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"device:{uuid.uuid4()}")
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
    definition = PatientCompanionQuestionnaireDefinition(
        employer_id=dentiste.id,
        lineage_key=str(uuid.uuid4()),
        version=1,
        title="Questionnaire test",
        questions_json=(
            '[{"id":"q1","label":"Question 1","type":"yes_no","required":true,"options":[]},'
            '{"id":"q2","label":"Question 2","type":"single_choice","required":false,"options":["A","B"]},'
            '{"id":"q3","label":"Question 3","type":"short_text","required":false,"options":[]}]'
        ),
        status="ACTIVE",
        published_at=datetime.utcnow(),
    )
    db.add(definition)
    db.flush()
    assignment = PatientCompanionQuestionnaireAssignment(
        employer_id=dentiste.id,
        patient_id=patient.id,
        questionnaire_id=definition.id,
        created_by_user_id=dentiste.id,
    )
    db.add(assignment)
    db.flush()
    return patient, identity, access, definition, assignment


def test_answer_validation_is_schema_bounded(db, dentiste):
    _, _, _, definition, _ = _context(db, dentiste)
    assert _validate_answers(definition, {"q1": True, "q2": "A", "q3": "  note  "}) == {
        "q1": True,
        "q2": "A",
        "q3": "note",
    }
    with pytest.raises(HTTPException) as unknown:
        _validate_answers(definition, {"q1": True, "internal_patient_id": 7})
    assert unknown.value.status_code == 422
    with pytest.raises(HTTPException):
        _validate_answers(definition, {"q2": "A"})
    with pytest.raises(HTTPException):
        _validate_answers(definition, {"q1": "oui"})
    with pytest.raises(HTTPException):
        _validate_answers(definition, {"q1": True, "q2": "C"})


def test_submission_is_patient_reported_and_does_not_mutate_clinical_history(db, dentiste):
    patient, identity, _access, _definition, assignment = _context(db, dentiste)
    before = patient.antecedents_medicaux
    result = submit_patient_questionnaire(
        access_id=_access.public_id,
        assignment_id=assignment.public_id,
        body=QuestionnaireSubmitRequest(answers={"q1": True, "q2": "B", "q3": "patient report"}),
        response=Response(),
        identity=identity,
        db=db,
    )
    assert result["status"] == "PENDING_REVIEW"
    assert result["clinical_record_updated"] is False
    db.refresh(patient)
    assert patient.antecedents_medicaux == before

    submission = db.query(PatientCompanionQuestionnaireSubmission).filter(
        PatientCompanionQuestionnaireSubmission.assignment_id == assignment.id
    ).one()
    assert submission.status == "PENDING_REVIEW"
    assert submission.reviewed_at is None
    assert submission.reviewed_by_user_id is None

    with pytest.raises(HTTPException) as duplicate:
        submit_patient_questionnaire(
            access_id=_access.public_id,
            assignment_id=assignment.public_id,
            body=QuestionnaireSubmitRequest(answers={"q1": False}),
            response=Response(),
            identity=identity,
            db=db,
        )
    assert duplicate.value.status_code == 409


def test_patient_list_exposes_versioned_assignment_without_internal_ids(db, dentiste):
    _patient, identity, access, definition, assignment = _context(db, dentiste)
    result = list_patient_questionnaires(
        access_id=access.public_id,
        response=Response(),
        identity=identity,
        db=db,
    )
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["assignment_id"] == assignment.public_id
    assert item["questionnaire_id"] == definition.public_id
    assert item["version"] == 1
    assert item["state"] == "ASSIGNED"
    assert "patient_id" not in item
    assert "employer_id" not in item
    assert "answers_json" not in item
