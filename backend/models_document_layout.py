"""Additive document-layout fields kept isolated from the legacy model monolith.

Digital Crown still exposes ``CabinetConfig`` from ``backend.models``.  This module
extends that declarative model with new additive document-layout columns without
forcing unrelated legacy models to move or be rewritten.
"""

from sqlalchemy import Float
from sqlalchemy.orm import mapped_column


def attach_document_layout_columns() -> None:
    """Attach additive layout columns to CabinetConfig exactly once."""
    from backend.models import CabinetConfig

    if "content_offset_y" not in CabinetConfig.__table__.c:
        CabinetConfig.content_offset_y = mapped_column(
            Float,
            default=0.0,
            nullable=False,
        )
