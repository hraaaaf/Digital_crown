"""04.8 evidence intake and uncertain-job review: no certification/dispatch.

Revision ID: neo000000030
Revises: neo000000029
Only immutable-by-API, deny-only references and investigation log are stored.
NO actual printer attestation is accepted/created. Hardware acceptance LOT10.
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000030"
down_revision = "neo000000029"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "station_print_device_evidence",
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("printer_id", sa.String(80), primary_key=True),
        sa.Column("evidence_sha256", sa.String(64), primary_key=True),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_field_verification"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "printer_id"],
            ["station_print_printer_drafts.tenant_id", "station_print_printer_drafts.printer_id"],
            ondelete="RESTRICT", name="fk_device_evidence_unverified_draft",
        ),
        sa.CheckConstraint(
            "status = 'pending_field_verification'",
            name="ck_device_evidence_never_certified",
        ),
    )
    op.create_table(
        "station_print_uncertain_reviews",
        sa.Column("review_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("delivery_key", sa.String(64), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=False),
        sa.Column("finding", sa.String(24), nullable=False),
        sa.Column("evidence_sha256", sa.String(64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "delivery_key"],
            ["station_print_held_claims.tenant_id", "station_print_held_claims.delivery_key"],
            ondelete="RESTRICT", name="fk_uncertain_review_claim",
        ),
        sa.UniqueConstraint("tenant_id", "delivery_key", "finding", name="uq_uncertain_review_one_finding"),
        sa.CheckConstraint(
            "finding IN ('investigating','evidence_checked','escalated')",
            name="ck_uncertain_review_finding",
        ),
    )


def downgrade():
    # LAB/approved test DB ONLY, after explicit backup. Review history is not
    # silently deleted on any operational Cabinet migration.
    op.drop_table("station_print_uncertain_reviews")
    op.drop_table("station_print_device_evidence")
