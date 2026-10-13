#!/usr/bin/env python3
"""SQLite real UPDATE/DELETE audit guard proof, no production DB."""
from __future__ import annotations
import os, sys, types
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

for name, path in (("backend","backend"),("backend.services","backend/services")):
    mod=types.ModuleType(name);mod.__path__=[os.path.abspath(path)];sys.modules[name]=mod

from backend.services.station_print_held_claims_lab import SCHEMA
from backend.services.station_print_attestation_recovery_v15 import device_evidence
from backend.core.print_audit_ddl import PROTECTED_PRINT_AUDITS,install_append_only_print_audit_guards

def main():
    eng=create_engine("sqlite+pysqlite:///:memory:")
    SCHEMA.create_all(eng)
    with eng.begin() as c:
        c.execute(text("CREATE TABLE station_print_config_audit (id INTEGER PRIMARY KEY, synthetic_note VARCHAR(30))"))
        install_append_only_print_audit_guards(c)
        install_append_only_print_audit_guards(c)  # install is idempotent on baseline
        c.execute(text("INSERT INTO station_print_config_audit(id,synthetic_note) VALUES (1,'lab-only')"))
        names=c.execute(text("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'dc_immutable_%'")).scalars().all()
        assert len(names)==2*len(PROTECTED_PRINT_AUDITS),names
    for sql in (
        "UPDATE station_print_config_audit SET synthetic_note='changed' WHERE id=1",
        "DELETE FROM station_print_config_audit WHERE id=1",
    ):
        try:
            with eng.begin() as c:c.execute(text(sql))
        except DBAPIError as exc:
            assert "DC_PRINT_AUDIT_APPEND_ONLY" in str(exc),str(exc)
        else:
            raise AssertionError("SQLITE_AUDIT_TAMPER_SUCCEEDED")
    with eng.connect() as c:
        assert c.execute(text("SELECT synthetic_note FROM station_print_config_audit")).scalar_one()=="lab-only"
    print("SQLITE_PRINT_APPEND_ONLY_PASS tables=4 triggers=8 update_denied=1 delete_denied=1 preserved=1")
    eng.dispose()

if __name__=="__main__":main()
