"""LOT04.8-B2c lab proof: empty-schema baseline must contain print tables.

Mirrors Alembic env.py's metadata transfer, without importing the application
backend or connecting to a real Cabinet database.
"""
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, inspect, select

from backend.services.station_document_print_store import schema as isolated_schema

PRINT_TABLES = (
    "station_print_configurations", "station_print_config_stations",
    "station_print_config_printers", "station_print_config_audit",
)


def test_metadata_clone_includes_all_print_tables_and_audit_index():
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    for table_name in PRINT_TABLES:
        isolated_schema.tables[table_name].to_metadata(metadata)

    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {"users", *PRINT_TABLES}
    indexes = {row["name"] for row in inspector.get_indexes("station_print_config_audit")}
    assert "ix_station_print_config_audit_tenant_revision" in indexes
    for table_name in ("station_print_configurations", "station_print_config_audit"):
        foreign_keys = inspector.get_foreign_keys(table_name)
        assert any(
            item["referred_table"] == "users"
            and item["constrained_columns"] == ["tenant_id"]
            for item in foreign_keys
        ), foreign_keys
    with engine.connect() as conn:
        assert conn.execute(select(metadata.tables["station_print_configurations"])).all() == []
    engine.dispose()


def test_print_schema_does_not_modify_global_application_metadata():
    # This module is defined outside Base.metadata for isolated unit tests.
    # Alembic env.py must explicitly clone only the four print tables.
    assert set(isolated_schema.tables) == {"users", *PRINT_TABLES}
    assert isolated_schema.tables["station_print_configurations"].c.mode.server_default.arg == "disabled"
