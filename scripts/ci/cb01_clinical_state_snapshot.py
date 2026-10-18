"""CB-01 synthetic-only SQLite full-table before/after read-only fingerprint.

Never opens a real cabinet DB. Emits only table names/counts/digests, no values.
Does not prove absence of transient writes later reverted; final state only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

DB = Path("t2-runtime-cert.db").resolve()
BEFORE = Path("/tmp/cb01-full-state-before.json")
AFTER = Path("artifacts/cb01-associate-sidecar/full-state-diff.json")


def fingerprint(db_path: Path) -> dict:
    uri = f"{db_path.as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as db:
        tables = db.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        if not tables or not {'patients', 'appointments'}.issubset({t[0] for t in tables}):
            raise RuntimeError("missing mandatory clinical SQLite tables")
        result = {}
        for name, ddl in tables:
            quoted = '"' + name.replace('"', '""') + '"'
            h = hashlib.sha256()
            h.update((ddl or "").encode("utf-8"))
            count = 0
            for row in db.execute(f"SELECT * FROM {quoted}"):
                h.update((repr(tuple(row)) + "\n").encode("utf-8"))
                count += 1
            result[name] = {"rows": count, "sha256": h.hexdigest()}
        return result


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"before", "after"}:
        raise SystemExit("usage: cb01_clinical_state_snapshot.py before|after")
    expected = os.environ.get("CB01_SOURCE_HEAD", "")
    if (os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1"
        or os.environ.get("DATABASE_URL") != "sqlite:///./t2-runtime-cert.db"
        or len(expected) != 40
        or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != expected
        or not DB.is_file()):
        raise SystemExit("REFUSED: not an exact-head isolated synthetic GitHub SQLite runtime")
    current = {"sourceHead": expected, "kind": "CB01_FULL_SQLITE_FINAL_STATE_SNAPSHOT",
               "allUserTablesIncluded": True, "tables": fingerprint(DB)}
    if sys.argv[1] == "before":
        BEFORE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print("CB01_FULL_STATE_BEFORE: RECORDED", len(current["tables"]), "tables")
        return
    if not BEFORE.is_file():
        raise SystemExit("FAIL: missing exact-head baseline")
    original = json.loads(BEFORE.read_text(encoding="utf-8"))
    if original.get("sourceHead") != expected or not original.get("allUserTablesIncluded"):
        raise SystemExit("FAIL: baseline source mismatch")
    changed = sorted(set(original["tables"]) ^ set(current["tables"]))
    changed += sorted(name for name in set(original["tables"]) & set(current["tables"])
                      if original["tables"][name] != current["tables"][name])
    proof = {"sourceHead": expected, "kind": "CB01_FULL_SQLITE_FINAL_STATE_DIFF",
             "allUserTablesIncluded": True, "tablesChecked": len(current["tables"]),
             "changedTables": changed, "status": "PASS_NO_FINAL_STATE_CHANGE" if not changed else "FAIL_TABLE_STATE_CHANGED",
             "limitation": "Final SQLite state only; technical transient writes and separate PostgreSQL/SQLCipher test DBs are not covered"}
    AFTER.parent.mkdir(parents=True, exist_ok=True)
    AFTER.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    if changed:
        raise SystemExit("FAIL: CB-01 full SQLite table state changed: " + ", ".join(changed))
    print("CB01_FULL_STATE_DIFF: PASS", len(current["tables"]), "tables, zero changed")


if __name__ == "__main__":
    main()
