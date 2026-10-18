"""Shared durable Patient Companion Agenda quota for HTTP and Relay.

Revision ID: f05q0000033
Revises: f05r0000032

Additive only, explicit operator migration; never write data on application
startup. Separate tiny quota transactions mean failed clinical operations
cannot reset the anti-abuse budget.
"""
import os

from alembic import op
import sqlalchemy as sa


revision = "f05q0000033"
down_revision = "f05r0000032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_companion_remote_agenda_quotas",
        sa.Column(
            "access_id", sa.Integer(),
            sa.ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
            primary_key=True, nullable=False,
        ),
        sa.Column("window_started_epoch", sa.BigInteger(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.CheckConstraint("attempts >= 1", name="ck_pc_remote_agenda_quota_positive"),
    )


def downgrade() -> None:
    # Removing this table from a real cabinet would disable the distributed
    # abuse barrier. Permit only the named disposable PostgreSQL schema-cert
    # database for historical reversible-migration tests.
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or os.environ.get("ENVIRONMENT") != "rehearsal":
        raise RuntimeError("shared patient Agenda quota downgrade denied outside synthetic PG rehearsal")
    if bind.execute(sa.text("SELECT current_database()")).scalar_one() != "digitalcrown_schema_cert":
        raise RuntimeError("shared patient Agenda quota downgrade restricted to disposable schema-cert database")
    op.drop_table("patient_companion_remote_agenda_quotas")
