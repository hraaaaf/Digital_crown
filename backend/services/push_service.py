"""Compatibility facade for the legacy E5 push API.

M6-D2 routes all OS delivery through the device/user-bound standards Web Push service.
"""
import logging

from sqlalchemy.orm import Session

from backend.services.mobile_push_service import send_push_for_alert_types

logger = logging.getLogger(__name__)


def send_push_to_employer(db: Session, employer_id: int, title: str = "", body: str = "") -> int:
    """Deprecated cabinet-wide entry point kept for compatibility; content is intentionally ignored."""
    logger.warning("Legacy send_push_to_employer called; using generic device-bound Web Push payload")
    return send_push_for_alert_types(db, employer_id, ["GENERIC"])
