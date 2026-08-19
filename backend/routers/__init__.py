# Digital Crown Routers Package

# Patient/clinical extensions are mounted under the canonical routers so the public
# URLs and access-control conventions stay unchanged.
from . import patients as patients
from . import patient_odontogram as patient_odontogram
from . import patient_clinical_conclusions as patient_clinical_conclusions
from . import ia as ia
from . import imaging_lifecycle_p4 as imaging_lifecycle_p4

patients.router.include_router(patient_odontogram.router)
patients.router.include_router(patient_clinical_conclusions.router)

# P4 replaces only the two normal hard-delete handlers. The scientific upload,
# analysis, report and history routes remain untouched. A user DELETE now records
# recoverable trash metadata; no image file or clinical analysis row is destroyed.
_HARD_DELETE_PATHS = {
    "/panoramic/{analysis_id}",
    "/cephalo/{analysis_id}",
}
ia.router.routes = [
    route
    for route in ia.router.routes
    if not (
        getattr(route, "path", None) in _HARD_DELETE_PATHS
        and "DELETE" in (getattr(route, "methods", set()) or set())
    )
]
ia.router.include_router(imaging_lifecycle_p4.router)
