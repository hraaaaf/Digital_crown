"""LOT05.7-C: PostgreSQL 18 native pg_dump/pg_restore of isolated FAKE databases.

Mandatory CI-only guard: dedicated ephemeral postgres service on loopback with
LOT05C_PG_SYNTHETIC_ONLY=1 and an exact expected service DB/user. All database
names are internally generated. No Cabinet runtime, Alembic, user data or API.
"""
from __future__ import annotations

from contextlib import contextmanager, closing
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tarfile
import tempfile
import unittest


class Refused(ValueError):
    pass


EXPECTED_COUNTS = (2, 100, 200, 10, 10, 3)
TABLES = ("practitioners", "patients", "appointments", "acts", "payments", "media_refs")
_SAFE_DB = re.compile(r"lot05c_fake_(?:src|restore)_[0-9a-f]{12}\Z")


def assert_ci_isolation():
    checks = {
        "LOT05C_PG_SYNTHETIC_ONLY": "1",
        "PGHOST": "127.0.0.1",
        "PGPORT": "5432",
        "PGUSER": "lot05c_ci",
        "PGDATABASE": "lot05c_fake_admin",
        "PGPASSWORD": "only-fake-lot05c-secret",
    }
    if any(os.environ.get(key) != value for key, value in checks.items()):
        raise Refused("DEDICATED_LOCAL_FAKE_POSTGRES_REQUIRED")
    ident = os.environ.get("LOT05C_PG_SERVICE_CONTAINER_ID", "")
    if not re.fullmatch(r"[0-9a-f]{64}", ident):
        raise Refused("EXACT_EPHEMERAL_CONTAINER_REQUIRED")
    return ident


def db_name(label):
    if label not in ("src", "restore"):
        raise Refused("INVALID_FAKE_ROLE")
    return f"lot05c_fake_{label}_{secrets.token_hex(6)}"


def allowed(name):
    if type(name) is not str or _SAFE_DB.fullmatch(name) is None:
        raise Refused("FAKE_DB_ONLY")
    return name


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def connect(name):
    allowed(name)
    import psycopg2
    conn = psycopg2.connect(
        host="127.0.0.1", port=5432,
        user="lot05c_ci", password="only-fake-lot05c-secret", dbname=name,
        connect_timeout=6
    )
    try:
        yield conn
    finally:
        conn.close()


def create_db(name):
    import psycopg2
    from psycopg2 import sql
    allowed(name)
    with closing(psycopg2.connect(
        host="127.0.0.1", port=5432, user="lot05c_ci",
        password="only-fake-lot05c-secret", dbname="lot05c_fake_admin"
    )) as admin:
        admin.autocommit = True
        with admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


def drop_db(name):
    import psycopg2
    from psycopg2 import sql
    allowed(name)
    with closing(psycopg2.connect(
        host="127.0.0.1", port=5432, user="lot05c_ci",
        password="only-fake-lot05c-secret", dbname="lot05c_fake_admin"
    )) as admin:
        admin.autocommit = True
        with admin.cursor() as cursor:
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))


