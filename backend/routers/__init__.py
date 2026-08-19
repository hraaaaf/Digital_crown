# Digital Crown Routers Package

# Patient/clinical extensions are mounted under the canonical routers so the public
# URLs and access-control conventions stay unchanged.
from . import patients as patients
from . import patient_odontogram as patient_odontogram
from . import patient_clinical_conclusions as patient_clinical_conclusions
from . import patient_master_plan_p3 as patient_master_plan_p3
from . import patient_journey_p4 as patient_journey_p4
from . import patient_financial_p6 as patient_financial_p6
from . import ia as ia
from . import imaging_lifecycle_p4 as imaging_lifecycle_p4

# Bring P3 Master Plan truth forward: same public GET/PUT path, immutable revision per
# successful save, plus /master-plan/revisions.
patients.router.routes = [
    route
    for route in patients.router.routes
    if not (
        getattr(route, "path", None) == "/{patient_id}/master-plan"
        and ({"GET", "PUT"} & (getattr(route, "methods", set()) or set()))
    )
]

# Replace only the P2 Journey GET handler. Milestone create/delete routes remain on the
# original patients router. The P4 facade delegates to the P2 aggregator then removes
# recoverably trashed Pano/Cephalo events.
patients.router.routes = [
    route
    for route in patients.router.routes
    if not (
        getattr(route, "path", None) == "/{patient_id}/journey"
        and "GET" in (getattr(route, "methods", set()) or set())
    )
]

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
patients.router.include_router(patient_master_plan_p3.router)
patients.router.include_router(patient_journey_p4.router)
patients.router.include_router(patient_financial_p6.router)

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
