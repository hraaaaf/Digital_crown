"""make the remaining runtime compatibility schema explicit

Revision ID: d0b000000002
Revises: d0b000000001
Create Date: 2026-09-15

Older cabinet boots added these fields opportunistically through ``database.py``.
This migration makes that additive contract reproducible before the API starts.
Existing values are preserved; the only data operation is the former conservative
identity backfill, which fills an empty canonical name from its matching legacy
cabinet copy and never overwrites a non-empty value.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d0b000000002"
down_revision: Union[str, None] = "d0b000000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector(bind):
    return sa.inspect(bind)


def _add_column_if_missing(bind, table: str, column: sa.Column) -> None:
    inspector = _inspector(bind)
    if not inspector.has_table(table):
        raise RuntimeError(f"Required schema table is missing: {table}")
    existing = {item["name"] for item in inspector.get_columns(table)}
    if column.name not in existing:
        op.add_column(table, column)


def _create_index_if_missing(bind, name: str, table: str, columns: list[str], *, unique: bool = False) -> None:
    if not _inspector(bind).has_table(table):
        raise RuntimeError(f"Required schema table is missing: {table}")
    indexes = {item["name"] for item in _inspector(bind).get_indexes(table)}
    if name not in indexes:
        op.create_index(name, table, columns, unique=unique)


def _ensure_payment_status_enum(bind) -> None:
    if bind.dialect.name != "postgresql":
        return
    if not _inspector(bind).has_table("actes"):
        raise RuntimeError("Required schema table is missing: actes")

    enum_row = bind.execute(sa.text("""
        SELECT n.nspname AS schema_name, t.typname AS type_name
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_type t ON t.oid = a.atttypid
        WHERE c.relname = 'actes'
          AND a.attname = 'statut_paiement'
          AND a.attnum > 0
          AND NOT a.attisdropped
          AND t.typtype = 'e'
          AND n.nspname = current_schema()
        LIMIT 1
    """)).mappings().first()
    if not enum_row:
        raise RuntimeError(
            "Critical payment schema mismatch: actes.statut_paiement PostgreSQL enum not found"
        )

    exists = bind.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = :schema_name
              AND t.typname = :type_name
              AND e.enumlabel = 'A_ENCAISSER'
        )
    """), {
        "schema_name": enum_row["schema_name"],
        "type_name": enum_row["type_name"],
    }).scalar()
    if exists:
        return

    preparer = bind.dialect.identifier_preparer
    qualified_type = (
        f"{preparer.quote(enum_row['schema_name'])}."
        f"{preparer.quote(enum_row['type_name'])}"
    )
    bind.execute(sa.text(
        f"ALTER TYPE {qualified_type} ADD VALUE IF NOT EXISTS 'A_ENCAISSER'"
    ))


def _backfill_identity_values(bind) -> None:
    """Preserve the old, conservative P5 behavior as an explicit data step."""
    bind.execute(sa.text("""
        UPDATE users
        SET nom_complet = (
            SELECT cabinet_configs.nom_praticien
            FROM cabinet_configs
            WHERE cabinet_configs.owner_id = users.id
            LIMIT 1
        )
        WHERE (nom_complet IS NULL OR TRIM(nom_complet) = '')
          AND EXISTS (
            SELECT 1
            FROM cabinet_configs
            WHERE cabinet_configs.owner_id = users.id
              AND cabinet_configs.nom_praticien IS NOT NULL
              AND TRIM(cabinet_configs.nom_praticien) <> ''
          )
    """))
    bind.execute(sa.text("""
        UPDATE users
        SET nom_complet_ar = (
            SELECT cabinet_configs.nom_praticien_ar
            FROM cabinet_configs
            WHERE cabinet_configs.owner_id = users.id
            LIMIT 1
        )
        WHERE (nom_complet_ar IS NULL OR TRIM(nom_complet_ar) = '')
          AND EXISTS (
            SELECT 1
            FROM cabinet_configs
            WHERE cabinet_configs.owner_id = users.id
              AND cabinet_configs.nom_praticien_ar IS NOT NULL
              AND TRIM(cabinet_configs.nom_praticien_ar) <> ''
          )
    """))


