"""Additive document-layout fields kept isolated from the legacy model monolith.

Digital Crown still exposes ``CabinetConfig`` from ``backend.models``. This module
extends that already-declared SQLAlchemy model with additive columns without
rewriting the large legacy model file.
"""

from sqlalchemy import Column, Float


def attach_document_layout_columns() -> None:
    """Attach additive layout columns to CabinetConfig exactly once."""
    from backend.models import CabinetConfig

    if "content_offset_y" not in CabinetConfig.__table__.c:
        # For an already-mapped declarative class SQLAlchemy supports assigning a
        # real Column post-declaration. ``mapped_column`` is intended primarily
        # for the declarative class body and is not used for this runtime extension.
        CabinetConfig.content_offset_y = Column(
            "content_offset_y",
            Float,
            default=0.0,
            nullable=False,
        )
