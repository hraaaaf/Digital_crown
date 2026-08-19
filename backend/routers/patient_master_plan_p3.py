from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.models_clinical_p3 import TreatmentMasterPlanRevision
from backend.routers.auth import require_permission
from backend.services.audit_service import audit_service
from backend.utils.access_control import assert_patient_access


router = APIRouter()


def _step_snapshot(step_data, order_index: int) -> dict:
    payload = step_data.model_dump(mode="json") if hasattr(step_data, "model_dump") else step_data.dict()
    payload["order_index"] = order_index
    return payload


@router.get("/{patient_id}/master-plan", response_model=Optional[schemas.TreatmentMasterPlanOut])
def get_master_plan_p3(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    assert_patient_access(patient_id, current_user, db)
    return (
        db.query(models.TreatmentMasterPlan)
        .filter(models.TreatmentMasterPlan.patient_id == patient_id)
        .first()
    )


@router.put("/{patient_id}/master-plan", response_model=schemas.TreatmentMasterPlanOut)
def update_master_plan_p3(
    patient_id: int,
    steps: List[schemas.TreatmentPlanStepCreate],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    """Replace current steps and append one immutable revision in the same transaction."""
    assert_patient_access(patient_id, current_user, db)
    plan = (
        db.query(models.TreatmentMasterPlan)
        .filter(models.TreatmentMasterPlan.patient_id == patient_id)
        .with_for_update()
        .first()
    )
    if plan is None:
        plan = models.TreatmentMasterPlan(patient_id=patient_id)
        db.add(plan)
        db.flush()
    else:
        (
            db.query(models.TreatmentPlanStep)
            .filter(models.TreatmentPlanStep.plan_id == plan.id)
            .delete(synchronize_session=False)
        )

    snapshot = []
    for order_index, step_data in enumerate(steps):
        db.add(
            models.TreatmentPlanStep(
                plan_id=plan.id,
                title=step_data.title,
                assistant=step_data.assistant,
                status=step_data.status,
                date_str=step_data.date_str,
                order_index=order_index,
            )
        )
        snapshot.append(_step_snapshot(step_data, order_index))

    latest_revision = int(
        db.query(func.max(TreatmentMasterPlanRevision.revision))
        .filter(TreatmentMasterPlanRevision.plan_id == plan.id)
        .scalar()
        or 0
    )
    revision = TreatmentMasterPlanRevision(
        plan_id=plan.id,
        patient_id=patient_id,
        revision=latest_revision + 1,
        steps_snapshot=snapshot,
        updated_by=current_user.id,
    )
    db.add(revision)

    db.commit()
    db.refresh(plan)

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="UPDATE",
        resource_type="TreatmentMasterPlan",
        resource_id=str(plan.id),
        details=f"patient_id={patient_id} revision={revision.revision} steps={len(snapshot)}",
    )
    return plan


@router.get("/{patient_id}/master-plan/revisions")
def list_master_plan_revisions_p3(
    patient_id: int,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    assert_patient_access(patient_id, current_user, db)
    rows = (
        db.query(TreatmentMasterPlanRevision)
        .filter(TreatmentMasterPlanRevision.patient_id == patient_id)
        .order_by(TreatmentMasterPlanRevision.revision.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return [
        {
            "id": row.id,
            "plan_id": row.plan_id,
            "patient_id": row.patient_id,
            "revision": row.revision,
            "steps_snapshot": row.steps_snapshot,
            "updated_by": row.updated_by,
            "created_at": row.created_at,
        }
        for row in rows
    ]
