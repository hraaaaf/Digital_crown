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
