# Digital Crown — LOT05 / Étape 2A — Offline source inventory, LAB only

Status: LAB CANDIDATE / FUE-0 + exact-HEAD CI required. No clinical import or real-vendor compatibility has been certified.

## GOAL / SCOPE

LOT05 step 1 is CLOSED: PR #1251 merged as d4d2d144393fc884e01ca8734c1efa9fb0e0f2e3; premerge Windows FUE-G run #42696964089; postmerge PowerShell/PostgreSQL run #42699723268.

This Step 2A adds a small operator command-line entrypoint to the existing 05.7C-A schema-only vendor-neutral inspector. No parser duplication, clinical API, frontend, database connection, target import, installer, or signed release change.

Supported *inspection candidates* (format only; never vendor-certified):

| Declared dialect | Export file | Inspected | Refused |
| --- | --- | --- | --- |
| SQLite | .db / .sqlite / .sqlite3 | cold offline copy; table and column counts | WAL sidecars and data-row parsing |
| PostgreSQL / MySQL / MariaDB / SQLite | .sql | bounded CREATE TABLE DDL | INSERT, COPY or SQL execution |
| Unknown or proprietary formats | Other | None | Unverified adapters/native dump |

Existing Open Dental 05.7C-F/G synthetic CSV tests do not establish actual vendor output compatibility, native demo provenance, or patient migration approval.

## LAB command

Use a disposable directory with generated FAKE fixtures only. Example for a fabricated SQLite copy (Windows PowerShell):

    py -3.12 -B backend/services/legacy_sql_vendor_inventory_v15.py --source C:\LAB_FAKE\staging\FAKE_patients.sqlite --staging-root C:\LAB_FAKE\staging --source-software FAKE_VENDOR --source-version FAKE_0 --dialect sqlite --export-format sqlite-copy --lab-synthetic-fixture --attest-offline-copy

The switches are operator attestations, NOT independently verified provenance. Never point this lab CLI at a live clinic database, an original vendor file, actual patient records or a network share. It returns only source SHA-256, size, dialect declaration, table/column aggregate counts and fixed warning/status fields. No patient values, schema names, paths, or vendor label appear in JSON. Failure returns a stable refusal code with exit status 2.

Every public report retains vendor_adapter_implemented=false, source_vendor_verified=false, human_mapping_approved=false, target_rows_written=0 and import_permitted=false.

## SUCCESS / PROOF

Required: the existing 22 FUE-0 inventory tests and 16 new CLI tests must pass on Windows and Ubuntu at the exact PR HEAD, including negative cases for unsafe paths, non-DDL data, missing attestations, bad dialect, source immutability, secret non-disclosure, and SQLite WAL sidecar.

A green FUE-0 confirms *only* the scoped software behavior. It does not prove that any actual dental software can generate the supported formats, does not validate patient identity/mapping, and cannot authorize clinical migration.

STOP on unknown original source, non-cold file, possible sensitive data, malformed/unsafe source, missing proof, or any unauthorized write.

NEXT: obtain one officially generated fictional dental software demo export in a separately authorized and safe lab, record actual version/provenance and header, then test a candidate mapping. Physical workstation, signed EXE, actual clinic data and production remain NO-GO. No merge or deployment is authorized here.
