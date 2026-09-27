from backend import models
from backend.routers import mobile_legacy


def test_waiting_room_status_round_trips_between_backend_and_pocket():
    assert mobile_legacy._MOBILE_TO_BACKEND_STATUS["EN_ATTENTE"] == models.AppointmentStatus.EN_SALLE_ATTENTE
    assert mobile_legacy._to_mobile_status(models.AppointmentStatus.EN_SALLE_ATTENTE) == "EN_ATTENTE"


def test_planned_and_chairside_statuses_keep_their_existing_contract():
    assert mobile_legacy._to_mobile_status(models.AppointmentStatus.PREVU) == "PLANIFIE"
    assert mobile_legacy._to_mobile_status(models.AppointmentStatus.EN_FAUTEUIL) == "EN_COURS"
    assert mobile_legacy._to_mobile_status(models.AppointmentStatus.TERMINE) == "TERMINE"
    assert mobile_legacy._to_mobile_status(models.AppointmentStatus.ANNULE) == "ANNULE"
