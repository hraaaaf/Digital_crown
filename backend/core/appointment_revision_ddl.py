"""DB-owned, monotonically increasing revision for every clinical appointment edit.

Crucially this covers ORM writes *and* raw SQL/bulk UPDATEs. No workstation,
API process, or mobile client is trusted to bump its own revision.
"""
from sqlalchemy import text


def install_appointment_revision_guard(connection):
    dialect = connection.dialect.name
    if dialect == "postgresql":
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION dc_bump_appointment_revision()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.clinical_revision := OLD.clinical_revision + 1;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))
        connection.execute(text(
            "DROP TRIGGER IF EXISTS dc_appointment_revision_update ON appointments"
        ))
        connection.execute(text("""
            CREATE TRIGGER dc_appointment_revision_update
            BEFORE UPDATE ON appointments
            FOR EACH ROW EXECUTE FUNCTION dc_bump_appointment_revision()
        """))
    elif dialect == "sqlite":
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS dc_appointment_revision_update
            AFTER UPDATE ON appointments
            FOR EACH ROW
            WHEN NEW.clinical_revision = OLD.clinical_revision
            BEGIN
                UPDATE appointments
                   SET clinical_revision = OLD.clinical_revision + 1
                 WHERE id = NEW.id;
            END
        """))
    else:
        raise RuntimeError("Unsupported clinical revision database dialect")


def remove_appointment_revision_guard(connection):
    dialect = connection.dialect.name
    if dialect == "postgresql":
        connection.execute(text(
            "DROP TRIGGER IF EXISTS dc_appointment_revision_update ON appointments"
        ))
        connection.execute(text(
            "DROP FUNCTION IF EXISTS dc_bump_appointment_revision()"
        ))
    elif dialect == "sqlite":
        connection.execute(text(
            "DROP TRIGGER IF EXISTS dc_appointment_revision_update"
        ))
    else:
        raise RuntimeError("Unsupported clinical revision database dialect")


def install_appointment_overlap_index(connection):
    """Index the exact end-of-booking expression without a 4-hour lookback."""
    if connection.dialect.name == "postgresql":
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_appointments_tenant_clinical_end
              ON appointments (
                employer_id,
                (datetime_start + duration_minutes * INTERVAL '1 minute')
              )
        """))
    elif connection.dialect.name == "sqlite":
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_appointments_tenant_clinical_end
              ON appointments (
                employer_id,
                (julianday(datetime_start) + duration_minutes / 1440.0)
              )
        """))
    else:
        raise RuntimeError("Unsupported booking index database dialect")


def remove_appointment_overlap_index(connection):
    connection.execute(text(
        "DROP INDEX IF EXISTS ix_appointments_tenant_clinical_end"
    ))