def seed(conn):
    with conn:
        with conn.cursor() as c:
            c.execute("""
CREATE TABLE fake_marker (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE practitioners(
 tenant INT NOT NULL, legacy TEXT NOT NULL, fake_name TEXT NOT NULL,
 PRIMARY KEY(tenant,legacy));
CREATE TABLE patients(
 tenant INT NOT NULL, legacy TEXT NOT NULL, fake_name TEXT NOT NULL,
 practitioner_legacy TEXT NOT NULL, PRIMARY KEY(tenant,legacy),
 FOREIGN KEY(tenant,practitioner_legacy) REFERENCES practitioners(tenant,legacy));
CREATE TABLE appointments(
 tenant INT NOT NULL, legacy TEXT NOT NULL,
 patient_legacy TEXT NOT NULL, practitioner_legacy TEXT NOT NULL,
 PRIMARY KEY(tenant,legacy),
 FOREIGN KEY(tenant,patient_legacy) REFERENCES patients(tenant,legacy),
 FOREIGN KEY(tenant,practitioner_legacy) REFERENCES practitioners(tenant,legacy));
CREATE TABLE acts(
 tenant INT NOT NULL, legacy TEXT NOT NULL,
 patient_legacy TEXT NOT NULL, fake_code TEXT NOT NULL,
 PRIMARY KEY(tenant,legacy),
 FOREIGN KEY(tenant,patient_legacy) REFERENCES patients(tenant,legacy));
CREATE TABLE payments(
 tenant INT NOT NULL, legacy TEXT NOT NULL, act_legacy TEXT NOT NULL,
 amount_cents INT NOT NULL CHECK(amount_cents>0),
 PRIMARY KEY(tenant,legacy),
 FOREIGN KEY(tenant,act_legacy) REFERENCES acts(tenant,legacy));
CREATE TABLE media_refs(
 tenant INT NOT NULL, legacy TEXT NOT NULL, patient_legacy TEXT NOT NULL,
 sha256 TEXT NOT NULL, PRIMARY KEY(tenant,legacy),
 FOREIGN KEY(tenant,patient_legacy) REFERENCES patients(tenant,legacy));
""")
            c.execute("INSERT INTO fake_marker VALUES('type','ONLY_FAKE_LOT05C_PG')")
            c.executemany("INSERT INTO practitioners VALUES (%s,%s,%s)",
                          [(777, f"FAKE-D-{i}", f"FAKE_DOCTOR_{i}") for i in range(2)])
            c.executemany("INSERT INTO patients VALUES (%s,%s,%s,%s)",
                          [(777, f"FAKE-P-{i:03}", f"FAKE_NAME_{i:03}", f"FAKE-D-{i%2}")
                           for i in range(100)])
            c.executemany("INSERT INTO appointments VALUES (%s,%s,%s,%s)",
                          [(777, f"FAKE-APPT-{i:03}", f"FAKE-P-{i//2:03}", f"FAKE-D-{(i//2)%2}")
                           for i in range(200)])
            c.executemany("INSERT INTO acts VALUES (%s,%s,%s,%s)",
                          [(777, f"FAKE-ACT-{i}", f"FAKE-P-{i:03}", "FAKE_CODE")
                           for i in range(10)])
            c.executemany("INSERT INTO payments VALUES (%s,%s,%s,%s)",
                          [(777, f"FAKE-PAY-{i}", f"FAKE-ACT-{i}", 10000 + i)
                           for i in range(10)])
            c.executemany("INSERT INTO media_refs VALUES (%s,%s,%s,%s)",
                          [(777, f"FAKE-MEDIA-{i}", f"FAKE-P-{i:03}",
                            digest_bytes(f"ONLY_FAKE_MEDIA_{i}".encode()))
                           for i in range(3)])


def evidence(conn):
    with conn.cursor() as c:
        c.execute("SELECT value FROM fake_marker WHERE key='type'")
        if c.fetchone() != ("ONLY_FAKE_LOT05C_PG",):
            raise Refused("FAKE_MARKER_REQUIRED")
        rows = {}
        for name in TABLES:
            c.execute(f"SELECT * FROM {name} ORDER BY tenant, legacy")
            rows[name] = c.fetchall()
        payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        counts = tuple(len(rows[n]) for n in TABLES)
        c.execute("SELECT COALESCE(SUM(amount_cents),0) FROM payments")
        money = c.fetchone()[0]
        return digest_bytes(payload.encode()), counts, money


