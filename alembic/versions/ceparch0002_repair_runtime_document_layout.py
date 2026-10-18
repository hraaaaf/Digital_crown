"""Repair runtime document-layout schema drift before PostgreSQL JWT archive T2.

Revision ID: ceparch0002
Revises: ceparch0001

A fresh PostgreSQL baseline already receives the full model column once the
Alembic snapshot attaches it. Databases previously stamped at ceparch0001 may
still be missing this one nonclinical field. Add it without touching any rows
or values. This is a pure schema migration; no auto-migration at app startup.
"""

from alembic import op
import sqlalchemy as sa

revision = "ceparch0002"
down_revision = "ceparch0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("cabinet_configs"):
        raise RuntimeError("Required cabinet_configs table missing; refusing partial repair")
    columns = {column["name"]: column for column in inspector.get_columns("cabinet_configs")}
    if "content_offset_y" not in columns:
        op.add_column(
            "cabinet_configs",
            sa.Column(
                "content_offset_y",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0.0"),
            ),
        )
    else:
        existing = columns["content_offset_y"]
        # Do not overwrite data or silently accept an incompatible column.
        if not isinstance(existing["type"], (sa.Float, sa.REAL, sa.Numeric)):
            raise RuntimeError("content_offset_y has an incompatible SQL type")
        if existing.get("nullable") is False and existing.get("default") is None:
            # Legacy non-null Float is already a valid runtime representation;
            # no default rewrite is necessary.
            return
        # Any existing numeric column is intentionally preserved as-is:
        # its values may reflect user layout adjustments.


def downgrade() -> None:
    # Removing this column would destroy per-cabinet layout calibration.
    raise RuntimeError("Explicit backup-and-restore required for layout schema downgrade")
