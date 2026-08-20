from collections import defaultdict, deque
from datetime import datetime
from typing import Deque, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.models_catalog_plan import TreatmentPlanCatalogSnapshot
from backend.models_clinical_p3 import TreatmentMasterPlanRevision
from backend.routers.auth import require_permission
from backend.services.audit_service import audit_service
from backend.utils.access_control import assert_patient_access

router = APIRouter()


class CatalogSnapshotPayload(BaseModel):
    act_id: int
    code: Optional[str] = None
    name: str
    price: float


class ConnectedTreatmentPlanStepCreate(schemas.TreatmentPlanStepCreate):
    catalog_snapshot: Optional[CatalogSnapshotPayload] = None


class ConnectedTreatmentPlanStepOut(schemas.TreatmentPlanStepOut):
    catalog_snapshot: Optional[CatalogSnapshotPayload] = None
    model_config = ConfigDict(from_attributes=True)


class ConnectedTreatmentMasterPlanOut(BaseModel):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime
    steps: List[ConnectedTreatmentPlanStepOut] = []
    model_config = ConfigDict(from_attributes=True)


def _snapshot_key(title: str, assistant: str) -> Tuple[str, str]:
    return (str(title or "").strip(), str(assistant or "").strip())


def _step_snapshot(step_data: ConnectedTreatmentPlanStepCreate, order_index: int, snapshot: Optional[dict] = None) -> dict:
    payload = step_data.model_dump(mode="json")
    payload["order_index"] = order_index
    payload["catalog_snapshot"] = snapshot
    return payload


def _attach_snapshots(db: Session, plan):
    if plan is None:
        return None
    steps = list(getattr(plan, "steps", []) or [])
    step_ids = [step.id for step in steps]
    rows = (
        db.query(TreatmentPlanCatalogSnapshot)
        .filter(TreatmentPlanCatalogSnapshot.step_id.in_(step_ids))
        .all()
        if step_ids
        else []
    )
    by_step = {row.step_id: row.as_payload() for row in rows}
    for step in steps:
        step.catalog_snapshot = by_step.get(step.id)
    return plan


def _old_snapshot_queues(db: Session, plan) -> Dict[Tuple[str, str], Deque[dict]]:
    queues: Dict[Tuple[str, str], Deque[dict]] = defaultdict(deque)
    if plan is None:
        return queues
    old_steps = (
        db.query(models.TreatmentPlanStep)
        .filter(models.TreatmentPlanStep.plan_id == plan.id)
        .order_by(models.TreatmentPlanStep.order_index.asc(), models.TreatmentPlanStep.id.asc())
        .all()
    )
    step_ids = [step.id for step in old_steps]
    rows = (
        db.query(TreatmentPlanCatalogSnapshot)
        .filter(TreatmentPlanCatalogSnapshot.step_id.in_(step_ids))
        .all()
        if step_ids
        else []
    )
    by_step = {row.step_id: row.as_payload() for row in rows}
    for step in old_steps:
        snapshot = by_step.get(step.id)
        if snapshot:
            queues[_snapshot_key(step.title, step.assistant)].append(snapshot)
    return queues


@router.get("/{patient_id}/master-plan", response_model=Optional[ConnectedTreatmentMasterPlanOut])
def get_master_plan_p3(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    assert_patient_access(patient_id, current_user, db)
    plan = (
        db.query(models.TreatmentMasterPlan)
        .filter(models.TreatmentMasterPlan.patient_id == patient_id)
        .first()
    )
    return _attach_snapshots(db, plan)


@router.put("/{patient_id}/master-plan", response_model=ConnectedTreatmentMasterPlanOut)
def update_master_plan_p3(
    patient_id: int,
    steps: List[ConnectedTreatmentPlanStepCreate],
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
        old_snapshots: Dict[Tuple[str, str], Deque[dict]] = defaultdict(deque)
    else:
        old_snapshots = _old_snapshot_queues(db, plan)
        old_step_ids = [
            row[0]
            for row in db.query(models.TreatmentPlanStep.id)
            .filter(models.TreatmentPlanStep.plan_id == plan.id)
            .all()
        ]
        if old_step_ids:
            (
                db.query(TreatmentPlanCatalogSnapshot)
                .filter(TreatmentPlanCatalogSnapshot.step_id.in_(old_step_ids))
                .delete(synchronize_session=False)
            )
        (
            db.query(models.TreatmentPlanStep)
            .filter(models.TreatmentPlanStep.plan_id == plan.id)
            .delete(synchronize_session=False)
        )

    revision_snapshot = []
    for order_index, step_data in enumerate(steps):
        explicit = step_data.catalog_snapshot.model_dump(mode="json") if step_data.catalog_snapshot else None
        preserved = None
        if explicit is None:
            queue = old_snapshots.get(_snapshot_key(step_data.title, step_data.assistant))
            if queue:
                preserved = queue.popleft()
        snapshot = explicit or preserved

        step = models.TreatmentPlanStep(
            plan_id=plan.id,
            title=step_data.title,
            assistant=step_data.assistant,
            status=step_data.status,
            date_str=step_data.date_str,
            order_index=order_index,
        )
        db.add(step)
        db.flush()

        if snapshot:
            db.add(
                TreatmentPlanCatalogSnapshot(
                    step_id=step.id,
                    act_id=int(snapshot["act_id"]),
                    code=snapshot.get("code"),
                    name=str(snapshot["name"]),
                    price=float(snapshot.get("price") or 0.0),
                )
            )
        revision_snapshot.append(_step_snapshot(step_data, order_index, snapshot))

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
        steps_snapshot=revision_snapshot,
        updated_by=current_user.id,
    )
    db.add(revision)

    db.commit()
    db.refresh(plan)
    _attach_snapshots(db, plan)

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="UPDATE",
        resource_type="TreatmentMasterPlan",
        resource_id=str(plan.id),
        details=f"patient_id={patient_id} revision={revision.revision} steps={len(revision_snapshot)}",
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
