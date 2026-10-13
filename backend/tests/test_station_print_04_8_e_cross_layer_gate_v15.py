"""04.8-E cross-layer DENY-FIRST contract, same source SHA only.

These static contract assertions are *supplementary* to the real JWT+clinical
FastAPI suite (#870), BCD SQL/PG multiprocess ledger suites (#862), and
Chromium BEFORE/AFTER on the mounted Station (#871). They cannot certify
a clinical permit or printer hardware.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest


ROOT = Path.cwd()  # GitHub job executes from checkout root; test copied outside backend conftest


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def function_node(path: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(source(path), filename=path)
    matches = [node for node in tree.body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1, (path, name)
    return matches[0]


def calls(fn: ast.FunctionDef) -> set[str]:
    return {
        node.func.id
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def test_cabinet_authenticated_route_must_stay_read_only_and_never_dispatch():
    path = "backend/routers/station_print_config_admin.py"
    fn = function_node(path, "check_cabinet_print_clinical_readiness")
    names = calls(fn)
    assert {"_owner", "require_same_origin_mutation", "_require_pin",
            "_find_workstation", "clinically_recheck_cabinet_print"} <= names
    assert not {
        "reserve_held_claim", "subprocess", "Popen", "run",
        "lp", "window", "print", "save_owner_configuration",
    } & names
    assert "Depends(get_current_user)" in ast.get_source_segment(source(path), fn)
    result = [
        node.value for node in ast.walk(fn)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
    ]
    assert len(result) == 1
    response = ast.literal_eval(result[0])
    assert response == {
        "status": "printing_unavailable", "printingAvailable": False,
        "claimCreated": False, "archiveVerified": False,
    }


def test_cabinet_clinical_source_has_no_positive_print_permit_or_ledger_write():
    path = "backend/services/station_print_cabinet_clinical_gate_v15.py"
    fn = function_node(path, "clinically_recheck_cabinet_print")
    names = calls(fn)
    assert {"care_sheet_state", "verified_care_sheet_bytes",
            "inspect_cabinet_care_sheet_preflight"} <= names
    assert not {"reserve_held_claim", "save_owner_configuration",
                "subprocess", "lp"} & names
    s = ast.get_source_segment(source(path), fn)
    assert "with_for_update()" in s
    assert 'reason="TRUSTED_PRINTER_CERTIFICATION_REQUIRED"' in s
    assert "allowed=False" in s
    assert "allowed=True" not in s
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "commit"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "db"
        for node in ast.walk(fn)
    )  # inspect executable calls, not safe mentions in docstrings


@pytest.mark.parametrize("name", ["station_care_sheet", "station_presence_receipt"])
def test_both_station_document_bytes_routes_fail_closed_423(name: str):
    path = "backend/routers/station_patient_session.py"
    fn = function_node(path, name)
    s = ast.get_source_segment(source(path), fn)
    assert "_identified_station_session_or_error(" in s
    assert re.search(r"raise HTTPException\(status_code=423, detail=\"STATION_PDF_REQUIRES_PERSONAL_COMPANION\"\)", s)
    assert not {"FileResponse", "StreamingResponse", "send_file", "read_pdf"} & calls(fn)


def test_trusted_printer_inventory_is_empty_pending_lot10():
    # Minimal-source LAB intentionally avoids app-wide ORM imports. The real
    # authenticated FastAPI path is covered by a different full-deps job.
    import sys
    import types
    for name, folder in (("backend", "backend"), ("backend.services", "backend/services")):
        if name not in sys.modules:
            package = types.ModuleType(name)
            package.__path__ = [str(ROOT / folder)]
            sys.modules[name] = package
    from backend.services.station_document_print_inventory import (
        independently_certified_printers_for_tenant,
    )
    from backend.services.station_document_print_configuration import (
        PrintConfigurationRejected,
    )

    assert independently_certified_printers_for_tenant(None, tenant_id=123) == {}
    for invalid in (0, -1, True, "123"):
        with pytest.raises(PrintConfigurationRejected):
            independently_certified_printers_for_tenant(None, tenant_id=invalid)


def test_real_station_ui_mount_remains_identified_only_and_inert():
    view = source("frontend/src/features/hub/StationPatientIdentity.tsx")
    panel = source("frontend/src/features/hub/StationPrintStatusPanel.tsx")
    service = source("frontend/src/services/stationPatientSession.ts")
    assert "if (status === 'identified' && session && purpose === 'documents')" in view
    assert view.count('<StationPrintStatusPanel language={language} status="disabled" />') == 1
    assert "data-station-print-status-slot" in view
    assert "window.print" not in view and "window.print" not in panel
    assert not re.search(r"\bfetch\s*\(|\baxios\b|\.post\(", panel)
    assert not re.search(r"\bonClick\s*=|\bonSubmit\s*=", panel)
    assert not re.search(r"/print-jobs|/station-print-config|\.pdf", service)
    assert 'status = \'disabled\'' in panel
    assert "dir={language === 'ar' ? 'rtl' : 'ltr'}" in panel


def test_synthetic_lab_is_not_a_prod_print_dispatch_endpoint():
    lab = source("backend/scripts/certify_print_ledger_to_virtual_spool_lab_v15.py")
    assert 'os.environ.get("GITHUB_ACTIONS") != "true"' in lab
    assert 'os.environ.get("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB") != "1"' in lab
    assert '"clinical_cabinet_permission_proven": False' in lab
    assert '"production_path_dispatch_enabled": False' in lab
    assert '"claim_marked_uncertain_before_virtual_spool": True' in lab
    assert '"virtual_outbox_single_attempt_fenced": True' in lab
    assert '"clinical_print_permit_issued": False' in lab
    outbox = source("backend/services/station_print_virtual_outbox_lab_v15.py")
    assert '"station_print_virtual_outbox_lab"' in outbox
    assert 'os.environ.get("GITHUB_ACTIONS") != "true"' in outbox
    assert 'os.environ.get("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB") != "1"' in outbox
    assert "allowed=True" not in outbox


def test_pending_evidence_and_uncertain_review_can_never_become_print_permits():
    """04.8 software gate: evidence intake is not field certification."""
    src = source("backend/services/station_print_attestation_recovery_v15.py")
    inventory = source("backend/services/station_document_print_inventory.py")
    assert '"pending_field_verification"' in src
    assert "status = 'pending_field_verification'" in src
    assert '"investigating", "evidence_checked", "escalated"' in src
    assert "reserve_held_claim(" not in src
    assert "mark_uncertain(" not in src
    assert "def enable_print" not in src
    assert "def certify_printer" not in src
    assert "def release_print" not in src
    assert "return {}" in inventory  # no independently field-certified printer source yet
    migration = source("alembic/versions/neo000000030_print_evidence_investigation.py")
    assert "pending_field_verification" in migration
    assert "fk_device_evidence_unverified_draft" in migration
    assert "fk_uncertain_review_claim" in migration


def test_owner_blocked_print_view_cannot_dispatch_or_expose_clinical_data():
    backend = source("backend/routers/station_print_config_admin.py")
    service = source("backend/services/station_print_attestation_recovery_v15.py")
    ui = source("frontend/src/features/admin/Settings/tabs/BlockedPrintJobsReadOnly.tsx")
    assert '@router.get("/station-print-config/blocked-jobs")' in backend
    assert '@router.post("/station-print-config/blocked-jobs")' not in backend
    assert 'Depends(get_current_user)' in backend
    assert '_find_workstation(request, db, tenant_id)' in backend
    assert 'retrySupported": False' in backend
    assert '"Cache-Control"] = "no-store"' in backend
    assert 'list_blocked_print_jobs' in service
    assert 'claims.c.state == "uncertain"' in service
    assert "claims.c.tenant_id == tenant_id" in service
    assert "delivery_key[:12]" in service
    assert "retry_print(" not in backend
    assert "reserve_held_claim(" not in backend
    assert "post(" not in ui and "put(" not in ui
    assert "/admin/station-print-config/blocked-jobs" in ui
    assert "Réimprimer</button>" not in ui
    assert "pdfBytes" not in ui


def test_print_audit_ddl_is_installed_by_both_operator_baselines():
    guard = source("backend/core/print_audit_ddl.py")
    migration = source("alembic/versions/neo000000031_print_audit_append_only.py")
    pg = source("backend/core/postgresql_alembic_baseline.py")
    sqlite = source("backend/core/sqlite_alembic_baseline.py")
    assert '"station_print_uncertain_reviews"' in guard
    assert '"station_print_claim_events"' in guard
    assert "CREATE OR REPLACE TRIGGER" in guard
    assert "RAISE(ABORT" in guard
    assert "install_append_only_print_audit_guards(op.get_bind())" in migration
    assert "install_append_only_print_audit_guards(connection)" in pg
    assert "install_append_only_print_audit_guards(connection)" in sqlite
    assert '"neo000000031"' in source("backend/core/schema_runtime.py")
