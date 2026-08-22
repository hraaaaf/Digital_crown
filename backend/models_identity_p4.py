"""P4B canonical clinic/practitioner identity extensions.

P1 fixed the ownership model:
- User owns practitioner identity.
- CabinetConfig owns organization identity.

These additive columns keep that contract without creating a parallel Practitioner table.
Legacy CabinetConfig.inpe is deliberately left untouched because its historical meaning is
ambiguous and must be classified explicitly during P5 migration.
"""
from __future__ import annotations

import logging

from sqlalchemy import String, inspect, text
from sqlalchemy.orm import mapped_column

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
    """Add P4B identity columns to existing installations, idempotently.

    Fresh databases receive the columns through ``Base.metadata.create_all``. Existing
    databases are altered only when the corresponding table already exists. No legacy
    value is copied or guessed here.
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
