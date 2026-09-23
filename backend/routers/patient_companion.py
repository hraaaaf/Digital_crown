"""Patient-facing local-first boundary. Canonical device auth is QR-paired; legacy Firebase identity remains compatible."""
from fastapi import APIRouter

from backend.routers import patient_companion_activation, patient_companion_agenda, patient_companion_consents, patient_companion_emergency_photo, patient_companion_finance, patient_companion_messages, patient_companion_notifications, patient_companion_pairing, patient_companion_questionnaires, patient_companion_shares

router = APIRouter(tags=["Patient Companion"])
router.include_router(patient_companion_activation.router)
router.include_router(patient_companion_agenda.router)
router.include_router(patient_companion_consents.router)
router.include_router(patient_companion_finance.router)
router.include_router(patient_companion_messages.router)
router.include_router(patient_companion_notifications.router)
router.include_router(patient_companion_pairing.router)
router.include_router(patient_companion_questionnaires.router)
router.include_router(patient_companion_shares.router)
