"""Durable Agenda-command budget shared by FastAPI and opaque Relay.

A signed Agenda command spends one attempt regardless of domain outcome,
replayed idempotency key or subsequent clinical-transaction rollback.
Unlike the legacy in-process IP guard, this per-access budget is enforced in
a separate short PostgreSQL/SQLite transaction for every worker.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

AGENDA_QUOTA_ATTEMPTS = 5
AGENDA_QUOTA_WINDOW_SECONDS = 600


class RemoteAgendaQuotaExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = max(1, int(retry_after))
        super().__init__("Patient Companion Agenda rate budget exceeded")


class RemoteAgendaQuotaUnavailable(Exception):
    pass


_QUOTA_SQL = text("""
INSERT INTO patient_companion_remote_agenda_quotas
    (access_id, window_started_epoch, attempts)
VALUES (:access_id, :now_epoch, 1)
ON CONFLICT(access_id) DO UPDATE SET
    window_started_epoch =
        CASE WHEN :now_epoch >= patient_companion_remote_agenda_quotas.window_started_epoch + :window
        THEN :now_epoch ELSE patient_companion_remote_agenda_quotas.window_started_epoch END,
    attempts =
        CASE WHEN :now_epoch >= patient_companion_remote_agenda_quotas.window_started_epoch + :window
        THEN 1 ELSE patient_companion_remote_agenda_quotas.attempts + 1 END
WHERE
    :now_epoch >= patient_companion_remote_agenda_quotas.window_started_epoch + :window
    OR patient_companion_remote_agenda_quotas.attempts < :maximum
RETURNING attempts, window_started_epoch
""")


def charge_remote_agenda_attempt(
    db: Session, *, access_id: int,
    maximum: int = AGENDA_QUOTA_ATTEMPTS,
    window_seconds: int = AGENDA_QUOTA_WINDOW_SECONDS,
) -> int:
    """Spend a committed attempt or fail closed, never weaken on DB errors.

    Both PostgreSQL and SQLite support atomic INSERT ON CONFLICT ... RETURNING.
    A second independent transaction ensures even clinical rollbacks count
    toward abuse protection. PostgreSQL derives time from its database clock,
    never from process-local time that could differ between workers.
    """
    if int(access_id) <= 0 or not 1 <= maximum <= 10000 or window_seconds <= 0:
        raise RemoteAgendaQuotaUnavailable("invalid agenda quota configuration")
    bind = db.get_bind()
    if bind.dialect.name not in {"postgresql", "sqlite"}:
        raise RemoteAgendaQuotaUnavailable("unsupported agenda quota database")

    # A SQLite in-memory test connection cannot safely use another concurrent
    # Session on the same StaticPool connection. Only such disposable SQLite
    # test databases use the caller transaction; persisted cabinet SQLite and
    # PostgreSQL use the independent, durable quota transaction below.
    database_name = str(getattr(bind.url, "database", "") or "")
    is_memory_test = bind.dialect.name == "sqlite" and (
        database_name == ":memory:" or database_name.startswith("file::memory:")
    )
    try:
        if is_memory_test:
            now_epoch = int(db.scalar(text("SELECT CAST(strftime('%s', 'now') AS INTEGER)")))
            row = db.execute(_QUOTA_SQL, dict(
                access_id=int(access_id), now_epoch=now_epoch,
                window=window_seconds, maximum=maximum,
            )).first()
            if row is None:
                started = db.scalar(text(
                    "SELECT window_started_epoch FROM patient_companion_remote_agenda_quotas WHERE access_id=:id"
                ), {"id": int(access_id)})
                raise RemoteAgendaQuotaExceeded(int(started) + window_seconds - now_epoch)
            return int(row.attempts)

        with Session(bind=bind) as counter:
            with counter.begin():
                now_epoch = int(counter.scalar(
                    text("SELECT CAST(EXTRACT(EPOCH FROM clock_timestamp()) AS BIGINT)")
                    if bind.dialect.name == "postgresql" else
                    text("SELECT CAST(strftime('%s', 'now') AS INTEGER)")
                ))
                row = counter.execute(_QUOTA_SQL, {
                    "access_id": int(access_id), "now_epoch": now_epoch,
                    "window": int(window_seconds), "maximum": int(maximum),
                }).first()
                if row is None:
                    start = int(counter.scalar(text(
                        "SELECT window_started_epoch FROM patient_companion_remote_agenda_quotas "
                        "WHERE access_id=:id"
                    ), {"id": int(access_id)}))
                    raise RemoteAgendaQuotaExceeded(start + window_seconds - now_epoch)
                return int(row.attempts)
    except RemoteAgendaQuotaExceeded:
        raise
    except (SQLAlchemyError, TypeError, ValueError, AttributeError) as exc:
        # Missing migrations/locked DB/driver errors must NEVER disable safety.
        raise RemoteAgendaQuotaUnavailable("agenda quota cannot be enforced") from exc
