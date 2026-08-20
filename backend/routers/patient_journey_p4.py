from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.models_imaging_p4 import ImagingTrashRecord
from backend.routers.auth import require_permission
from backend.utils.access_control import assert_patient_access


router = APIRouter()


def _trashed_imaging_ids(db: Session, patient_id: int):
    records = (
        db.query(ImagingTrashRecord)
        .filter(ImagingTrashRecord.patient_id == patient_id)
        .all()
    )
    pano_ids = {record.analysis_id for record in records if record.modality == "panoramic"}
    cephalo_ids = {record.analysis_id for record in records if record.modality == "cephalo"}
    return pano_ids, cephalo_ids


def _count_trashed_events_in_window(
    db: Session,
    patient_id: int,
    pano_ids: set[int],
    cephalo_ids: set[int],
    full_history: bool,
) -> int:
    since = None if full_history else datetime.now() - timedelta(days=12 * 30)
    count = 0
    if pano_ids:
        q = db.query(models.PanoramicAnalysis.id).filter(
            models.PanoramicAnalysis.patient_id == patient_id,
            models.PanoramicAnalysis.id.in_(pano_ids),
        )
        if since is not None:
            q = q.filter(models.PanoramicAnalysis.created_at >= since)
        count += q.count()
    if cephalo_ids:
        q = db.query(models.CephaloAnalysis.id).filter(
            models.CephaloAnalysis.patient_id == patient_id,
            models.CephaloAnalysis.id.in_(cephalo_ids),
        )
        if since is not None:
            q = q.filter(models.CephaloAnalysis.created_at >= since)
        count += q.count()
    return count


@router.get("/{patient_id}/journey", response_model=schemas.PatientJourneyResponse)
def get_patient_journey_p4(
    patient_id: int,
    full_history: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """P2 Journey contract, with recoverable P4 imaging trash excluded from active chronology."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services import patient_journey_service

    result = patient_journey_service.build_journey(
        db,
        patient_id,
        current_user.get_employer_id(),
        full_history,
    )
    pano_ids, cephalo_ids = _trashed_imaging_ids(db, patient_id)
    if not pano_ids and not cephalo_ids:
        return result

    removed_keys = {
        f"panoramic_analysis:{analysis_id}" for analysis_id in pano_ids
    } | {
        f"cephalo_analysis:{analysis_id}" for analysis_id in cephalo_ids
    }

    filtered_events = []
    for event in result.events:
        if event.source == "panoramic_analysis" and event.ref_id in pano_ids:
            continue
        if event.source == "cephalo_analysis" and event.ref_id in cephalo_ids:
            continue
        if event.related_event_key in removed_keys:
            event = event.model_copy(update={"related_event_key": None})
        filtered_events.append(event)

    removed_count = _count_trashed_events_in_window(
        db,
        patient_id,
        pano_ids,
        cephalo_ids,
        full_history,
    )
    return result.model_copy(
        update={
            "events": filtered_events,
            "total_events_available": max(0, result.total_events_available - removed_count),
        }
    )
