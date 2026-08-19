# Digital Crown Routers Package

# P3 clinical extensions are mounted under the existing patient router so they inherit
# the canonical /api/patients prefix and patient-level access-control conventions.
from . import patients as patients
from . import patient_odontogram as patient_odontogram
from . import patient_clinical_conclusions as patient_clinical_conclusions

patients.router.include_router(patient_odontogram.router)
patients.router.include_router(patient_clinical_conclusions.router)
