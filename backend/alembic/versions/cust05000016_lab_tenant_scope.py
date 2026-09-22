"""CUST-05 tenant-scoped laboratory catalog.

Revision ID: cust05000016
Revises: cust02000015
"""

from alembic import op
import sqlalchemy as sa

revision = "cust05000016"
down_revision = "cust02000015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "labs",
        sa.Column(
            "employer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_labs_employer_id", "labs", ["employer_id"])
    op.create_unique_constraint("uq_labs_tenant_name", "labs", ["employer_id", "name"])


def downgrade():
    op.drop_constraint("uq_labs_tenant_name", "labs", type_="unique")
    op.drop_index("ix_labs_employer_id", table_name="labs")
    op.drop_column("labs", "employer_id")
