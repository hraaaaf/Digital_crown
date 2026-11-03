from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.cephalo_r15_clinical_studio import build_r15_clinical_studio_snapshot
from backend.services.cephalo_r11_r12_attestation import (
    R11R12AttestationRequest,
    attest_r11r12,
    read_r11r12_attestation,
)
from backend.services.cephalo_r14_final_decision import R14FinalDecisionRequest, decide_r14_final
from backend.services.cephalo_r14_final_read import read_r14_final
from backend.services.cephalo_r13_option_decision import R13DecisionRequest, decide_r13_option
from backend.services.cephalo_r13_option_read import read_r13_decision
from backend.services.cephalo_r11_r13_staging import (
    R11R13StagingRequest,
    read_staged_clinical_evidence,
    stage_clinical_evidence,
)
from backend.services.cephalo_r14_review_receipt import (
    CephaloBlockerReviewRequest,
    read_blocker_review_receipts,
    save_blocker_review_receipt,
)
from backend.utils.access_control import assert_patient_access

router = APIRouter()


@router.get("/{patient_id}/cephalo-clinical-studio")
def get_cephalo_clinical_studio(
    patient_id: int,
    analysis_id: int | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")

    analysis_query = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id)
    if analysis_id is not None:
        analysis = analysis_query.filter(models.CephaloAnalysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse céphalométrique introuvable pour ce patient")
    else:
        analysis = (
            analysis_query
            .order_by(models.CephaloAnalysis.created_at.desc(), models.CephaloAnalysis.id.desc())
            .first()
        )

    return build_r15_clinical_studio_snapshot(
        patient_id=patient_id,
        analysis_id=analysis.id if analysis else None,
        angles_data=analysis.angles_data if analysis else None,
    )


def _bound_review_analysis(patient_id: int, analysis_id: int, current_user: models.User, db: Session, *, lock: bool = False):
    # Patient ownership must be checked BEFORE an analysis query, including GET.
    assert_patient_access(patient_id, current_user, db)
    query = (
        db.query(models.CephaloAnalysis)
        .filter(models.CephaloAnalysis.patient_id == patient_id, models.CephaloAnalysis.id == analysis_id)
    )
    # The staged scientific JSON must not overwrite a concurrent revision.
    analysis = (query.with_for_update() if lock else query).first()
    if not analysis or analysis.patient_id != patient_id or analysis.id != analysis_id:
        raise HTTPException(status_code=404, detail="Analyse céphalométrique introuvable pour ce patient")
    return analysis


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/blocker-reviews", status_code=201)
def acknowledge_r14_blockers(
    patient_id: int,
    analysis_id: int,
    body: CephaloBlockerReviewRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Audit a dentist reading the R11–R14 clinical blockers. Never sign a case."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return save_blocker_review_receipt(
        patient_id=patient_id, analysis=analysis, actor=current_user, request=body, db=db
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/blocker-reviews")
def get_r14_blocker_receipts(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_blocker_review_receipts(patient_id=patient_id, analysis=analysis, db=db)


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r11-r13-staging", status_code=201)
def stage_r11_r13_clinical_snapshot(
    patient_id: int,
    analysis_id: int,
    body: R11R13StagingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Store non-final source-validated data; never select R13 or sign R14."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db, lock=True)
    return stage_clinical_evidence(
        patient_id=patient_id, analysis=analysis, actor=current_user, body=body, db=db,
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r11-r13-staging")
def get_r11_r13_clinical_snapshot(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_staged_clinical_evidence(patient_id=patient_id, analysis=analysis)


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r13-option-decision", status_code=201)
def post_r13_clinician_option_decision(
    patient_id: int,
    analysis_id: int,
    body: R13DecisionRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Select or reject one eligible R13 option with a backend audit. NOT R14."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db, lock=True)
    return decide_r13_option(
        patient_id=patient_id, analysis=analysis, actor=current_user, request=body, db=db,
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r13-option-decision")
def get_r13_clinician_option_decision(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Reopen the audited R13 choice, always non-final and never an R14 signoff."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_r13_decision(
        patient_id=patient_id, analysis=analysis,
        tenant_id=current_user.get_employer_id(), db=db,
    )


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r11-r12-attestation", status_code=201)
def post_r11_r12_clinician_attestation(
    patient_id: int,
    analysis_id: int,
    body: R11R12AttestationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Explicit dentist review of source-validated R11/R12. Never R14."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db, lock=True)
    return attest_r11r12(
        patient_id=patient_id, analysis=analysis, actor=current_user,
        request=body, db=db,
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r11-r12-attestation")
def get_r11_r12_clinician_attestation(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_r11r12_attestation(
        patient_id=patient_id, analysis=analysis,
        tenant_id=current_user.get_employer_id(), db=db,
    )


@router.post("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r14-final-decision", status_code=201)
def post_r14_final_clinician_decision(
    patient_id: int,
    analysis_id: int,
    body: R14FinalDecisionRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Dentist-owned R14 decision, source-locked and not PDF-release authority."""
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db, lock=True)
    return decide_r14_final(
        patient_id=patient_id, analysis=analysis, actor=current_user,
        request=body, db=db,
    )


@router.get("/{patient_id}/cephalo-clinical-studio/{analysis_id}/r14-final-decision")
def get_r14_final_clinician_decision(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _bound_review_analysis(patient_id, analysis_id, current_user, db)
    return read_r14_final(
        patient_id=patient_id, analysis=analysis,
        tenant_id=current_user.get_employer_id(), db=db,
    )
