"""Single clinical occupancy contract shared by every appointment ingress.

Only bookings that have occupied clinical capacity block a precise slot.
A frontdesk request is NOT a confirmed booking until its CAS confirmation
succeeds; refused/expired/cancelled proposals never reserve capacity.
"""
from backend import models

OCCUPYING_APPOINTMENT_STATUSES = (
    models.AppointmentStatus.PREVU,
    models.AppointmentStatus.EN_SALLE_ATTENTE,
    models.AppointmentStatus.EN_FAUTEUIL,
    models.AppointmentStatus.TERMINE,
    models.AppointmentStatus.CONFIRME,
    models.AppointmentStatus.ABSENT,
)
