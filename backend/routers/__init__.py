# Digital Crown Routers Package

# P3 clinical extension: mount the odontogram API under the existing patient router
# so /api/patients/{patient_id}/odontogram inherits the canonical patient prefix.
from . import patients as patients
from . import patient_odontogram as patient_odontogram

patients.router.include_router(patient_odontogram.router)
