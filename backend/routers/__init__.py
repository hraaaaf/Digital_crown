# Digital Crown Routers Package

# Patient extensions are mounted under the existing patient router so they inherit
# the canonical /api/patients prefix and patient-level access-control conventions.
from . import patients as patients
from . import patient_odontogram as patient_odontogram
from . import patient_clinical_conclusions as patient_clinical_conclusions
from . import patient_financial_p6 as patient_financial_p6

# P6 replaces the legacy finance snapshot route rather than registering a duplicate
# GET handler for the same path. The legacy implementation only required `patients`
# and could turn an absent billing basis into a misleading zero balance.
patients.router.routes = [
    route
    for route in patients.router.routes
    if not (
        getattr(route, "path", None) == "/{patient_id}/financial-snapshot"
        and "GET" in (getattr(route, "methods", set()) or set())
    )
]

patients.router.include_router(patient_odontogram.router)
patients.router.include_router(patient_clinical_conclusions.router)
patients.router.include_router(patient_financial_p6.router)
