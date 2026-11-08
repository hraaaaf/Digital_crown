from sqlalchemy import create_engine, inspect

from queue_core.persistence import QueueBase
from queue_core.persistence import models  # noqa: F401 - registers isolated tables


def test_queue_schema_is_self_contained_and_creatable_in_ephemeral_sqlite():
    names = set(QueueBase.metadata.tables)
    assert names == {
        "queue_tenants", "queue_lines", "queue_resources", "queue_visits",
        "queue_visit_resources", "queue_event_log", "queue_external_references",
    }
    assert all(not name.startswith("patients") and not name.startswith("appointments") for name in names)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    QueueBase.metadata.create_all(engine)
    assert set(inspect(engine).get_table_names()) == names


def test_external_appointment_reference_cannot_point_to_two_queue_visits():
    """A duplicated upstream appointment must never create a second visit."""
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from queue_core.persistence.models import (
        QueueExternalReference, QueueLine, QueueTenant, QueueVisitRecord,
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    QueueBase.metadata.create_all(engine)
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add(QueueTenant(id="T", timezone_name="Africa/Casablanca", created_at_utc=now))
        session.add(QueueLine(id="Q", tenant_id="T", queue_key="reception", is_active=True))
        session.commit()
        for vid in ("A", "B"):
            session.add(QueueVisitRecord(
                id=vid, tenant_id="T", queue_id="Q", visit_kind="APPOINTMENT",
                status="PLANNED", scheduled_at_utc=now, version=0,
            ))
        session.commit()
        session.add(QueueExternalReference(
            id="EXT-A", tenant_id="T", visit_id="A",
            source_system="SOURCE", entity_kind="APPOINTMENT", external_id="upstream-123",
        ))
        session.commit()
        session.add(QueueExternalReference(
            id="EXT-B", tenant_id="T", visit_id="B",
            source_system="SOURCE", entity_kind="APPOINTMENT", external_id="upstream-123",
        ))
        with pytest.raises(IntegrityError):
            session.commit()


def test_external_patient_reference_is_not_part_of_08_1_contract():
    """Patient mapping can repeat across appointments; keep it deferred to LOT09."""
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from queue_core.persistence.models import (
        QueueExternalReference, QueueLine, QueueTenant, QueueVisitRecord,
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    QueueBase.metadata.create_all(engine)
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add(QueueTenant(id="T", timezone_name="Africa/Casablanca", created_at_utc=now))
        session.add(QueueLine(id="Q", tenant_id="T", queue_key="reception", is_active=True))
        session.commit()
        session.add(QueueVisitRecord(
            id="A", tenant_id="T", queue_id="Q", visit_kind="APPOINTMENT",
            status="PLANNED", scheduled_at_utc=now, version=0,
        ))
        session.commit()
        session.add(QueueExternalReference(
            id="EXT-A", tenant_id="T", visit_id="A", source_system="SOURCE",
            entity_kind="PATIENT", external_id="patient-123",
        ))
        with pytest.raises(IntegrityError):
            session.commit()


def test_sqlite_foreign_keys_reject_cross_tenant_resource_binding():
    """A Queue visit may not claim a resource owned by another tenant."""
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from queue_core.persistence.models import (
        QueueLine, QueueResource, QueueTenant, QueueVisitRecord, QueueVisitResource,
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enforce_fk(connection, connection_record):
        connection.execute("PRAGMA foreign_keys=ON")

    QueueBase.metadata.create_all(engine)
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add_all([
            QueueTenant(id="A", timezone_name="Africa/Casablanca", created_at_utc=now),
            QueueTenant(id="B", timezone_name="Africa/Casablanca", created_at_utc=now),
        ])
        session.commit()
        session.add(QueueLine(id="Q", tenant_id="A", queue_key="reception"))
        session.add(QueueResource(
            id="R", tenant_id="B", resource_key="chair",
            resource_kind="CHAIR",
        ))
        session.commit()
        session.add(QueueVisitRecord(
            id="V", tenant_id="A", queue_id="Q", visit_kind="APPOINTMENT",
            status="PLANNED", scheduled_at_utc=now,
        ))
        session.commit()
        session.add(QueueVisitResource(tenant_id="A", visit_id="V", resource_id="R"))
        with pytest.raises(IntegrityError):
            session.commit()



def _fk_enforcing_queue_db():
    """Synthetic SQLite only: exercise DB constraints with foreign keys enabled."""
    from sqlalchemy import event

    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enforce_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    QueueBase.metadata.create_all(engine)
    return engine


def test_active_chair_owner_is_persisted_unique_and_tenant_scoped():
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from queue_core.persistence.models import (
        QueueLine, QueueResource, QueueTenant, QueueVisitRecord,
    )

    engine = _fk_enforcing_queue_db()
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add(QueueTenant(id="TENANT", timezone_name="Africa/Casablanca", created_at_utc=now))
        session.flush()  # Explicit FK parent first; model has no ORM relationship ordering.
        session.add(QueueLine(id="LINE", tenant_id="TENANT", queue_key="main"))
        for rid in ("CHAIR1", "CHAIR2"):
            session.add(QueueResource(id=rid, tenant_id="TENANT", resource_key=rid, resource_kind="CHAIR"))
        session.commit()

        def record(vid, seq, chair, status="CHAIR"):
            return QueueVisitRecord(
                id=vid, tenant_id="TENANT", queue_id="LINE",
                visit_kind="APPOINTMENT", status=status,
                scheduled_at_utc=now, arrival_confirmed_at_utc=now,
                waiting_since_utc=now, queue_sequence=seq,
                held_resource_id=chair, version=3,
            )

        session.add(record("A", 1, "CHAIR1"))
        session.commit()
        session.expire_all()
        assert session.get(QueueVisitRecord, "A").held_resource_id == "CHAIR1"

        session.add(record("B", 2, "CHAIR1"))
        with pytest.raises(IntegrityError):
            session.commit()  # cannot double-book CHAIR1
        session.rollback()

        session.add(record("B", 2, "CHAIR2"))
        session.commit()
        assert session.get(QueueVisitRecord, "B").held_resource_id == "CHAIR2"

        session.add(record("C", 3, "CHAIR1", status="WAITING"))
        with pytest.raises(IntegrityError):
            session.commit()  # only CHAIR can hold a chair
        session.rollback()

        session.add(record("C", 3, None, status="CHAIR"))
        with pytest.raises(IntegrityError):
            session.commit()  # CHAIR must hold an existing resource
        session.rollback()

        session.add(record("C", 3, "NOT_IN_THIS_TENANT"))
        with pytest.raises(IntegrityError):
            session.commit()  # composite tenant FK rejects phantom resource
        session.rollback()


def test_arrival_provenance_is_persisted_and_constrained_in_event_ledger():
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from queue_core.persistence.models import QueueEventRecord, QueueTenant

    engine = _fk_enforcing_queue_db()
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add(QueueTenant(id="TENANT", timezone_name="Africa/Casablanca", created_at_utc=now))
        session.commit()

        def audit(event_id, version, event_type, method):
            return QueueEventRecord(
                id=event_id, tenant_id="TENANT", visit_ref="OPAQUE_VISIT",
                aggregate_version=version, event_type=event_type,
                state_before="PLANNED", state_after="WAITING" if version > 1 else "PLANNED",
                occurred_at_utc=now, actor_kind="DEVICE", actor_ref="PAIRED_KIOSK",
                method=method,
            )

        session.add(audit("E1", 1, "ARRIVED", "KIOSK_QR"))
        session.commit()
        session.expire_all()
        assert session.get(QueueEventRecord, "E1").method == "KIOSK_QR"

        session.add(audit("E2", 2, "WAITING_ENTERED", None))
        with pytest.raises(IntegrityError):
            session.commit()  # every check-in event retains its method
        session.rollback()

        session.add(audit("E2", 2, "WAITING_ENTERED", "KIOSK_QR"))
        session.commit()

        session.add(audit("E3", 3, "CALLED", "STAFF"))
        with pytest.raises(IntegrityError):
            session.commit()  # unrelated events cannot spoof check-in method
        session.rollback()

        session.add(audit("E3", 3, "CALLED", None))
        session.commit()



def test_resource_audit_reference_persists_and_cannot_attach_to_other_event_types():
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session
    from queue_core.persistence.models import QueueEventRecord, QueueTenant

    engine = _fk_enforcing_queue_db()
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add(QueueTenant(id="T", timezone_name="Africa/Casablanca", created_at_utc=now))
        session.commit()

        def record(event_id, v, event_type, resource_id):
            return QueueEventRecord(
                id=event_id, tenant_id="T", visit_ref="VISIT_OPAQUE",
                aggregate_version=v, event_type=event_type,
                state_before="CHAIR", state_after="CHAIR",
                occurred_at_utc=now, actor_kind="HUMAN", actor_ref="STAFF",
                resource_id=resource_id,
            )

        session.add(record("E1", 1, "RESOURCE_RELEASED", "chair-1"))
        session.commit()
        assert session.get(QueueEventRecord, "E1").resource_id == "chair-1"

        session.add(record("E2", 2, "RESOURCE_CLAIMED", None))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(record("E2", 2, "CALLED", "chair-1"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(record("E2", 2, "RESOURCE_CLAIMED", "chair-2"))
        session.commit()



def test_event_sql_constraints_reject_unknown_enums_and_invalid_manual_facts():
    from datetime import datetime, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session
    from queue_core.persistence.models import QueueEventRecord, QueueTenant

    engine = _fk_enforcing_queue_db()
    now = datetime(2026, 11, 8, 9, tzinfo=timezone.utc)
    with Session(engine) as session:
        session.add(QueueTenant(id="T", timezone_name="Africa/Casablanca", created_at_utc=now))
        session.commit()

        cases = [
            dict(event_type="UNRECOGNIZED"),
            dict(state_before="INVALID"),
            dict(state_after="INVALID"),
            dict(event_type="NO_SHOW", reason_code=None),
            dict(event_type="NO_SHOW", actor_kind="DEVICE", reason_code="ABSENT"),
            dict(event_type="ARRIVED", method="STAFF", actor_kind="DEVICE"),
            dict(event_type="WAITING_ENTERED", method="KIOSK_QR", actor_kind="HUMAN"),
            dict(event_type="CANCELLED", reason_code="  "),
        ]
        defaults = dict(
            tenant_id="T", visit_ref="V", event_type="CALLED",
            state_before="WAITING", state_after="CALLED",
            occurred_at_utc=now, actor_kind="HUMAN", actor_ref="STAFF",
            method=None, reason_code=None, resource_id=None,
        )
        for i, override in enumerate(cases, 1):
            session.add(QueueEventRecord(
                id=f"BAD{i}", aggregate_version=i, **{**defaults, **override}
            ))
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

        session.add(QueueEventRecord(
            id="GOOD1", aggregate_version=20,
            **{**defaults, "event_type": "NO_SHOW", "reason_code": "ABSENT"},
        ))
        session.commit()
        session.add(QueueEventRecord(
            id="GOOD2", aggregate_version=21,
            **{**defaults, "event_type": "ARRIVED", "actor_kind": "DEVICE",
               "method": "KIOSK_QR", "state_before": "PLANNED", "state_after": "PLANNED"},
        ))
        session.commit()
