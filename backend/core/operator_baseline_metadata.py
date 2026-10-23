"""Metadata registration shared by Alembic and empty-database baseline tests.

Only adds the explicitly versioned, default-inert tables needed for a fresh
SQLite/SQLCipher or PostgreSQL operator baseline. Never creates a database,
imports backend.database, starts a worker, or grants a print permit.
"""
from __future__ import annotations

from sqlalchemy.schema import MetaData


def register_operator_baseline_metadata(metadata: MetaData) -> None:
    # Same source-locked application declarations used by alembic/env.py.
    from backend import models_patient_companion as _patient_companion  # noqa: F401
    from backend import models_patient_companion_notifications as _notifications  # noqa: F401
    from backend.services import cabinet_catalog_store as _catalog  # noqa: F401

    # The isolated print stores include a synthetic users stub. Never clone it:
    # the operator metadata must use the real Cabinet users table.
    from backend.services.station_document_print_store import schema as print_schema
    for name in (
        "station_print_configurations",
        "station_print_config_stations",
        "station_print_config_printers",
        "station_print_config_audit",
    ):
        if name not in metadata.tables:
            print_schema.tables[name].to_metadata(metadata)

    from backend.services.station_print_printer_draft_lab import SCHEMA as drafts
    from backend.services.station_print_held_claims_lab import SCHEMA as held
    for name, source in (
        ("station_print_printer_drafts", drafts),
        ("station_print_held_claims", held),
        ("station_print_claim_events", held),
    ):
        if name not in metadata.tables:
            source.tables[name].to_metadata(metadata)

    from backend.services.station_print_attestation_recovery_v15 import (
        device_evidence,
        uncertain_reviews,
    )
    for table in (device_evidence, uncertain_reviews):
        if table.name not in metadata.tables:
            table.to_metadata(metadata)

    # The signed baseline cannot legitimately be stamped if an append-only
    # audit table is absent from the snapshot that receives its SQL guards.
    from backend.core.print_audit_ddl import PROTECTED_PRINT_AUDITS
    missing = sorted(set(PROTECTED_PRINT_AUDITS) - set(metadata.tables))
    if missing:
        raise RuntimeError("PRINT_AUDIT_BASELINE_METADATA_INCOMPLETE: " + ", ".join(missing))
