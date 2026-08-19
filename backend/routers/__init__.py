# Digital Crown Routers Package

# P3 clinical extensions are mounted under the existing patient router so they inherit
# the canonical /api/patients prefix and patient-level access-control conventions.
from . import patients as patients
from . import patient_odontogram as patient_odontogram
from . import patient_clinical_conclusions as patient_clinical_conclusions
from . import patient_master_plan_p3 as patient_master_plan_p3

# Replace only the legacy current-state Master Plan GET/PUT handlers. P3 keeps the same
# public contract, but every successful PUT now appends an immutable revision snapshot.
patients.router.routes = [
    route
    for route in patients.router.routes
    if not (
        getattr(route, "path", None) == "/{patient_id}/master-plan"
        and ({"GET", "PUT"} & (getattr(route, "methods", set()) or set()))
    )
]

patients.router.include_router(patient_odontogram.router)
patients.router.include_router(patient_clinical_conclusions.router)
patients.router.include_router(patient_master_plan_p3.router)
