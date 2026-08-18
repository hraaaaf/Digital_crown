"""Optionally link installment plans to the billed Acte they settle.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-08-18

Legacy installment plans remain valid with acte_id=NULL. Patient-page plans can
carry an explicit Acte link and be reconciled transactionally.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("installment_plans") as batch_op:
        batch_op.add_column(sa.Column("acte_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_installment_plans_acte_id_actes",
            "actes",
            ["acte_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_installment_plans_acte_id", ["acte_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("installment_plans") as batch_op:
        batch_op.drop_index("ix_installment_plans_acte_id")
        batch_op.drop_constraint("fk_installment_plans_acte_id_actes", type_="foreignkey")
        batch_op.drop_column("acte_id")