def _ensure_catalog_tables(bind) -> None:
    inspector = _inspector(bind)
    tables = set(inspector.get_table_names())

    if "cabinet_specialties" not in tables:
        op.create_table(
            "cabinet_specialties",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("employer_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("color", sa.String(length=20), nullable=True),
            sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employer_id", "name", name="uq_cabinet_specialty_name"),
        )
    _create_index_if_missing(bind, "ix_cabinet_specialties_employer_id", "cabinet_specialties", ["employer_id"])

    if "cabinet_pathologies" not in tables:
        op.create_table(
            "cabinet_pathologies",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("employer_id", sa.Integer(), nullable=False),
            sa.Column("specialty_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["specialty_id"], ["cabinet_specialties.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "employer_id", "specialty_id", "name", name="uq_cabinet_pathology_name"
            ),
        )
    _create_index_if_missing(bind, "ix_cabinet_pathologies_employer_id", "cabinet_pathologies", ["employer_id"])
    _create_index_if_missing(bind, "ix_cabinet_pathologies_specialty_id", "cabinet_pathologies", ["specialty_id"])

    if "cabinet_catalog_acts" not in tables:
        op.create_table(
            "cabinet_catalog_acts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("employer_id", sa.Integer(), nullable=False),
            sa.Column("specialty_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=True),
            sa.Column("base_price", sa.Float(), nullable=False),
            sa.Column("color", sa.String(length=20), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["specialty_id"], ["cabinet_specialties.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employer_id", "code", name="uq_cabinet_act_code"),
        )
    _create_index_if_missing(bind, "ix_cabinet_catalog_acts_employer_id", "cabinet_catalog_acts", ["employer_id"])
    _create_index_if_missing(bind, "ix_cabinet_catalog_acts_specialty_id", "cabinet_catalog_acts", ["specialty_id"])


def _ensure_agenda_mode_enum(bind) -> None:
    if bind.dialect.name != "postgresql":
        return
    bind.execute(sa.text("""
        DO $$
        BEGIN
            CREATE TYPE agendamode AS ENUM ('EXACT', 'BLOCK');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """))


def _ensure_agenda_tables(bind) -> None:
    """Version the legacy Agenda tables and tenant columns used by the router."""
    tables = set(_inspector(bind).get_table_names())
    if "cabinet_settings" not in tables:
        _ensure_agenda_mode_enum(bind)
        op.create_table(
            "cabinet_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("opening_time_morning", sa.String(length=5), nullable=True),
            sa.Column("closing_time_morning", sa.String(length=5), nullable=True),
            sa.Column("opening_time_afternoon", sa.String(length=5), nullable=True),
            sa.Column("closing_time_afternoon", sa.String(length=5), nullable=True),
            sa.Column("is_continuous", sa.Boolean(), nullable=True),
            sa.Column(
                "agenda_mode",
                sa.Enum("EXACT", "BLOCK", name="agendamode", create_type=False),
                nullable=True,
            ),
            sa.Column("use_tickets", sa.Boolean(), nullable=True),
            sa.Column("employer_id", sa.Integer(), nullable=True),
            sa.Column("weekly_schedule_json", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        _add_column_if_missing(bind, "cabinet_settings", sa.Column("employer_id", sa.Integer(), nullable=True))
        _add_column_if_missing(bind, "cabinet_settings", sa.Column("weekly_schedule_json", sa.Text(), nullable=True))
    _create_index_if_missing(bind, "ix_cabinet_settings_id", "cabinet_settings", ["id"])
    _create_index_if_missing(bind, "ix_cabinet_settings_employer_id", "cabinet_settings", ["employer_id"])

    if "agenda_exceptions" not in tables:
        op.create_table(
            "agenda_exceptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("start_date", sa.DateTime(), nullable=False),
            sa.Column("end_date", sa.DateTime(), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=False),
            sa.Column("is_holiday", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("employer_id", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        _add_column_if_missing(bind, "agenda_exceptions", sa.Column("employer_id", sa.Integer(), nullable=True))
    _create_index_if_missing(bind, "ix_agenda_exceptions_id", "agenda_exceptions", ["id"])
    _create_index_if_missing(bind, "ix_agenda_exceptions_employer_id", "agenda_exceptions", ["employer_id"])


def upgrade() -> None:
    bind = op.get_bind()

    # Columns historically added by database.py compatibility functions.
    _add_column_if_missing(bind, "appointments", sa.Column("source", sa.String(length=50), nullable=True))
    _add_column_if_missing(bind, "appointments", sa.Column("phone", sa.String(length=30), nullable=True))
    _add_column_if_missing(bind, "appointments", sa.Column("confirmed_by_id", sa.Integer(), nullable=True))
    _add_column_if_missing(bind, "appointments", sa.Column("confirmed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(bind, "appointments", sa.Column("expires_at", sa.DateTime(), nullable=True))

    _add_column_if_missing(bind, "actes", sa.Column("document_archive_id", sa.Integer(), nullable=True))
    _create_index_if_missing(bind, "ix_actes_document_archive_id", "actes", ["document_archive_id"])
    _add_column_if_missing(bind, "actes", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    _create_index_if_missing(bind, "ix_actes_deleted_at", "actes", ["deleted_at"])

    _add_column_if_missing(bind, "patients", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    _create_index_if_missing(bind, "ix_patients_deleted_at", "patients", ["deleted_at"])
    _add_column_if_missing(bind, "patients", sa.Column("deleted_by", sa.Integer(), nullable=True))

    _add_column_if_missing(bind, "proactive_alerts", sa.Column("snoozed_until", sa.DateTime(), nullable=True))

    for name, column in (
        ("header_logo_offset_x", sa.Column("header_logo_offset_x", sa.Float(), nullable=True)),
        ("header_logo_offset_y", sa.Column("header_logo_offset_y", sa.Float(), nullable=True)),
        ("qr_code_offset_x", sa.Column("qr_code_offset_x", sa.Float(), nullable=True)),
        ("qr_code_offset_y", sa.Column("qr_code_offset_y", sa.Float(), nullable=True)),
        ("content_offset_y", sa.Column("content_offset_y", sa.Float(), nullable=True, server_default="0.0")),
        ("custom_specialty_fr", sa.Column("custom_specialty_fr", sa.String(length=255), nullable=True)),
        ("custom_specialty_ar", sa.Column("custom_specialty_ar", sa.String(length=255), nullable=True)),
        ("header_customized", sa.Column("header_customized", sa.Boolean(), nullable=True, server_default=sa.false())),
        ("inpe_etablissement", sa.Column("inpe_etablissement", sa.String(length=50), nullable=True)),
    ):
        _add_column_if_missing(bind, "cabinet_configs", column)

    _add_column_if_missing(bind, "users", sa.Column("nom_complet_ar", sa.String(length=255), nullable=True))
    _add_column_if_missing(bind, "users", sa.Column("inpe_professionnel", sa.String(length=50), nullable=True))

    _add_column_if_missing(bind, "zka_pairing_tokens", sa.Column("user_id", sa.Integer(), nullable=True))
    _create_index_if_missing(bind, "ix_zka_pairing_tokens_user_id", "zka_pairing_tokens", ["user_id"])
    _add_column_if_missing(bind, "zka_pairing_tokens", sa.Column("manual_code", sa.String(length=6), nullable=True))
    _create_index_if_missing(bind, "ix_zka_pairing_tokens_manual_code", "zka_pairing_tokens", ["manual_code"])

    _ensure_payment_status_enum(bind)
    _ensure_agenda_tables(bind)
    _ensure_catalog_tables(bind)
    _backfill_identity_values(bind)


def downgrade() -> None:
    # The fields are compatibility additions and are intentionally not removed by
    # a routine downgrade: doing so could destroy data written by a newer runtime.
    # A destructive schema rollback requires a separately reviewed restore plan.
    pass
