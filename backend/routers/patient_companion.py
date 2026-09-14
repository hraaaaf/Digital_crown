"""Patient-facing companion boundary. Authentication is Firebase; authorization is local and tenant-scoped."""
from fastapi import APIRouter

from backend.routers import patient_companion_activation, patient_companion_shares

router = APIRouter(tags=["Patient Companion"])
router.include_router(patient_companion_activation.router)
router.include_router(patient_companion_shares.router)