def native_command(container_id, database, *, restore_bytes=None):
    allowed(database)
    ident = assert_ci_isolation()
    if container_id != ident:
        raise Refused("EPHEMERAL_SERVICE_MISMATCH")
    prefix = ["docker", "exec"]
    if restore_bytes is not None:
        prefix.append("-i")
    prefix.extend(["-e", "PGPASSWORD=only-fake-lot05c-secret", ident])
    if restore_bytes is None:
        command = ["pg_dump", "-Fc", "-h", "127.0.0.1",
                   "-U", "lot05c_ci", "-d", database, "--no-owner", "--no-privileges"]
    else:
        command = ["pg_restore", "--single-transaction", "--exit-on-error",
                   "--no-owner", "--no-privileges", "-h", "127.0.0.1",
                   "-U", "lot05c_ci", "-d", database]
    return subprocess.run(prefix + command,
                          input=restore_bytes, capture_output=True, timeout=90)


def fake_media_zip():
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for i in range(3):
            z.writestr(f"fake_media/FAKE-MEDIA-{i}.bin", f"ONLY_FAKE_MEDIA_{i}".encode())
    return buffer.getvalue()


def verified_db_media_refs(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT legacy, sha256 FROM media_refs ORDER BY legacy")
        refs = dict(cursor.fetchall())
    if set(refs) != {f"FAKE-MEDIA-{i}" for i in range(3)}:
        raise Refused("DB_MEDIA_REFERENCE_MISMATCH")
    return refs


def verify_media_zip(raw, db_refs=None):
    import zipfile
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members = sorted(z.namelist())
        if members != [f"fake_media/FAKE-MEDIA-{i}.bin" for i in range(3)]:
            raise Refused("UNEXPECTED_MEDIA_MEMBER")
        for i, name in enumerate(members):
            actual = digest_bytes(z.read(name))
            if actual != digest_bytes(f"ONLY_FAKE_MEDIA_{i}".encode()):
                raise Refused("MEDIA_DIGEST_MISMATCH")
            if db_refs is not None and actual != db_refs.get(f"FAKE-MEDIA-{i}"):
                raise Refused("DB_MEDIA_DIGEST_MISMATCH")


class NativePostgres18Recovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container_id = assert_ci_isolation()
        import psycopg2  # noqa: F401

    def setUp(self):
        self.root_ctx = tempfile.TemporaryDirectory(prefix="lot05c_fake_pg_")
        self.root = Path(self.root_ctx.name)
        self.src, self.dest = db_name("src"), db_name("restore")
        self.created = []
        for db in (self.src, self.dest):
            create_db(db)
            self.created.append(db)
        with connect(self.src) as con:
            seed(con)
            self.before = evidence(con)
        self.assertEqual(self.before[1], EXPECTED_COUNTS)
        self.assertEqual(self.before[2], sum(10000 + i for i in range(10)))
        dump = native_command(self.container_id, self.src)
        if dump.returncode or not dump.stdout.startswith(b"PGDMP"):
            raise Refused("PG_NATIVE_CUSTOM_BACKUP_FAILED")
        self.dump = dump.stdout
        self.dump_sha = digest_bytes(self.dump)
        self.media = fake_media_zip()
        verify_media_zip(self.media)

    def tearDown(self):
        try:
            for db in reversed(getattr(self, "created", [])):
                drop_db(db)
        finally:
            self.root_ctx.cleanup()

    def restore(self, content=None, expected_digest=None):
        raw = self.dump if content is None else content
        wanted = self.dump_sha if expected_digest is None else expected_digest
        if digest_bytes(raw) != wanted:
            raise Refused("PG_DUMP_DIGEST_MISMATCH")
        result = native_command(self.container_id, self.dest, restore_bytes=raw)
        if result.returncode != 0:
            raise Refused("PG_NATIVE_RESTORE_FAILED")
        with connect(self.dest) as con:
            actual = evidence(con)
        if actual != self.before:
            raise Refused("PG_RESTORE_PARITY_FAILED")
        return actual

    def test_01_native_restore_reconciles_all_synthetic_families(self):
        self.assertEqual(self.restore(), self.before)
        with connect(self.dest) as con:
            verify_media_zip(self.media, verified_db_media_refs(con))

    def test_02_post_backup_source_changes_not_in_restored_copy(self):
        with connect(self.src) as con:
            with con:
                with con.cursor() as c:
                    c.execute("UPDATE patients SET fake_name='FAKE_LATER' WHERE legacy='FAKE-P-000'")
            self.assertNotEqual(evidence(con), self.before)
        self.assertEqual(self.restore(), self.before)

    def test_03_tampered_dump_hash_fails_before_any_restore(self):
        with self.assertRaisesRegex(Refused, "PG_DUMP_DIGEST_MISMATCH"):
            self.restore(content=self.dump[:-128])
        with connect(self.dest) as con:
            with con.cursor() as c:
                c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
                self.assertEqual(c.fetchone()[0], 0)

    def test_04_truncated_native_dump_is_refused_by_pg_restore(self):
        result = native_command(self.container_id, self.dest, restore_bytes=self.dump[:24])
        self.assertNotEqual(result.returncode, 0)
        with connect(self.dest) as con:
            with con.cursor() as c:
                c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
                self.assertEqual(c.fetchone()[0], 0)

    def test_05_composite_foreign_key_blocks_cross_tenant(self):
        import psycopg2
        with connect(self.src) as con:
            with self.assertRaises(psycopg2.IntegrityError):
                with con:
                    with con.cursor() as c:
                        c.execute("INSERT INTO appointments VALUES (778,'FAKE-CROSS','FAKE-P-000','FAKE-D-0')")
            self.assertEqual(evidence(con), self.before)

    def test_06_payment_constraint_and_rollback(self):
        import psycopg2
        with connect(self.src) as con:
            with self.assertRaises(psycopg2.IntegrityError):
                with con:
                    with con.cursor() as c:
                        c.execute("INSERT INTO payments VALUES (777,'FAKE-NEG','FAKE-ACT-0',-5)")
            self.assertEqual(evidence(con), self.before)

    def test_07_fake_media_byte_corruption_denied(self):
        altered = bytearray(self.media)
        # Parse valid zip and alter a member payload to prove content digest checking.
        import zipfile
        zipped = io.BytesIO()
        with zipfile.ZipFile(zipped, "w") as out:
            for i in range(3):
                out.writestr(f"fake_media/FAKE-MEDIA-{i}.bin",
                             b"WRONG_FAKE_CONTENT" if i == 1 else f"ONLY_FAKE_MEDIA_{i}".encode())
        with self.assertRaisesRegex(Refused, "MEDIA_DIGEST_MISMATCH"):
            verify_media_zip(zipped.getvalue())

    def test_08_zip_traversal_member_denied(self):
        import zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../fake_exit.txt", b"NOT_ALLOWED")
        with self.assertRaisesRegex(Refused, "UNEXPECTED_MEDIA_MEMBER"):
            verify_media_zip(buffer.getvalue())

    def test_09_wrong_database_name_fails_closed(self):
        for name in ("production", "cabinet", "postgres", "lot05c_fake_src_BAD", "lot05c_fake_src_../x"):
            with self.subTest(name=name), self.assertRaisesRegex(Refused, "FAKE_DB_ONLY"):
                allowed(name)

    def test_10_repeated_native_restore_to_nonempty_target_is_rejected(self):
        self.restore()
        again = native_command(self.container_id, self.dest, restore_bytes=self.dump)
        self.assertNotEqual(again.returncode, 0)
        with connect(self.dest) as con:
            self.assertEqual(evidence(con), self.before)


    def test_11_media_reference_change_after_restore_is_refused(self):
        self.restore()
        with connect(self.dest) as con:
            with con:
                with con.cursor() as cursor:
                    cursor.execute(
                        "UPDATE media_refs SET sha256=%s WHERE legacy=%s",
                        ("0" * 64, "FAKE-MEDIA-1")
                    )
            with self.assertRaisesRegex(Refused, "DB_MEDIA_DIGEST_MISMATCH"):
                verify_media_zip(self.media, verified_db_media_refs(con))


if __name__ == "__main__":
    unittest.main()
