import logging

logger = logging.getLogger(__name__)


class SyncManager:
    """Local-first compatibility facade.

    Patient, appointment, payment and treatment data must remain on the cabinet
    machine. Firebase is reserved for identity/licensing and must never receive
    clinical or patient snapshots from this service.

    The object is intentionally kept because startup/admin code imports the
    historical ``sync_manager`` symbol. All patient-cloud sync entry points are
    fail-closed no-ops until a future architecture explicitly reintroduces a
    compliant, separately reviewed transport.
    """

    def start_listening(self) -> None:
        """Keep patient-data SQLAlchemy listeners disabled by construction."""
        logger.info(
            "Local-first mode: patient/agenda/payment/act cloud sync is disabled."
        )

    def _perform_bulk_sync(self) -> None:
        """Compatibility no-op: cloud patient snapshots are forbidden."""
        logger.warning(
            "Patient cloud sync request ignored: local-first boundary enforced."
        )

    def _perform_sync(self, employer_id: int) -> None:
        """Legacy compatibility no-op used by historical revocation code."""
        logger.warning(
            "Patient cloud sync request ignored for cabinet %s: local-first boundary enforced.",
            employer_id,
        )

    def _sync_single_cabinet(self, db, employer_id: int) -> None:
        """Compatibility no-op: no patient data leaves the local database."""
        logger.warning(
            "Patient cloud sync request ignored for cabinet %s: local-first boundary enforced.",
            employer_id,
        )


sync_manager = SyncManager()
