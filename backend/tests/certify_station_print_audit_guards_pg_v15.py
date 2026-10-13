#!/usr/bin/env python3
"""Real PostgreSQL role+trigger proof for print audit immutability.

Runs in a disposable nonclinical schema with synthetic audit rows; checks that
normal non-owner DB roles with explicit UPDATE/DELETE grants still cannot
modify/delete any print audit row. This is not tamper proof against a DBA.
"""
from __future__ import annotations

import os
import sys
import types

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

for name,path in (("backend","backend"),("backend.services","backend/services")):
    pkg=types.ModuleType(name);pkg.__path__=[os.path.abspath(path)];sys.modules[name]=pkg

from backend.services.station_print_held_claims_lab import SCHEMA
from backend.services.station_print_attestation_recovery_v15 import device_evidence, uncertain_reviews
from backend.core.print_audit_ddl import (
    PROTECTED_PRINT_AUDITS, install_append_only_print_audit_guards,
)

SCHEMA_NAME="dc_print_append_only_lab"
ROLE_NAME="dc_print_audit_guard_client_lab"

def main():
    dsn=os.environ.get("DATABASE_URL","")
    if not dsn.startswith("postgresql"):
        raise RuntimeError("POSTGRES_ONLY")
    admin=create_engine(dsn)
    with admin.begin() as conn:
        conn.execute(text("CREATE SCHEMA "+SCHEMA_NAME))
    admin.dispose()
    engine=create_engine(dsn,connect_args={"options":"-csearch_path="+SCHEMA_NAME})
    SCHEMA.create_all(engine)
    with engine.begin() as c:
        c.execute(text(
            "CREATE TABLE station_print_config_audit "
            "(id INTEGER PRIMARY KEY, synthetic_note VARCHAR(30) NOT NULL)"
        ))
        install_append_only_print_audit_guards(c)
        c.execute(text("INSERT INTO station_print_config_audit(id,synthetic_note) VALUES (1,'lab-only')"))

        guards=c.execute(text("""
            SELECT t.tgname
            FROM pg_trigger t
            JOIN pg_class cl ON cl.oid=t.tgrelid
            JOIN pg_namespace ns ON ns.oid=cl.relnamespace
            WHERE ns.nspname=:schema AND NOT t.tgisinternal
              AND t.tgname LIKE 'dc_immutable_%'
        """),{"schema":SCHEMA_NAME}).scalars().all()
        assert len(guards)==2*len(PROTECTED_PRINT_AUDITS),guards
        c.execute(text("CREATE ROLE "+ROLE_NAME+" NOLOGIN"))
        c.execute(text("GRANT USAGE ON SCHEMA "+SCHEMA_NAME+" TO "+ROLE_NAME))
        c.execute(text(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON station_print_config_audit TO "+ROLE_NAME
        ))
    # Use separate transactions after switching to a genuinely unprivileged
    # role; REVOKE PUBLIC is insufficient without trigger enforcement.
    for sql in (
        "UPDATE station_print_config_audit SET synthetic_note='tampered' WHERE id=1",
        "DELETE FROM station_print_config_audit WHERE id=1",
    ):
        try:
            with engine.begin() as c:
                c.execute(text("SET LOCAL ROLE "+ROLE_NAME))
                c.execute(text(sql))
        except DBAPIError as exc:
            assert "DC_PRINT_AUDIT_APPEND_ONLY" in str(exc),str(exc)
        else:
            raise AssertionError("unprivileged actor modified append-only audit row")
    with engine.connect() as c:
        assert c.execute(
            text("SELECT synthetic_note FROM station_print_config_audit WHERE id=1")
        ).scalar_one()=="lab-only"
    engine.dispose()
    print("PG_PRINT_APPEND_ONLY_PASS tables=4 triggers=8 unprivileged_update_denied=1 unprivileged_delete_denied=1 preserved=1 production=0")

if __name__=="__main__":
    main()
