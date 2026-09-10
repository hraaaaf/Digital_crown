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

# Scientific Core calibration provenance replaces only the legacy calibration POST.
# The public URL is unchanged; the replacement persists the measured points, method,
# operator and timestamp atomically with the typed evidence revision.
ia.router.routes = [
    route
    for route in ia.router.routes
    if not (
        getattr(route, "path", None) == "/analyses/{analysis_id}/calibrate"
        and "POST" in (getattr(route, "methods", set()) or set())
    )
]
ia.router.include_router(cephalo_calibration_provenance.router)

# Scientific Core landmark audit replaces only the legacy refinement PUT. The stable
# public path remains unchanged while practitioner identity comes from authentication.
ia.router.routes = [
    route
    for route in ia.router.routes
    if not (
        getattr(route, "path", None) == "/analyses/{analysis_id}"
        and "PUT" in (getattr(route, "methods", set()) or set())
    )
]
ia.router.include_router(cephalo_landmark_refinement.router)

# Scientific Core typed read authority replaces only the legacy analysis GET. Once a
# typed evidence graph exists, the four CRANIOM linear values come from MeasurementEvidence
# or fail closed; legacy rows without a graph keep their historical read behavior.
ia.router.routes = [
    route
    for route in ia.router.routes
    if not (
        getattr(route, "path", None) == "/analyses/{analysis_id}"
        and "GET" in (getattr(route, "methods", set()) or set())
    )
]
ia.router.include_router(cephalo_analysis_read.router)

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
# reads stay compatible with the historical response contract.
clinics.router.routes = [
    route
    for route in clinics.router.routes
    if not (
        getattr(route, "path", None) == "/me"
        and ({"GET", "PUT"} & (getattr(route, "methods", set()) or set()))
    )
]
clinics.router.include_router(clinic_profile_p4.router)

# P4D replaces only the legacy first-run setup endpoint. The public POST /setup-clinic
# remains unchanged while payload validation and practitioner scoping move to the
# dedicated facade.
clinics.router.routes = [
    route
    for route in clinics.router.routes
    if not (
        getattr(route, "path", None) == "/setup-clinic"
        and "POST" in (getattr(route, "methods", set()) or set())
    )
]
clinics.router.include_router(clinic_setup_p4.router)

from . import auth as auth
from . import cabinet as cabinet
from . import cabinet_member_p4 as cabinet_member_p4
from . import cabinet_setup_p4 as cabinet_setup_p4
from . import cabinet_activation_p4 as cabinet_activation_p4
from . import cabinet_session_p4 as cabinet_session_p4
from . import cabinet_backup_p4 as cabinet_backup_p4
from . import cabinet_portability_p4 as cabinet_portability_p4

# P4 cabinet membership and setup endpoints are mounted under the canonical cabinet
# router so external URLs remain /api/cabinet/*.
cabinet.router.include_router(cabinet_member_p4.router)
cabinet.router.include_router(cabinet_setup_p4.router)
cabinet.router.include_router(cabinet_activation_p4.router)
cabinet.router.include_router(cabinet_session_p4.router)
cabinet.router.include_router(cabinet_backup_p4.router)
cabinet.router.include_router(cabinet_portability_p4.router)

