"""MOB-5I waiting-room facade over the canonical mobile appointment contracts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import database, models
from backend.services.zka_crypto import decrypt_payload, encrypt_payload
from . import mobile_legacy as _legacy

router = APIRouter()

# The legacy mobile vocabulary flattened EN_SALLE_ATTENTE into PLANIFIE. Keep the
# existing mobile CRUD and security dependencies, but make the fifth canonical
# business state round-trip exactly instead of creating a second queue model.
_legacy._MOBILE_TO_BACKEND_STATUS["EN_ATTENTE"] = models.AppointmentStatus.EN_SALLE_ATTENTE
_legacy._BACKEND_TO_MOBILE_STATUS[models.AppointmentStatus.EN_SALLE_ATTENTE] = "EN_ATTENTE"


def _ticket_by_appointment_id(db: Session, employer_id: int, appointment_ids: list[int]) -> dict[int, int | None]:
    if not appointment_ids:
        return {}
    rows = (
        db.query(models.Appointment.id, models.Appointment.ticket_number)
        .filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.id.in_(appointment_ids),
        )
        .all()
    )
    return {int(row.id): row.ticket_number for row in rows}


def _enrich_tickets(data: dict, db: Session, employer_id: int, key: str) -> dict:
    appointments = data.get(key) or []
    appointment_ids = [int(item["id"]) for item in appointments if item.get("id") is not None]
    tickets = _ticket_by_appointment_id(db, employer_id, appointment_ids)
    for item in appointments:
        appointment_id = item.get("id")
        item["ticket_number"] = tickets.get(int(appointment_id)) if appointment_id is not None else None
    return data


@router.get("/snapshot", summary="Snapshot mobile avec état Salle d’attente canonique")
def get_mobile_waiting_room_snapshot(
    target_date: str = None,
    employer_id: int = Depends(_legacy.get_mobile_employer_id),
    current_user: models.User = Depends(_legacy.require_mobile_permission("agenda")),
    can_view_finance: bool = Depends(_legacy.get_mobile_finance_access),
    role: str = Depends(_legacy.get_mobile_role),
    db: Session = Depends(database.get_db),
):
    encrypted = _legacy.get_mobile_snapshot(
        target_date=target_date,
        employer_id=employer_id,
        current_user=current_user,
        can_view_finance=can_view_finance,
        role=role,
        db=db,
    )
    data = decrypt_payload(encrypted["payload"])
    return encrypt_payload(_enrich_tickets(data, db, employer_id, "appointments"))


@router.get("/appointments", summary="Liste mobile des RDV avec état Salle d’attente canonique")
def get_mobile_waiting_room_appointments(
    start_date: str,
    end_date: str,
    employer_id: int = Depends(_legacy.get_mobile_employer_id),
    _mobile_user: models.User = Depends(_legacy.require_mobile_permission("agenda")),
    db: Session = Depends(database.get_db),
):
    encrypted = _legacy.get_mobile_appointments(
        start_date=start_date,
        end_date=end_date,
        employer_id=employer_id,
        _mobile_user=_mobile_user,
        db=db,
    )
    data = decrypt_payload(encrypted["payload"])
    return encrypt_payload(_enrich_tickets(data, db, employer_id, "data"))
