"""P4B canonical clinic/practitioner identity extensions.

P1 fixed the ownership model:
- User owns practitioner identity.
- CabinetConfig owns organization identity.

These additive columns keep that contract without creating a parallel Practitioner table.
Legacy CabinetConfig.inpe is deliberately left untouched because its historical meaning is
ambiguous and must never be classified automatically.
"""
from __future__ import annotations

import logging

from sqlalchemy import String, inspect, text
from sqlalchemy.orm import Session, mapped_column

from backend.models import CabinetConfig, User

logger = logging.getLogger(__name__)


# SQLAlchemy declarative classes support additive mapped attributes after declaration.
# Guard each addition so reloads/test collection cannot register the same column twice.
if "nom_complet_ar" not in User.__table__.c:
    User.nom_complet_ar = mapped_column(String(255), nullable=True)
if "inpe_professionnel" not in User.__table__.c:
    User.inpe_professionnel = mapped_column(String(50), nullable=True)
if "inpe_etablissement" not in CabinetConfig.__table__.c:
    CabinetConfig.inpe_etablissement = mapped_column(String(50), nullable=True)


_IDENTITY_COLUMNS = {
    "users": (
        ("nom_complet_ar", "VARCHAR(255)"),
        ("inpe_professionnel", "VARCHAR(50)"),
    ),
    "cabinet_configs": (
        ("inpe_etablissement", "VARCHAR(50)"),
    ),
}


def migrate_identity_columns(engine) -> None:
    """Upgrade existing installations to the canonical identity contract, idempotently.

    Phase 1 adds the P4B columns when needed. Phase 2 runs the deliberately conservative
    P5 legacy backfill: only empty canonical practitioner-name fields may be populated.
    Ambiguous INPE, legal IDs, contacts, footer and custom headers are never inferred or
    rewritten here.
    """
    inspector = inspect(engine)
    for table_name, columns in _IDENTITY_COLUMNS.items():
        if not inspector.has_table(table_name):
            continue
        existing = {col["name"] for col in inspector.get_columns(table_name)}
        for column_name, column_type in columns:
            if column_name in existing:
                continue
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    ))
                existing.add(column_name)
                logger.info("Added P4B identity column %s.%s", table_name, column_name)
            except Exception:
                # A concurrent/idempotent startup may have added the column after the
                # inspector snapshot. Re-check before treating the migration as failed.
                refreshed = {col["name"] for col in inspect(engine).get_columns(table_name)}
                if column_name not in refreshed:
                    raise

    # P5: only run the value migration when both backing tables exist. Keeping this on the
    # same startup hook as P4E guarantees schema-before-data ordering on old installations.
    refreshed_inspector = inspect(engine)
    if refreshed_inspector.has_table("users") and refreshed_inspector.has_table("cabinet_configs"):
        from backend.services.clinic_identity_legacy_migration import migrate_legacy_identity_values

        with Session(engine) as db:
            report = migrate_legacy_identity_values(db)
        if report.changed or report.practitioner_fr_conflicts or report.practitioner_ar_conflicts:
            logger.info(
                "P5 identity migration: scanned=%s changed=%s conflicts_fr=%s conflicts_ar=%s",
                report.scanned,
                report.changed,
                report.practitioner_fr_conflicts,
                report.practitioner_ar_conflicts,
            )
