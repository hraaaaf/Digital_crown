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
