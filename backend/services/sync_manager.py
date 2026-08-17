import logging
import threading

logger = logging.getLogger(__name__)


class SyncManager:
    """Local-first compatibility facade.

    Patient, appointment, payment and treatment data must remain on the cabinet
    machine. Firebase is reserved for identity/licensing and must never receive
    clinical or patient snapshots from this service.

    Historical debounce/event methods are deliberately preserved because other
    runtime code and regression tests still import them. They may collect a
    cabinet identifier in memory, but every execution path terminates in a
    fail-closed no-op: no patient payload is built and no cloud write occurs.
    """

    def __init__(self, debounce_seconds: float = 2.0):
        self.debounce_seconds = debounce_seconds
        self._pending_employers: set[int] = set()
        self._timer = None
        self._lock = threading.Lock()

    def start_listening(self) -> None:
        logger.info("Local-first mode: patient/agenda/payment/act cloud sync is disabled.")

    def _on_change(self, mapper, connection, target) -> None:
        employer_id = getattr(target, "employer_id", None)
        if employer_id is None:
            employer_id = getattr(target, "praticien_id", None)
        if employer_id is not None:
            self._schedule_sync(int(employer_id))

    def _schedule_sync(self, employer_id: int) -> None:
        with self._lock:
            self._pending_employers.add(employer_id)
            if self._timer is not None:
                try:
                    self._timer.cancel()
                except Exception:
                    pass
            self._timer = threading.Timer(self.debounce_seconds, self._perform_bulk_sync)
            self._timer.daemon = True
            self._timer.start()

    def _perform_bulk_sync(self) -> None:
        with self._lock:
            pending = set(self._pending_employers)
            self._pending_employers.clear()
            self._timer = None
        if pending:
            logger.warning(
                "Ignored patient cloud sync request for cabinet(s) %s: local-first boundary enforced.",
                sorted(pending),
            )

    def _perform_sync(self, employer_id: int) -> None:
        logger.warning(
            "Patient cloud sync request ignored for cabinet %s: local-first boundary enforced.",
            employer_id,
        )

    def _sync_single_cabinet(self, db, employer_id: int) -> None:
        logger.warning(
            "Patient cloud sync request ignored for cabinet %s: local-first boundary enforced.",
            employer_id,
        )


sync_manager = SyncManager()
