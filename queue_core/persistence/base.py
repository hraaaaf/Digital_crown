"""Independent SQLAlchemy metadata for the standalone Queue Core schema."""

from sqlalchemy.orm import DeclarativeBase


class QueueBase(DeclarativeBase):
    """Separate metadata boundary; runtime engine setup is outside 08.1."""
