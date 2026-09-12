from sqlalchemy import create_engine, inspect, text

from backend import database
from backend import seed_user


def _legacy_appointment_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email VARCHAR(255) NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER,
                datetime_start DATETIME NOT NULL,
                duration_minutes INTEGER NOT NULL,
                employer_id INTEGER NOT NULL
            )
        """))
        conn.execute(text(
            "INSERT INTO appointments "
            "(id, patient_id, datetime_start, duration_minutes, employer_id) "
            "VALUES (42, 7, '2026-09-01 09:00:00', 30, 1)"
        ))
    return engine


def test_runtime_migration_adds_practitioner_without_rewriting_legacy_appointment(tmp_path):
    engine = _legacy_appointment_engine(tmp_path)

    database.migrate_appointment_columns(bind=engine)
    database.migrate_appointment_columns(bind=engine)  # idempotence

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("appointments")}
    indexes = {index["name"] for index in inspector.get_indexes("appointments")}

    assert "praticien_id" in columns
    assert columns["praticien_id"]["nullable"] is True
    assert "ix_appointments_praticien_id" in indexes

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT id, patient_id, employer_id, duration_minutes, praticien_id
            FROM appointments WHERE id = 42
        """)).mappings().one()

    assert dict(row) == {
        "id": 42,
        "patient_id": 7,
        "employer_id": 1,
        "duration_minutes": 30,
        "praticien_id": None,
    }


def test_payment_status_enum_migration_is_noop_outside_postgresql(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'enum-noop.db'}")
    database.migrate_payment_status_enum(bind=engine)


class _FakeMappingsResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FakeIdentifierPreparer:
    @staticmethod
    def quote(value):
        return f'"{value}"'


class _FakePostgresDialect:
    name = "postgresql"
    identifier_preparer = _FakeIdentifierPreparer()


class _FakePostgresConnection:
    def __init__(self):
        self.statements = []
        self._execute_count = 0

    def execution_options(self, **_kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append((sql, params))
        self._execute_count += 1
        if self._execute_count == 1:
            return _FakeMappingsResult({
                "schema_name": "public",
                "type_name": "paiementstatut",
            })
        if self._execute_count == 2:
            return _FakeScalarResult(False)
        return _FakeScalarResult(None)


class _FakePostgresEngine:
    dialect = _FakePostgresDialect()

    def __init__(self):
        self.connection = _FakePostgresConnection()

    def connect(self):
        return self.connection


def test_payment_status_enum_migration_adds_missing_value_on_postgresql():
    engine = _FakePostgresEngine()

    database.migrate_payment_status_enum(bind=engine)

    alter_statements = [sql for sql, _params in engine.connection.statements if "ALTER TYPE" in sql]
    assert alter_statements == [
        'ALTER TYPE "public"."paiementstatut" ADD VALUE IF NOT EXISTS \'A_ENCAISSER\''
    ]


def test_automatic_admin_seed_is_forbidden_in_cabinet_and_production():
    assert seed_user.automatic_admin_seed_allowed("cabinet") is False
    assert seed_user.automatic_admin_seed_allowed("production") is False
    assert seed_user.automatic_admin_seed_allowed("development") is True
    assert seed_user.automatic_admin_seed_allowed("test") is True


def test_cabinet_admin_seed_returns_before_database_access(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "cabinet")

    def _must_not_open_database():
        raise AssertionError("SessionLocal must not be opened by automatic seed in cabinet")

    monkeypatch.setattr(seed_user, "SessionLocal", _must_not_open_database)
    seed_user.seed_admin_user()
