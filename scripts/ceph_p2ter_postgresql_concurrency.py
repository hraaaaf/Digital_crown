"""Two independent PostgreSQL connections contend on migrated claim uniqueness.

Works in a disposable pg18 service; clones exact migrated claim table's unique
constraint into a temporary schema (without production foreign keys) so all
patient identities are synthetic and no other clinical tables require seeding.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
import threading
import time
import psycopg2
from psycopg2 import errors

assert os.getenv("ENVIRONMENT") == "test"
assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
dburl=os.environ["DATABASE_URL"]
assert dburl.startswith("postgresql://postgres:") and "127.0.0.1:5432/" in dburl
with psycopg2.connect(dburl) as db:
    with db.cursor() as c:
        c.execute("SELECT version_num FROM alembic_version")
        assert c.fetchone()[0]=="ceparch0002"
        c.execute("""
          SELECT pg_get_constraintdef(oid) FROM pg_constraint
          WHERE conrelid='public.cephalo_archive_claims'::regclass
            AND conname='uq_cephalo_archive_claim_study_revision'
        """)
        ddl=c.fetchone()
        assert ddl and 'UNIQUE (patient_id, analysis_id, revision)' in ddl[0],ddl
        c.execute("CREATE SCHEMA bench_p2ter_atomic")
        c.execute("""
          CREATE TABLE bench_p2ter_atomic.claims(
            LIKE public.cephalo_archive_claims INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES
          )
        """)
        c.execute("""SELECT count(*) FROM pg_index i
                     JOIN pg_class t ON i.indrelid=t.oid
                     WHERE t.oid='bench_p2ter_atomic.claims'::regclass AND i.indisunique""")
        assert c.fetchone()[0]>=2  # primary key + unique study triple
    db.commit()

first_done=threading.Event()
second_attempt=threading.Event()
def worker_first():
    with psycopg2.connect(dburl) as db:
        with db.cursor() as c:
            c.execute("INSERT INTO bench_p2ter_atomic.claims (patient_id,analysis_id,revision,created_at) VALUES (1717,2727,2,now())")
            first_done.set()
            assert second_attempt.wait(timeout=10)
            time.sleep(.15)
        db.commit()
    return "COMMITTED"

def worker_second():
    assert first_done.wait(timeout=10)
    with psycopg2.connect(dburl) as db:
        with db.cursor() as c:
            second_attempt.set()
            try:
                c.execute("SET LOCAL lock_timeout = '8s'")
                c.execute("INSERT INTO bench_p2ter_atomic.claims(patient_id,analysis_id,revision,created_at) VALUES(1717,2727,2,now())")
            except errors.UniqueViolation:
                db.rollback()
                return "SQLSTATE_23505_REJECTED"
        db.commit()
        return "UNSAFE_SECOND_COMMIT"

with ThreadPoolExecutor(max_workers=2) as pool:
    first=pool.submit(worker_first)
    second=pool.submit(worker_second)
    result=sorted([first.result(timeout=15),second.result(timeout=15)])
assert result==["COMMITTED","SQLSTATE_23505_REJECTED"],result
with psycopg2.connect(dburl) as db:
    with db.cursor() as c:
        c.execute("SELECT count(*) FROM bench_p2ter_atomic.claims")
        assert c.fetchone()[0]==1
        c.execute("DROP SCHEMA bench_p2ter_atomic CASCADE")
    db.commit()
print("POSTGRESQL_18_MIGRATED_CLAIM_TWO_CONNECTIONS_PASS",
      {"outcomes":result,"durable_rows":1,"real_patient_data":False,"clinical_parity_proven":False})
