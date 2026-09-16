"""version NGAP reference and insurance linkage schema explicitly

Revision ID: d0b000000003
Revises: d0b000000002
Create Date: 2026-09-16

NGAP reference metadata and insurance linkage fields landed on master while the
boot/schema lot was in progress. Older boots could materialize them through
SQLAlchemy ``create_all`` hooks. This additive migration makes the same schema
explicit and repeatable for existing cabinet databases.

No patient, document or financial row is rewritten. Existing ``actes`` rows are
preserved and receive nullable linkage fields only.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d0b000000003"
down_revision: Union[str, None] = "d0b000000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NGAP_TABLE = "ngap_catalog_mappings"
_NGAP_COLUMNS = {
    "id",
    "catalog_act_id",
    "code_kind",
    "ngap_code",
    "coefficient",
    "official_label",
    "requires_prior_approval",
    "requires_radiograph",
    "reference_version",
    "mapping_rule_id",
    "verification_status",
    "source_authority",
    "source_url",
    "source_hash",
    "valid_from",
    "valid_to",
    "validated_by_practitioner_id",
    "validated_at",
    "created_at",
}
_NGAP_CHECKS = {
    "ck_ngap_mapping_code_kind",
    "ck_ngap_mapping_verification_status",
    "ck_ngap_mapping_ngap_payload",
    "ck_ngap_mapping_verified_evidence",
}


def _inspector(bind):
    return sa.inspect(bind)


def _require_table(bind, table: str) -> None:
    if not _inspector(bind).has_table(table):
        raise RuntimeError(f"Required schema table is missing: {table}")


def _create_index_if_missing(
    bind,
    name: str,
    table: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    indexes = {item["name"] for item in _inspector(bind).get_indexes(table)}
    if name not in indexes:
        op.create_index(name, table, columns, unique=unique)


def _validate_ngap_table(bind) -> None:
    inspector = _inspector(bind)
    existing = {item["name"] for item in inspector.get_columns(_NGAP_TABLE)}
    missing = _NGAP_COLUMNS - existing
    if missing:
        raise RuntimeError(
            "Critical NGAP schema mismatch: missing columns "
            + ", ".join(sorted(missing))
        )

    unique_sets = {
        tuple(item.get("column_names") or ())
        for item in inspector.get_unique_constraints(_NGAP_TABLE)
    }
    required_unique_sets = {
        ("catalog_act_id", "reference_version"),
        ("mapping_rule_id",),
    }
    missing_unique = required_unique_sets - unique_sets
    if missing_unique:
        rendered = "; ".join(",".join(columns) for columns in sorted(missing_unique))
        raise RuntimeError(
            "Critical NGAP schema mismatch: missing unique constraints " + rendered
        )

    check_names = {
        item.get("name")
        for item in inspector.get_check_constraints(_NGAP_TABLE)
        if item.get("name")
    }
    missing_checks = _NGAP_CHECKS - check_names
    if missing_checks:
        raise RuntimeError(
            "Critical NGAP schema mismatch: missing check constraints "
            + ", ".join(sorted(missing_checks))
        )


def _ensure_ngap_table(bind) -> None:
    _require_table(bind, "catalog_acts")
    _require_table(bind, "users")

    if not _inspector(bind).has_table(_NGAP_TABLE):
        op.create_table(
            _NGAP_TABLE,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("catalog_act_id", sa.Integer(), nullable=False),
            sa.Column("code_kind", sa.String(length=16), nullable=False),
            sa.Column("ngap_code", sa.String(length=32), nullable=True),
            sa.Column("coefficient", sa.Float(), nullable=True),
            sa.Column("official_label", sa.Text(), nullable=True),
            sa.Column("requires_prior_approval", sa.Boolean(), nullable=False),
            sa.Column("requires_radiograph", sa.Boolean(), nullable=False),
            sa.Column("reference_version", sa.String(length=64), nullable=False),
            sa.Column("mapping_rule_id", sa.String(length=128), nullable=False),
            sa.Column("verification_status", sa.String(length=32), nullable=False),
            sa.Column("source_authority", sa.String(length=255), nullable=False),
            sa.Column("source_url", sa.Text(), nullable=False),
            sa.Column("source_hash", sa.String(length=64), nullable=True),
            sa.Column("valid_from", sa.Date(), nullable=True),
            sa.Column("valid_to", sa.Date(), nullable=True),
            sa.Column("validated_by_practitioner_id", sa.Integer(), nullable=True),
            sa.Column("validated_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(
                "code_kind IN ('NGAP', 'INTERNAL', 'OTHER')",
                name="ck_ngap_mapping_code_kind",
            ),
            sa.CheckConstraint(
                "verification_status IN ('PRIMARY_HASH_PENDING', 'VERIFIED_PRIMARY', 'OUTDATED')",
                name="ck_ngap_mapping_verification_status",
            ),
            sa.CheckConstraint(
                "code_kind != 'NGAP' OR (ngap_code IS NOT NULL AND coefficient IS NOT NULL)",
                name="ck_ngap_mapping_ngap_payload",
            ),
            sa.CheckConstraint(
                "verification_status != 'VERIFIED_PRIMARY' OR "
                "(source_hash IS NOT NULL AND length(source_hash) = 64 "
                "AND validated_by_practitioner_id IS NOT NULL AND validated_at IS NOT NULL)",
                name="ck_ngap_mapping_verified_evidence",
            ),
            sa.ForeignKeyConstraint(
                ["catalog_act_id"],
                ["catalog_acts.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["validated_by_practitioner_id"],
                ["users.id"],
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "catalog_act_id",
                "reference_version",
                name="uq_ngap_catalog_mapping_act_version",
            ),
            sa.UniqueConstraint("mapping_rule_id"),
        )

    _validate_ngap_table(bind)
    _create_index_if_missing(bind, "ix_ngap_catalog_mappings_id", _NGAP_TABLE, ["id"])
    _create_index_if_missing(
        bind,
        "ix_ngap_catalog_mappings_catalog_act_id",
        _NGAP_TABLE,
        ["catalog_act_id"],
    )
    _create_index_if_missing(
        bind,
        "ix_ngap_catalog_mappings_ngap_code",
        _NGAP_TABLE,
        ["ngap_code"],
    )
    _create_index_if_missing(
        bind,
        "ix_ngap_catalog_mappings_reference_version",
        _NGAP_TABLE,
        ["reference_version"],
    )
    _create_index_if_missing(
        bind,
        "ix_ngap_catalog_mappings_validated_by_practitioner_id",
        _NGAP_TABLE,
        ["validated_by_practitioner_id"],
    )


def _has_catalog_act_fk(bind) -> bool:
    for item in _inspector(bind).get_foreign_keys("actes"):
        columns = item.get("constrained_columns") or []
        if (
            columns == ["catalog_act_id"]
            and item.get("referred_table") == "catalog_acts"
            and (item.get("referred_columns") or []) == ["id"]
        ):
            return True
    return False


def _ensure_insurance_linkage(bind) -> None:
    _require_table(bind, "actes")
    _require_table(bind, "catalog_acts")

    existing = {item["name"] for item in _inspector(bind).get_columns("actes")}
    if "source_line_uid" not in existing:
        op.add_column(
            "actes",
            sa.Column("source_line_uid", sa.String(length=36), nullable=True),
        )

    if "catalog_act_id" not in existing:
        if bind.dialect.name == "sqlite":
            # SQLite cannot add a foreign-key constraint separately after the
            # column exists. The inline REFERENCES form is additive and keeps
            # all existing rows unchanged.
            bind.execute(
                sa.text(
                    "ALTER TABLE actes ADD COLUMN catalog_act_id "
                    "INTEGER REFERENCES catalog_acts(id) ON DELETE SET NULL"
                )
            )
        else:
            op.add_column(
                "actes",
                sa.Column(
                    "catalog_act_id",
                    sa.Integer(),
                    sa.ForeignKey("catalog_acts.id", ondelete="SET NULL"),
                    nullable=True,
                ),
            )

    migrated = {item["name"] for item in _inspector(bind).get_columns("actes")}
    missing = {"source_line_uid", "catalog_act_id"} - migrated
    if missing:
        raise RuntimeError(
            "Critical insurance linkage schema mismatch: missing "
            + ", ".join(sorted(missing))
        )
    if not _has_catalog_act_fk(bind):
        raise RuntimeError(
            "Critical insurance linkage schema mismatch: "
            "actes.catalog_act_id foreign key is missing"
        )

    _create_index_if_missing(
        bind,
        "ix_actes_source_line_uid",
        "actes",
        ["source_line_uid"],
    )
    _create_index_if_missing(
        bind,
        "ix_actes_catalog_act_id",
        "actes",
        ["catalog_act_id"],
    )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_ngap_table(bind)
    _ensure_insurance_linkage(bind)


def downgrade() -> None:
    # Additive compatibility fields/tables may contain newer clinical or
    # regulatory linkage data. Routine downgrade must not destroy them.
    pass
