# Digital Crown Routers Package

# Patient/clinical extensions are mounted under the canonical routers so the public
# URLs and access-control conventions stay unchanged.
from . import patients as patients
from . import patient_odontogram as patient_odontogram
from . import patient_clinical_conclusions as patient_clinical_conclusions
from . import patient_master_plan_p3 as patient_master_plan_p3
from . import patient_journey_p4 as patient_journey_p4
from . import patient_financial_p6 as patient_financial_p6
from . import patient_clinical_context as patient_clinical_context
from . import ia as ia
from . import imaging_lifecycle_p4 as imaging_lifecycle_p4
from . import cephalo_calibration_provenance as cephalo_calibration_provenance
from . import cephalo_landmark_refinement as cephalo_landmark_refinement
from . import cephalo_analysis_read as cephalo_analysis_read
from . import clinics as clinics
from . import license_portability_p4 as license_portability_p4
from . import clinic_identity_p4 as clinic_identity_p4
from . import clinic_profile_p4 as clinic_profile_p4
from . import clinic_setup_p4 as clinic_setup_p4

# Bring P3 Master Plan truth forward: same public GET/PUT path, immutable revision per
# successful save, plus /master-plan/revisions.
patients.router.routes = [route for route in patients.router.routes if not (getattr(route, "path", None) == "/{patient_id}/master-plan" and ({"GET", "PUT"} & (getattr(route, "methods", set()) or set())))]
patients.router.routes = [route for route in patients.router.routes if not (getattr(route, "path", None) == "/{patient_id}/journey" and "GET" in (getattr(route, "methods", set()) or set()))]
patients.router.routes = [route for route in patients.router.routes if not (getattr(route, "path", None) == "/{patient_id}/financial-snapshot" and "GET" in (getattr(route, "methods", set()) or set()))]
patients.router.include_router(patient_odontogram.router)
patients.router.include_router(patient_clinical_conclusions.router)
patients.router.include_router(patient_master_plan_p3.router)
patients.router.include_router(patient_journey_p4.router)
patients.router.include_router(patient_financial_p6.router)
patients.router.include_router(patient_clinical_context.router)
_HARD_DELETE_PATHS = {"/panoramic/{analysis_id}", "/cephalo/{analysis_id}"}
ia.router.routes = [route for route in ia.router.routes if not (getattr(route, "path", None) in _HARD_DELETE_PATHS and "DELETE" in (getattr(route, "methods", set()) or set()))]
ia.router.include_router(imaging_lifecycle_p4.router)
ia.router.routes = [route for route in ia.router.routes if not (getattr(route, "path", None) == "/analyses/{analysis_id}/calibrate" and "POST" in (getattr(route, "methods", set()) or set()))]
ia.router.include_router(cephalo_calibration_provenance.router)
ia.router.routes = [route for route in ia.router.routes if not (getattr(route, "path", None) == "/analyses/{analysis_id}" and "PUT" in (getattr(route, "methods", set()) or set()))]
ia.router.include_router(cephalo_landmark_refinement.router)
ia.router.routes = [route for route in ia.router.routes if not (getattr(route, "path", None) == "/analyses/{analysis_id}" and "GET" in (getattr(route, "methods", set()) or set()))]
ia.router.include_router(cephalo_analysis_read.router)
clinics.router.routes = [route for route in clinics.router.routes if not (getattr(route, "path", None) == "/recheck-license" and "POST" in (getattr(route, "methods", set()) or set()))]
clinics.router.include_router(license_portability_p4.router)
clinics.router.include_router(clinic_identity_p4.router)
clinics.router.routes = [route for route in clinics.router.routes if not (getattr(route, "path", None) == "/me" and ({"GET", "PUT"} & (getattr(route, "methods", set()) or set())))]
clinics.router.include_router(clinic_profile_p4.router)
clinics.router.routes = [route for route in clinics.router.routes if not (getattr(route, "path", None) == "/" and "POST" in (getattr(route, "methods", set()) or set()))]
clinics.router.include_router(clinic_setup_p4.router)
from . import mobile as mobile
from . import mobile_resource_bridge as mobile_resource_bridge
from . import mobile_patient_cockpit as mobile_patient_cockpit
mobile.router.include_router(mobile_resource_bridge.router)
mobile.router.include_router(mobile_patient_cockpit.router)
from . import mobile_waiting_room as mobile_waiting_room
mobile.router.routes = [route for route in mobile.router.routes if not (getattr(route, "path", None) in {"/snapshot", "/appointments"} and "GET" in (getattr(route, "methods", set()) or set()))]
mobile.router.include_router(mobile_waiting_room.router)
from . import mobile_push as mobile_push
mobile_push.install_secure_lan_url_overrides()
mobile.router.include_router(mobile_push.router)
from . import mobile_legacy as mobile_legacy
from . import mobile_passkey as mobile_passkey
from backend.services.mobile_biometric import install_mobile_biometric_identity_gate
mobile_passkey.install_stable_lan_url_overrides()
mobile.get_lan_base_url = mobile_legacy.get_lan_base_url
mobile.get_lan_frontend_url = mobile_legacy.get_lan_frontend_url
install_mobile_biometric_identity_gate(mobile_legacy)
mobile.router.include_router(mobile_passkey.router)
from . import partner_orders as partner_orders
from . import partner_dispatch as partner_dispatch
from . import partner_orders_p6 as partner_orders_p6
from . import partner_procurement as partner_procurement
from . import partner_receipts as partner_receipts
from . import partner_stock as partner_stock
from . import partner_receipts_p7 as partner_receipts_p7
from . import partner_stock_safety as partner_stock_safety
from . import partner_finance as partner_finance
partner_orders.router.routes = [route for route in partner_orders.router.routes if not (getattr(route, "path", None) == "/{order_id}" and "PATCH" in (getattr(route, "methods", set()) or set()))]
partner_receipts.router.routes = [route for route in partner_receipts.router.routes if not (getattr(route, "path", None) == "/{order_id}/receipt" and "POST" in (getattr(route, "methods", set()) or set()))]
partner_orders.router.include_router(partner_orders_p6.router)
partner_orders.router.include_router(partner_dispatch.router)
partner_orders.router.include_router(partner_procurement.router)
partner_orders.router.include_router(partner_receipts_p7.router)
partner_orders.router.include_router(partner_receipts.router)
partner_orders.router.include_router(partner_finance.router)
partner_stock.router.routes = [route for route in partner_stock.router.routes if not ((getattr(route, "path", None) == "/marketplace/items/{stock_item_id}/consume" and "POST" in (getattr(route, "methods", set()) or set())) or (getattr(route, "path", None) == "/marketplace/reorder-suggestions" and "GET" in (getattr(route, "methods", set()) or set())))]
from . import stock as stock
stock.router.include_router(partner_stock.router)
stock.router.include_router(partner_stock_safety.router)
from . import partner_catalog as partner_catalog
from . import partner_sync as partner_sync
from . import partner_sync_safety as partner_sync_safety
partner_sync_safety.install_partner_sync_identity_guard(partner_sync)
partner_catalog.router.include_router(partner_sync.router)
from . import media_core as media_core
patients.router.include_router(media_core.router)
from backend.models_document_provenance_p3 import install_document_provenance_p3
install_document_provenance_p3()
from . import documents as documents
from . import document_provenance_p3 as document_provenance_p3
documents.router.routes = [route for route in documents.router.routes if not (getattr(route, "path", None) == "/generate" and "POST" in (getattr(route, "methods", set()) or set()))]
patients.router.routes = [route for route in patients.router.routes if not (getattr(route, "path", None) == "/{patient_id}/pdf" and "POST" in (getattr(route, "methods", set()) or set()))]
documents.router.include_router(document_provenance_p3.documents_router)
patients.router.include_router(document_provenance_p3.patients_router)
from . import insurance_submissions as insurance_submissions
documents.router.include_router(insurance_submissions.router, prefix="/insurance-submissions")
from . import cephalo_clinical_studio as cephalo_clinical_studio
patients.router.include_router(cephalo_clinical_studio.router)

# LOT E mounts the read-only Connect Hub under the already-canonical intelligence surface.
from . import intelligence as intelligence
from . import connect_hub as connect_hub
intelligence.router.include_router(connect_hub.router)
