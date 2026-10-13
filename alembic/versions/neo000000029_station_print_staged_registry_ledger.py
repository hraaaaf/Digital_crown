"""04.8 B/C staged ledger + unverified printer catalog; NEVER activates printing.

Revision ID: neo000000029
Revises: neo000000028

No patient data, queue worker, spool dispatch, print permission or seed data.
These tables are staging primitives only; an authorized business service is
required before use and physical release remains gated to V1.5-10.
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000029"
down_revision = "neo000000028"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "station_print_printer_drafts",
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("printer_id", sa.String(length=80), primary_key=True),
        sa.Column("location", sa.String(length=16), nullable=False),
        sa.Column("station_id", sa.String(length=80), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("location IN ('reception','near_station')", name="ck_print_draft_location"),
        sa.CheckConstraint("revision > 0", name="ck_print_draft_revision"),
        sa.CheckConstraint(
            "(location = 'reception' AND station_id IS NULL) OR "
            "(location = 'near_station' AND station_id IS NOT NULL)",
            name="ck_print_draft_station_binding",
        ),
    )
    op.create_table(
        "station_print_held_claims",
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("delivery_key", sa.String(length=64), primary_key=True),
        sa.Column("first_printer_id", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="held"),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('held','uncertain')", name="ck_print_claim_state"),
        sa.CheckConstraint("revision > 0", name="ck_print_claim_revision"),
    )


def downgrade():
    # Destructive; only use on an approved backed-up test DB. No silent
    # replacement to a printer destination after a job is deleted.
    op.drop_table("station_print_held_claims")
    op.drop_table("station_print_printer_drafts")
