from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionQuestionnaireAssignment,
    PatientCompanionQuestionnaireDefinition,
    PatientCompanionQuestionnaireSubmission,
)
from backend.routers.auth import get_current_user
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
    staff_patient_or_404,
)
from backend.services.audit_service import audit_service

router = APIRouter()


class QuestionnaireQuestion(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=300)
    type: Literal["yes_no", "single_choice", "short_text"]
    required: bool = False
    options: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_options(self):
        if self.type == "single_choice":
            if len(self.options) < 2:
                raise ValueError("single_choice requires at least two options")
            if any(not option.strip() or len(option) > 120 for option in self.options):
                raise ValueError("invalid single_choice option")
        elif self.options:
            raise ValueError("options are only allowed for single_choice")
        return self


class QuestionnaireDefinitionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    lineage_key: str | None = Field(default=None, min_length=36, max_length=36)
    questions: list[QuestionnaireQuestion] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [item.id for item in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("question ids must be unique")
        return self


class QuestionnaireAssignRequest(BaseModel):
    expires_at: datetime | None = None


class QuestionnaireSubmitRequest(BaseModel):
    answers: dict[str, object]


class QuestionnaireReviewRequest(BaseModel):
    decision: Literal["REVIEWED", "REJECTED"]
    note: str | None = Field(default=None, max_length=2000)


def _definition_payload(row: PatientCompanionQuestionnaireDefinition) -> dict:
    return {
        "questionnaire_id": row.public_id,
        "title": row.title,
        "version": row.version,
        "questions": json.loads(row.questions_json),
    }


def _validate_answers(definition: PatientCompanionQuestionnaireDefinition, answers: dict[str, object]) -> dict[str, object]:
    questions = json.loads(definition.questions_json)
    by_id = {item["id"]: item for item in questions}
    unknown = set(answers) - set(by_id)
    if unknown:
        raise HTTPException(status_code=422, detail="Réponse contenant une question inconnue.")

    normalized: dict[str, object] = {}
    for question in questions:
        qid = question["id"]
        if qid not in answers:
            if question.get("required"):
                raise HTTPException(status_code=422, detail=f"Réponse obligatoire manquante: {qid}")
            continue
        value = answers[qid]
        qtype = question["type"]
        if qtype == "yes_no":
            if not isinstance(value, bool):
                raise HTTPException(status_code=422, detail=f"Réponse oui/non invalide: {qid}")
        elif qtype == "single_choice":
            if not isinstance(value, str) or value not in question.get("options", []):
                raise HTTPException(status_code=422, detail=f"Choix invalide: {qid}")
        elif qtype == "short_text":
            if not isinstance(value, str) or len(value.strip()) > 1000:
                raise HTTPException(status_code=422, detail=f"Texte invalide: {qid}")
            value = value.strip()
        else:
            raise HTTPException(status_code=500, detail="Définition questionnaire invalide.")
        normalized[qid] = value
    return normalized


@router.post("/admin/questionnaires/definitions", status_code=201)
def create_questionnaire_definition(
    body: QuestionnaireDefinitionCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    employer_id = int(current_user.get_employer_id())
    lineage_key = body.lineage_key or str(uuid.uuid4())
    try:
        uuid.UUID(lineage_key)
    except ValueError:
        raise HTTPException(status_code=422, detail="lineage_key invalide.") from None

    previous = (
        db.query(PatientCompanionQuestionnaireDefinition)
        .filter(
            PatientCompanionQuestionnaireDefinition.employer_id == employer_id,
            PatientCompanionQuestionnaireDefinition.lineage_key == lineage_key,
        )
        .order_by(PatientCompanionQuestionnaireDefinition.version.desc())
        .first()
    )
    version = 1 if previous is None else previous.version + 1
    if previous is not None and previous.status == "ACTIVE":
        previous.status = "RETIRED"
        previous.retired_at = datetime.utcnow()

    row = PatientCompanionQuestionnaireDefinition(
        employer_id=employer_id,
        lineage_key=lineage_key,
        version=version,
        title=body.title.strip(),
        questions_json=json.dumps([item.model_dump() for item in body.questions], ensure_ascii=False, separators=(",", ":")),
        status="ACTIVE",
        published_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_QUESTIONNAIRE_VERSION_CREATED",
        resource_type="PatientCompanionQuestionnaireDefinition",
        resource_id=row.public_id,
        details=f"lineage={lineage_key}; version={version}",
    )
    response.headers["Cache-Control"] = "no-store"
    return {**_definition_payload(row), "lineage_key": lineage_key, "status": row.status}


@router.post("/admin/patients/{patient_id}/questionnaires/{questionnaire_id}/assign", status_code=201)
def assign_questionnaire(
    patient_id: int,
    questionnaire_id: str,
    body: QuestionnaireAssignRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    definition = db.query(PatientCompanionQuestionnaireDefinition).filter(
        PatientCompanionQuestionnaireDefinition.public_id == questionnaire_id,
        PatientCompanionQuestionnaireDefinition.employer_id == employer_id,
        PatientCompanionQuestionnaireDefinition.status == "ACTIVE",
    ).first()
    if definition is None:
        raise HTTPException(status_code=404, detail="Questionnaire actif introuvable.")
    existing = db.query(PatientCompanionQuestionnaireAssignment).filter(
        PatientCompanionQuestionnaireAssignment.employer_id == employer_id,
        PatientCompanionQuestionnaireAssignment.patient_id == patient.id,
        PatientCompanionQuestionnaireAssignment.questionnaire_id == definition.id,
    ).first()
    if existing is not None:
        response.headers["Cache-Control"] = "no-store"
        return {"assignment_id": existing.public_id, "status": existing.status}

    assignment = PatientCompanionQuestionnaireAssignment(
        employer_id=employer_id,
        patient_id=patient.id,
        questionnaire_id=definition.id,
        created_by_user_id=current_user.id,
        expires_at=body.expires_at,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_QUESTIONNAIRE_ASSIGNED",
        resource_type="Patient",
        resource_id=str(patient.id),
        details=f"assignment={assignment.public_id}; questionnaire={definition.public_id}",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"assignment_id": assignment.public_id, "status": assignment.status}


@router.get("/contexts/{access_id}/questionnaires")
def list_patient_questionnaires(
    access_id: str,
    response: Response,
    identity=Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    assignments = db.query(PatientCompanionQuestionnaireAssignment).filter(
        PatientCompanionQuestionnaireAssignment.employer_id == principal.employer_id,
        PatientCompanionQuestionnaireAssignment.patient_id == principal.patient_id,
        PatientCompanionQuestionnaireAssignment.revoked_at.is_(None),
    ).order_by(PatientCompanionQuestionnaireAssignment.assigned_at.desc()).all()
    items = []
    now = datetime.utcnow()
    for assignment in assignments:
        definition = db.query(PatientCompanionQuestionnaireDefinition).filter(
            PatientCompanionQuestionnaireDefinition.id == assignment.questionnaire_id,
            PatientCompanionQuestionnaireDefinition.employer_id == principal.employer_id,
        ).first()
        if definition is None:
            continue
        submission = db.query(PatientCompanionQuestionnaireSubmission).filter(
            PatientCompanionQuestionnaireSubmission.assignment_id == assignment.id,
        ).first()
        if assignment.expires_at is not None and assignment.expires_at <= now and submission is None:
            state = "EXPIRED"
        elif submission is not None:
            state = submission.status
        else:
            state = "ASSIGNED"
        items.append({
            "assignment_id": assignment.public_id,
            "state": state,
            "assigned_at": assignment.assigned_at,
            "expires_at": assignment.expires_at,
            **_definition_payload(definition),
            "submitted_at": None if submission is None else submission.submitted_at,
            "reviewed_at": None if submission is None else submission.reviewed_at,
        })
    response.headers["Cache-Control"] = "no-store"
    return {"items": items}


@router.post("/contexts/{access_id}/questionnaires/{assignment_id}/submit", status_code=201)
def submit_patient_questionnaire(
    access_id: str,
    assignment_id: str,
    body: QuestionnaireSubmitRequest,
    response: Response,
    identity=Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == principal.access_id,
        PatientCompanionAccess.identity_id == principal.identity_id,
        PatientCompanionAccess.employer_id == principal.employer_id,
        PatientCompanionAccess.patient_id == principal.patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    assignment = db.query(PatientCompanionQuestionnaireAssignment).filter(
        PatientCompanionQuestionnaireAssignment.public_id == assignment_id,
        PatientCompanionQuestionnaireAssignment.employer_id == principal.employer_id,
        PatientCompanionQuestionnaireAssignment.patient_id == principal.patient_id,
        PatientCompanionQuestionnaireAssignment.revoked_at.is_(None),
    ).first()
    if access is None or assignment is None:
        raise HTTPException(status_code=404, detail="Questionnaire introuvable.")
    if assignment.expires_at is not None and assignment.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=409, detail="Questionnaire expiré.")
    existing = db.query(PatientCompanionQuestionnaireSubmission).filter(
        PatientCompanionQuestionnaireSubmission.assignment_id == assignment.id,
    ).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Questionnaire déjà envoyé.")
    definition = db.query(PatientCompanionQuestionnaireDefinition).filter(
        PatientCompanionQuestionnaireDefinition.id == assignment.questionnaire_id,
        PatientCompanionQuestionnaireDefinition.employer_id == principal.employer_id,
    ).first()
    if definition is None:
        raise HTTPException(status_code=409, detail="Version du questionnaire indisponible.")

    normalized = _validate_answers(definition, body.answers)
    submission = PatientCompanionQuestionnaireSubmission(
        assignment_id=assignment.id,
        access_id=access.id,
        employer_id=principal.employer_id,
        patient_id=principal.patient_id,
        questionnaire_id=definition.id,
        answers_json=json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        status="PENDING_REVIEW",
    )
    assignment.status = "SUBMITTED"
    db.add(submission)
    db.commit()
    db.refresh(submission)
    audit_service.log(
        db=db,
        user_id=None,
        employer_id=principal.employer_id,
        action="PATIENT_COMPANION_QUESTIONNAIRE_SUBMITTED",
        resource_type="PatientCompanionQuestionnaireSubmission",
        resource_id=submission.public_id,
        details=f"assignment={assignment.public_id}; pending_clinician_review=true",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "submission_id": submission.public_id,
        "status": submission.status,
        "submitted_at": submission.submitted_at,
        "clinical_record_updated": False,
    }


@router.post("/admin/questionnaire-submissions/{submission_id}/review")
def review_questionnaire_submission(
    submission_id: str,
    body: QuestionnaireReviewRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    employer_id = int(current_user.get_employer_id())
    submission = db.query(PatientCompanionQuestionnaireSubmission).filter(
        PatientCompanionQuestionnaireSubmission.public_id == submission_id,
        PatientCompanionQuestionnaireSubmission.employer_id == employer_id,
    ).first()
    if submission is None:
        raise HTTPException(status_code=404, detail="Soumission introuvable.")
    if submission.status != "PENDING_REVIEW":
        raise HTTPException(status_code=409, detail="Soumission déjà revue.")
    submission.status = body.decision
    submission.reviewed_at = datetime.utcnow()
    submission.reviewed_by_user_id = current_user.id
    submission.reviewer_note = body.note.strip() if body.note else None
    db.commit()
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_QUESTIONNAIRE_REVIEWED",
        resource_type="PatientCompanionQuestionnaireSubmission",
        resource_id=submission.public_id,
        details=f"decision={body.decision}; clinical_record_updated=false",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "submission_id": submission.public_id,
        "status": submission.status,
        "reviewed_at": submission.reviewed_at,
        "clinical_record_updated": False,
    }
