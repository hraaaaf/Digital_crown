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
    # Removing fingerprints would make already-certified idempotent receipts
    # unverifiable. Never silently destroy this clinical-safety provenance.
    raise RuntimeError(
        "F05-R1 receipt fingerprints cannot be discarded by an automatic downgrade"
    )
