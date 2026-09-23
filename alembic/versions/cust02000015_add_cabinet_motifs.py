"""CUST-02 cabinet consultation motifs.

Revision ID: cust02000015
Revises: pc080000015
"""

from alembic import op
import sqlalchemy as sa

revision = "cust02000015"
down_revision = "pc080000015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cabinet_motifs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.String(length=64), nullable=False, server_default="CABINET"),
        sa.Column("urgency", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("employer_id", "public_id", name="uq_cabinet_motif_tenant_public_id"),
    )
    op.create_index("ix_cabinet_motifs_public_id", "cabinet_motifs", ["public_id"])
    op.create_index("ix_cabinet_motifs_employer_id", "cabinet_motifs", ["employer_id"])
    op.create_index("ix_cabinet_motif_tenant_active", "cabinet_motifs", ["employer_id", "is_active"])


def downgrade():
    op.drop_table("cabinet_motifs")
