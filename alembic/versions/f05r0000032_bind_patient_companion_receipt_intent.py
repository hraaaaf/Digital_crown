"""Bind Patient Companion replay receipts to their original clinical intent.

Revision ID: f05r0000032
Revises: neo000000031

Existing rows are preserved with a NULL digest because their historical
request payload was never stored. Runtime fails closed on attempts to replay
those unverifiable receipts; it does not invent their original request.
This is an operator-applied additive upgrade only, NEVER a startup migration.
"""
from alembic import op
import sqlalchemy as sa
import os


revision = "f05r0000032"
down_revision = "neo000000031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable: preserves all existing receipts without inventing missing
    # fingerprints. Only newly claimed receipts can safely be replayed.
    op.add_column(
        "patient_companion_remote_receipts",
        sa.Column("intent_sha256", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    # Historical migration CI rehearses multiple downgrade/upgrade cycles.
    # ONLY the named disposable PostgreSQL schema-cert database may drop the
    # column, and ONLY while zero receipt fingerprints would be destroyed.
    # Production, real cabinets, arbitrary dev DBs and SQLite fail closed.
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or os.environ.get("ENVIRONMENT") != "rehearsal":
        raise RuntimeError("F05-R1 receipt fingerprints cannot be downgraded outside isolated certification")
    database_name = bind.execute(sa.text("SELECT current_database()")).scalar_one()
    if database_name != "digitalcrown_schema_cert":
        raise RuntimeError("F05-R1 receipt downgrade restricted to disposable schema-cert database")
    existing = bind.execute(sa.text(
        "SELECT COUNT(*) FROM patient_companion_remote_receipts "
        "WHERE intent_sha256 IS NOT NULL"
    )).scalar_one()
    if existing:
        raise RuntimeError("F05-R1 receipt downgrade would destroy signed intent evidence")
    op.drop_column("patient_companion_remote_receipts", "intent_sha256")
