"""Backfill legacy dossier medical history into canonical Patient field.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-17

P0-G Patient truth rule:
- patients.antecedents_medicaux is canonical;
- dossiers_cliniques.antecedents_medicaux is legacy;
- never overwrite a non-empty canonical Patient value.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BACKFILL_SQL = """
UPDATE patients
SET antecedents_medicaux = (
    SELECT dc.antecedents_medicaux
    FROM dossiers_cliniques AS dc
    WHERE dc.patient_id = patients.id
)
WHERE (antecedents_medicaux IS NULL OR TRIM(antecedents_medicaux) = '')
  AND EXISTS (
      SELECT 1
      FROM dossiers_cliniques AS dc
      WHERE dc.patient_id = patients.id
        AND dc.antecedents_medicaux IS NOT NULL
        AND TRIM(dc.antecedents_medicaux) <> ''
  )
"""


def upgrade() -> None:
    op.execute(BACKFILL_SQL)


def downgrade() -> None:
    # Intentionally no reverse copy: after upgrade, Patient is the canonical
    # runtime source. Copying values back into the legacy column would recreate
    # a second source of medical truth and could overwrite historical content.
    pass
