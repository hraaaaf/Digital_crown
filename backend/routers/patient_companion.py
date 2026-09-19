"""Patient-facing local-first boundary. Canonical device auth is QR-paired; legacy Firebase identity remains compatible."""
from fastapi import APIRouter

from backend.routers import patient_companion_activation, patient_companion_pairing, patient_companion_shares

router = APIRouter(tags=["Patient Companion"])
router.include_router(patient_companion_activation.router)
router.include_router(patient_companion_pairing.router)
router.include_router(patient_companion_shares.router)
