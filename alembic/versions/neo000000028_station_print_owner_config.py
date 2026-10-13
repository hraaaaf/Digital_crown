"""LOT04.8-B2b: inert, owner-scoped Station printing configuration tables.

Revision ID: neo000000028
Revises: neo000000027

Only schema. No seeded enabled policies, no printer registry, no routes,
no PDF delivery, no driver/print dispatch and no migration execution here.
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000028"
down_revision = "neo000000027"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "station_print_configurations",
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default="disabled"),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("mode IN ('disabled','reception','near_station','both')", name="ck_station_print_mode"),
        sa.CheckConstraint("revision > 0", name="ck_station_print_revision"),
    )
    op.create_table(
        "station_print_config_stations",
        sa.Column(
            "tenant_id", sa.Integer(),
            sa.ForeignKey("station_print_configurations.tenant_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # Cross-tenant membership is checked against the authoritative
        # WorkstationMode registry by the pure compiler and rechecked on read.
        # A physical composite tenant/workstation FK remains a B2c gate.
        sa.Column("station_id", sa.String(length=80), primary_key=True),
    )
    op.create_table(
        "station_print_config_printers",
        sa.Column(
            "tenant_id", sa.Integer(),
            sa.ForeignKey("station_print_configurations.tenant_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # No real printer registry/certification exists yet: a foreign key
        # would falsely imply material validation. Keep the runtime NO-GO.
        sa.Column("printer_id", sa.String(length=80), primary_key=True),
    )
    op.create_table(
        "station_print_config_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_station_print_config_audit_tenant_revision",
        "station_print_config_audit", ["tenant_id", "revision"],
    )


def downgrade():
    # Explicit destructive downgrade: only on backed-up synthetic/approved DB.
    # Defensive rollback for partially-upgraded/legacy installations.
    # PostgreSQL drops any remaining table-owned index with DROP TABLE; only
    # remove it explicitly when the actual catalog still lists it.
    audit_indexes = {
        entry["name"]
        for entry in sa.inspect(op.get_bind()).get_indexes("station_print_config_audit")
    }
    if "ix_station_print_config_audit_tenant_revision" in audit_indexes:
        op.drop_index("ix_station_print_config_audit_tenant_revision", table_name="station_print_config_audit")
    op.drop_table("station_print_config_audit")
    op.drop_table("station_print_config_printers")
    op.drop_table("station_print_config_stations")
    op.drop_table("station_print_configurations")
