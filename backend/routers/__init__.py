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
from . import clinics as clinics
from . import license_portability_p4 as license_portability_p4
from . import clinic_identity_p4 as clinic_identity_p4
from . import clinic_profile_p4 as clinic_profile_p4
from . import clinic_setup_p4 as clinic_setup_p4

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

# Portability P4 replaces the legacy env-based licence recheck. The stable public URL
# remains unchanged, but identity now comes from the authenticated CabinetConfig.
clinics.router.routes = [
    route
    for route in clinics.router.routes
    if not (
        getattr(route, "path", None) == "/recheck-license"
        and "POST" in (getattr(route, "methods", set()) or set())
    )
]
clinics.router.include_router(license_portability_p4.router)

# P4B keeps a targeted practitioner contract for direct identity operations.
clinics.router.include_router(clinic_identity_p4.router)

# P4C replaces only the legacy Settings GET/PUT /me handlers. The stable public URL is
# preserved while persistence is split internally between User and CabinetConfig and
# committed atomically.
clinics.router.routes = [
    route
    for route in clinics.router.routes
    if not (
        getattr(route, "path", None) == "/me"
        and ({"GET", "PUT"} & (getattr(route, "methods", set()) or set()))
    )
]
clinics.router.include_router(clinic_profile_p4.router)

# P4D replaces the legacy setup POST / handler. Draft persistence now uses the same
# User/CabinetConfig ownership split as Settings, and completion is an explicit second
# phase so failed optional uploads cannot leave a falsely initialized cabinet.
clinics.router.routes = [
    route
    for route in clinics.router.routes
    if not (
        getattr(route, "path", None) == "/"
        and "POST" in (getattr(route, "methods", set()) or set())
    )
]
clinics.router.include_router(clinic_setup_p4.router)

# M4-A adds resource-bound mobile context routes without modifying the existing
# M6.4 destination bridge implementation. Importing here also registers the context
# table in shared SQLAlchemy metadata before application startup create_all().
from . import mobile as mobile
from . import mobile_resource_bridge as mobile_resource_bridge
mobile.router.include_router(mobile_resource_bridge.router)

# M6-D2 registers the device/user-bound Web Push table before create_all(), mounts the
# push API under /api/mobile and keeps LAN URLs aligned with the selected HTTPS runtime.
from . import mobile_push as mobile_push
mobile_push.install_secure_lan_url_overrides()
mobile.router.include_router(mobile_push.router)

# M6-I registers WebAuthn tables before create_all(), moves secure LAN discovery to
# the stable mDNS RP hostname and gates all canonical mobile identities after enable.
from . import mobile_legacy as mobile_legacy
from . import mobile_passkey as mobile_passkey
from backend.services.mobile_biometric import install_mobile_biometric_identity_gate
mobile_passkey.install_stable_lan_url_overrides()
# Keep the compatibility re-export used by the legacy admin pairing endpoint aligned
# with the same stable frontend origin selected above.
mobile.get_lan_base_url = mobile_legacy.get_lan_base_url
mobile.get_lan_frontend_url = mobile_legacy.get_lan_frontend_url
install_mobile_biometric_identity_gate(mobile_legacy)
mobile.router.include_router(mobile_passkey.router)

# Marketplace P6 replaces the legacy manual DRAFT->SENT PATCH by a dispatch-proof gate,
# registers transport/procurement/receipt tables before create_all(), then mounts all
# P6 lifecycles under the canonical /api/partner-orders router.
from . import partner_orders as partner_orders
from . import partner_dispatch as partner_dispatch
from . import partner_orders_p6 as partner_orders_p6
from . import partner_procurement as partner_procurement
from . import partner_receipts as partner_receipts
partner_orders.router.routes = [
    route
    for route in partner_orders.router.routes
    if not (
        getattr(route, "path", None) == "/{order_id}"
        and "PATCH" in (getattr(route, "methods", set()) or set())
    )
]
partner_orders.router.include_router(partner_orders_p6.router)
partner_orders.router.include_router(partner_dispatch.router)
partner_orders.router.include_router(partner_procurement.router)
partner_orders.router.include_router(partner_receipts.router)
