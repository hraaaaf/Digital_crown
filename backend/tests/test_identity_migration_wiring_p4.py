"""P4E proves the existing-install startup migration path wires P4B identity columns."""
from backend import database


def test_cabinet_startup_migration_invokes_identity_extension(monkeypatch):
    calls = []

    def fake_identity_migration(engine):
        calls.append(engine)

    monkeypatch.setattr(
        "backend.models_identity_p4.migrate_identity_columns",
        fake_identity_migration,
    )

    database.migrate_cabinet_config_columns()

    assert calls == [database.engine]