from . import documents as documents
from . import document_archive_p4 as document_archive_p4
from . import document_template_p4 as document_template_p4
from . import document_share_p4 as document_share_p4
from . import document_portability_p4 as document_portability_p4
from . import document_pdf_p4 as document_pdf_p4
from . import document_signing_p4 as document_signing_p4
from . import document_storage_p4 as document_storage_p4
from . import document_office_p4 as document_office_p4
from . import document_sync_p4 as document_sync_p4
from . import document_print_p4 as document_print_p4
from . import document_review_p4 as document_review_p4
from . import document_search_p4 as document_search_p4
from . import document_export_p4 as document_export_p4
from . import document_import_p4 as document_import_p4
from . import document_integrity_p4 as document_integrity_p4
from . import document_retention_p4 as document_retention_p4
from . import document_audit_p4 as document_audit_p4
from . import document_reconciliation_p4 as document_reconciliation_p4
from . import document_compliance_p4 as document_compliance_p4
from . import document_case_p4 as document_case_p4
from . import document_storage_policy_p4 as document_storage_policy_p4
from . import document_validation_p4 as document_validation_p4
from . import document_lifecycle_p4 as document_lifecycle_p4
from . import document_access_p4 as document_access_p4
from . import document_backup_p4 as document_backup_p4
from . import document_restore_p4 as document_restore_p4
from . import document_migration_p4 as document_migration_p4
from . import document_disaster_recovery_p4 as document_disaster_recovery_p4
from . import document_observability_p4 as document_observability_p4
from . import document_repair_p4 as document_repair_p4
from . import document_health_p4 as document_health_p4
from . import document_reindex_p4 as document_reindex_p4
from . import document_gc_p4 as document_gc_p4
from . import document_freeze_p4 as document_freeze_p4
from . import document_release_p4 as document_release_p4
from . import document_legal_hold_p4 as document_legal_hold_p4
from . import document_ownership_p4 as document_ownership_p4
from . import document_transfer_p4 as document_transfer_p4
from . import document_security_p4 as document_security_p4
from . import document_encryption_p4 as document_encryption_p4
from . import document_key_rotation_p4 as document_key_rotation_p4
from . import document_signature_validation_p4 as document_signature_validation_p4
from . import document_worm_p4 as document_worm_p4
from . import document_hash_p4 as document_hash_p4
from . import document_manifest_p4 as document_manifest_p4
from . import document_verification_p4 as document_verification_p4
from . import document_attestation_p4 as document_attestation_p4
from . import document_chain_p4 as document_chain_p4
from . import document_provenance_p4 as document_provenance_p4
from . import document_catalog_p4 as document_catalog_p4
from . import document_archive_index_p4 as document_archive_index_p4
from . import document_archive_search_p4 as document_archive_search_p4
from . import document_archive_restore_p4 as document_archive_restore_p4
from . import document_archive_export_p4 as document_archive_export_p4
from . import document_archive_import_p4 as document_archive_import_p4
from . import document_archive_integrity_p4 as document_archive_integrity_p4
from . import document_archive_retention_p4 as document_archive_retention_p4
from . import document_archive_audit_p4 as document_archive_audit_p4
from . import document_archive_compliance_p4 as document_archive_compliance_p4
from . import document_archive_observability_p4 as document_archive_observability_p4
from . import document_archive_repair_p4 as document_archive_repair_p4
from . import document_archive_health_p4 as document_archive_health_p4
from . import document_archive_gc_p4 as document_archive_gc_p4
from . import document_archive_freeze_p4 as document_archive_freeze_p4
from . import document_archive_release_p4 as document_archive_release_p4
from . import document_archive_legal_hold_p4 as document_archive_legal_hold_p4
from . import document_archive_ownership_p4 as document_archive_ownership_p4
from . import document_archive_transfer_p4 as document_archive_transfer_p4
from . import document_archive_security_p4 as document_archive_security_p4
from . import document_archive_encryption_p4 as document_archive_encryption_p4
from . import document_archive_key_rotation_p4 as document_archive_key_rotation_p4
from . import document_archive_signature_validation_p4 as document_archive_signature_validation_p4
from . import document_archive_worm_p4 as document_archive_worm_p4
from . import document_archive_hash_p4 as document_archive_hash_p4
from . import document_archive_manifest_p4 as document_archive_manifest_p4
from . import document_archive_verification_p4 as document_archive_verification_p4
from . import document_archive_attestation_p4 as document_archive_attestation_p4
from . import document_archive_chain_p4 as document_archive_chain_p4
from . import document_archive_provenance_p4 as document_archive_provenance_p4
from . import document_archive_catalog_p4 as document_archive_catalog_p4
from . import partner_catalog as partner_catalog
from . import partner_sync as partner_sync
from . import partner_sync_safety as partner_sync_safety
partner_sync_safety.install_partner_sync_identity_guard(partner_sync)
partner_catalog.router.include_router(partner_sync.router)
