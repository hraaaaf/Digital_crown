"""LOT05.7-D. Real Alembic schema, genuine native PostgreSQL 18 restore.

FAKE patients only, ephemeral GitHub Actions Postgres only.
Never accept external source, filename, username, host, or clinical DB.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import unittest
from datetime import datetime
from decimal import Decimal

URL = "postgresql://postgres:postgres@127.0.0.1:5432/lot05d_fake_source"
HEAD = "neo000000031"
TARGET = "lot05d_fake_restored"
COUNTS = {"users": 2, "patients": 6, "appointments": 12,
          "actes": 4, "payments": 4, "document_archives": 2}


class Refused(RuntimeError):
    pass


def isolated():
    cid = os.getenv("LOT05D_PG_SERVICE_CONTAINER_ID", "")
    if (os.getenv("LOT05D_REAL_ALEMBIC_SYNTHETIC_ONLY") != "1"
            or os.getenv("DATABASE_URL") != URL
            or not re.fullmatch(r"[0-9a-f]{64}", cid)):
        raise Refused("DEDICATED_FAKE_POSTGRES_REQUIRED")
    return cid


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def native(db, data=None):
    cid = isolated()
    if (data is None and db != "lot05d_fake_source") or (data is not None and db != TARGET):
        raise Refused("FOREIGN_DATABASE_DENIED")
    command = ["docker", "exec"]
    if data is not None:
        command.append("-i")
    command += ["-e", "PGPASSWORD=postgres", cid]
    if data is None:
        command += ["pg_dump", "-Fc", "--no-owner", "--no-privileges", "-h", "127.0.0.1",
                    "-U", "postgres", "-d", db]
    else:
        command += ["pg_restore", "--single-transaction", "--exit-on-error",
                    "--no-owner", "--no-privileges", "-h", "127.0.0.1",
                    "-U", "postgres", "-d", db]
    return subprocess.run(command, input=data, capture_output=True, timeout=120)



# PostgreSQL 18 deparser rewrites text[] casts on one partial index and
# four CHECK expressions after pg_dump/restore. Narrow allowlist only;
# any changed enum literal, operator, table/column or constraint FAILS.
KNOWN_PG18_ARRAYS = {
    "ck_clinical_assets_asset_type": (
        "asset_type", ("PHOTO", "RADIOGRAPH", "DOCUMENT", "VIDEO", "AUDIO", "OTHER")),
    "ck_clinical_assets_source_kind": (
        "source_kind", ("UPLOAD", "IMPORT", "DERIVED", "CLINICAL_ANALYSIS", "DEVICE_CAPTURE")),
    "ck_ngap_mapping_code_kind": (
        "code_kind", ("NGAP", "INTERNAL", "OTHER")),
    "ck_ngap_mapping_verification_status": (
        "verification_status", ("PRIMARY_HASH_PENDING", "VERIFIED_PRIMARY", "OUTDATED")),
    "ck_ortho_cases_lifecycle_status": (
        "lifecycle_status", ("ACTIVE", "INTERRUPTED", "ABANDONED", "CLOSED")),
    "ck_ortho_controls_phase_key": (
        "phase_key", ("DIAGNOSTIC", "PREPARATION", "APPAREILLAGE",
                      "ALIGNEMENT", "FINITION", "CONTENTION", "CLOTURE")),
    "ck_ortho_phase_events_event_type": (
        "event_type", ("START", "ENTER_PHASE", "INTERRUPT",
                       "RESUME", "ABANDON", "CLOSE")),
    "uq_ortho_cases_one_open_per_patient": (
        "lifecycle_status", ("ACTIVE", "INTERRUPTED")),
}


# Exactly three additional affected constraints; do not transform other CHECK
# expressions. Exact table, semantic values, and full SQL grammar are pinned.
KNOWN_PG18_EXTRA_CHECKS = {
    "ck_ortho_phase_events_phase_key": (
        "ortho_phase_events",
        ("DIAGNOSTIC", "PREPARATION", "APPAREILLAGE", "ALIGNEMENT",
         "FINITION", "CONTENTION", "CLOTURE"),
        "CHECK (phase_key IS NULL OR (phase_key::text = ANY ({array})))",
    ),
    "ck_ortho_phase_events_phase_only_on_start_or_enter": (
        "ortho_phase_events",
        ("START", "ENTER_PHASE"),
        "CHECK ((event_type::text = ANY ({array})) OR phase_key IS NULL)",
    ),
    "ck_station_print_event_transition": (
        "station_print_claim_events",
        ("held_reserved", "marked_uncertain"),
        "CHECK (transition::text = ANY ({array}))",
    ),
}



def normalize_pg18_check_text_arrays(expr):
    """Canonicalize only the proven literal varchar[] to text[] cast rewrite."""
    pattern = re.compile(r"ARRAY\[(?P<body>[^\[\]]+)\](?P<outer>::text\[\])?")

    def replace_array(match):
        pieces = match.group("body").split(",")
        values = []
        per_element_text = []
        for item in pieces:
            parsed = re.fullmatch(
                r"\s*'([^']+)'::character varying(?P<per>::text)?\s*", item
            )
            if parsed is None:
                return match.group(0)
            values.append(parsed.group(1))
            per_element_text.append(parsed.group("per") is not None)
        outer = match.group("outer") == "::text[]"
        if (outer and any(per_element_text)) or (not outer and not all(per_element_text)):
            return match.group(0)
        return "ARRAY[" + ",".join("'" + v + "'::text" for v in values) + "]"

    return pattern.sub(replace_array, expr)


def canonical_catalog_row(section, row):
    name = row[1] if section == "constraints" else row[0]
    is_constraint = section == "constraints" and name in KNOWN_PG18_ARRAYS and name.startswith("ck_")
    is_index = section == "indexes" and name == "uq_ortho_cases_one_open_per_patient"
    if not (is_constraint or is_index):
        if section == "constraints" and name in KNOWN_PG18_EXTRA_CHECKS:
            table, exact_values, expected_sql_template = KNOWN_PG18_EXTRA_CHECKS[name]
            if len(row) != 4 or row[0] != table or row[2] != "c":
                raise Refused("PG18_EXTRA_CHECK_IDENTITY_MISMATCH")
            array = "ARRAY[" + ",".join("'" + value + "'::text"
                                        for value in exact_values) + "]"
            expected_sql = expected_sql_template.format(array=array)
            # Only known PostgreSQL 18 cast spelling is canonicalized; the
            # entire resulting CHECK SQL must match the approved template.
            if normalize_pg18_check_text_arrays(row[-1]) != expected_sql:
                raise Refused("PG18_EXTRA_CHECK_SEMANTICS_CHANGED")
            return (*row[:-1], expected_sql)
        # All other catalog objects are compared byte-for-byte.
        return row
    column, values = KNOWN_PG18_ARRAYS[name]
    raw = row[-1]
    literal_values = tuple(re.findall(r"'([^']+)'::character varying", raw))
    if literal_values != values or raw.count("'") != len(values) * 2:
        raise Refused("PG18_ENUM_DEPARSE_UNEXPECTED_VALUES")
    shadow = re.sub(r"'[^']+'::character varying", "ENUM", raw)
    shadow = shadow.replace("::text[]", "").replace("::text", "")
    shadow = re.sub(r"[\s\(\)\[\],]", "", shadow)
    if is_constraint:
        if row[2] != "c":
            raise Refused("PG18_DEPARSE_CONSTRAINT_TYPE_CHANGED")
        expected = ("CHECK" + column +
                    ("ISNULLOR" + column if name == "ck_ortho_controls_phase_key" else "") +
                    "=ANYARRAY" + "ENUM" * len(values))
    else:
        expected = ("CREATEUNIQUEINDEXuq_ortho_cases_one_open_per_patient"
                    "ONpublic.ortho_casesUSINGbtreeemployer_idpatient_id"
                    "WHERElifecycle_status=ANYARRAYENUMENUM")
    if shadow != expected:
        raise Refused("PG18_ENUM_DEPARSE_UNEXPECTED_SQL")
    return (*row[:-1], expected)


def catalog(c, include_details=False):
    from sqlalchemy import text
    sql = {
        "columns": """SELECT table_name,column_name,data_type,udt_name,is_nullable,
                COALESCE(column_default,'') FROM information_schema.columns
                WHERE table_schema='public' ORDER BY table_name,ordinal_position""",
        "indexes": """SELECT indexname,indexdef FROM pg_indexes
                WHERE schemaname='public' ORDER BY indexname""",
        "constraints": """SELECT conrelid::regclass::text,conname,contype,
                       pg_get_constraintdef(oid,TRUE)
                FROM pg_constraint WHERE connamespace='public'::regnamespace
                ORDER BY conrelid::regclass::text,conname""",
    }
    data = {name: [tuple(map(str, row)) for row in c.execute(text(query)).all()]
            for name, query in sql.items()}
    table_count = len({row[0] for row in data["columns"]})
    if table_count < 30:
        raise Refused("REAL_ALEMBIC_SCHEMA_INCOMPLETE")
    # PostgreSQL restore can reorder homonymous catalog rows although the
    # object multiset is unchanged. Compare sorted FULL row tuples, retaining
    # every object and multiplicity; no subset counting or silent exclusion.
    normalized = {section: sorted(canonical_catalog_row(section, row) for row in rows)
                  for section, rows in data.items()}
    base = (digest(json.dumps(normalized, sort_keys=True).encode()), table_count)
    return (*base, data) if include_details else base


def evidence(c):
    from sqlalchemy import text
    queries = {
        "users": "SELECT id,email,role,employer_id FROM users ORDER BY id",
        "patients": "SELECT id,numero_dossier,nom,prenom,employer_id FROM patients ORDER BY id",
        "appointments": "SELECT id,patient_id,employer_id,datetime_start FROM appointments ORDER BY id",
        "actes": "SELECT id,patient_id,praticien_id,libelle,montant FROM actes ORDER BY id",
        "payments": "SELECT id,patient_id,acte_id,amount FROM payments ORDER BY id",
        "document_archives": "SELECT id,patient_id,filename,file_hash,file_path FROM document_archives ORDER BY id",
    }
    rows = {name: [tuple(str(v) if v is not None else None for v in row)
                   for row in c.execute(text(query)).all()]
            for name, query in queries.items()}
    sums = (
        str(sum(Decimal(x[4]) for x in rows["actes"])),
        str(sum(Decimal(x[3]) for x in rows["payments"])),
    )
    return digest(json.dumps(rows, sort_keys=True).encode()), {
        name: len(row) for name, row in rows.items()
    }, sums


def tenant_orphans(c):
    from sqlalchemy import text
    return c.execute(text("""SELECT COUNT(*) FROM appointments a
        JOIN patients p ON p.id=a.patient_id WHERE a.employer_id <> p.employer_id""")).scalar_one()


class RealHeadRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        isolated()
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from backend.core.schema_runtime import CURRENT_ALEMBIC_HEAD, assert_database_at_current_head
        from backend import models

        if ScriptDirectory.from_config(Config("alembic.ini")).get_heads() != [HEAD]:
            raise Refused("WRONG_ALEMBIC_GRAPH_HEAD")
        if CURRENT_ALEMBIC_HEAD != HEAD:
            raise Refused("STALE_APPLICATION_HEAD")
        cls.engine = create_engine(URL)
        assert_database_at_current_head(cls.engine)
        with cls.engine.connect() as c:
            if any(c.exec_driver_sql(f'SELECT COUNT(*) FROM "{table}"').scalar_one()
                   for table in COUNTS):
                raise Refused("SYNTHETIC_SOURCE_NOT_EMPTY")
        with Session(cls.engine) as s:
            owners = [
                models.User(email=f"only-fake-{i}@invalid.example",
                            hashed_password="FICTIONAL_NON_AUTHENTICATING",
                            role=models.UserRole.DENTISTE, is_active=True)
                for i in range(2)
            ]
            s.add_all(owners)
            s.flush()
            patients = []
            for k in range(6):
                owner = owners[k // 3]
                p = models.Patient(
                    numero_dossier=f"FAKE-{k}", nom="SYNTHETIC_ONLY",
                    prenom=f"FICTION_{k}", date_naissance=datetime(2000, 1, k+1),
                    sexe="M", employer_id=owner.id)
                s.add(p)
                patients.append(p)
            s.flush()
            for k, p in enumerate(patients):
                for n in range(2):
                    s.add(models.Appointment(
                        patient_id=p.id, employer_id=p.employer_id,
                        datetime_start=datetime(2026, 11, k+1, 9+n),
                        duration_minutes=30, motif="SYNTHETIC_ONLY"))
            for k in range(4):
                p = patients[k]
                act = models.Acte(
                    patient_id=p.id, praticien_id=owners[k // 3].id,
                    type_acte=models.ActeType.SOIN, libelle="FAKE_ACT",
                    montant=float(120+k), notes_cliniques="FICTION")
                s.add(act)
                s.flush()
                s.add(models.Payment(
                    patient_id=p.id, acte_id=act.id, amount=float(80+k)))
            for k in (0, 3):
                p = patients[k]
                raw = f"ONLY_FAKE_DOC_{k}".encode()
                s.add(models.DocumentArchive(
                    patient_id=p.id,
                    document_type=list(models.DocumentType)[0],
                    filename=f"FAKE_{k}.bin", original_filename=f"FAKE_{k}.bin",
                    file_path=f"/ONLY-FAKE-UNRESOLVABLE/FAKE_{k}.bin",
                    file_hash=digest(raw), file_size=len(raw),
                    document_group_id=f"FAKE_GROUP_{k}"))
            s.commit()
        with cls.engine.connect() as c:
            cls.before = evidence(c)
            cls.schema = catalog(c)
            if cls.before[1] != COUNTS or tenant_orphans(c):
                raise Refused("FICTITIOUS_SEED_INCONSISTENT")
        export = native("lot05d_fake_source")
        if export.returncode or not export.stdout.startswith(b"PGDMP"):
            raise Refused("NATIVE_PG_DUMP_FAILED")
        cls.dump = export.stdout
        cls.dump_sha = digest(export.stdout)
        cls.dst = create_engine(URL.replace("lot05d_fake_source", TARGET))

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "dst"):
            cls.dst.dispose()
        if hasattr(cls, "engine"):
            cls.engine.dispose()

    def setUp(self):
        import psycopg2
        from psycopg2 import sql
        isolated()
        admin = psycopg2.connect(URL)
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TARGET)))
        finally:
            admin.close()

    def tearDown(self):
        import psycopg2
        from psycopg2 import sql
        self.dst.dispose()
        admin = psycopg2.connect(URL)
        admin.autocommit = True
        try:
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(TARGET)))
        finally:
            admin.close()

    def restore(self, raw=None, expected_sha=None):
        value = self.dump if raw is None else raw
        expected = self.dump_sha if expected_sha is None else expected_sha
        if digest(value) != expected:
            raise Refused("DUMP_BYTES_MISMATCH")
        result = native(TARGET, data=value)
        if result.returncode:
            raise Refused("PG_NATIVE_RESTORE_FAILED")

    def test_01_full_physical_alembic_schema_restored(self):
        from backend.core.schema_runtime import assert_database_at_current_head
        self.restore()
        assert_database_at_current_head(self.dst)
        with self.dst.connect() as c:
            actual = catalog(c)
            if actual != self.schema:
                # Real physical mismatch is not skipped or normalized away.
                with self.engine.connect() as source_conn:
                    before = catalog(source_conn, include_details=True)[2]
                after = catalog(c, include_details=True)[2]
                first_differences = {}
                for section in before:
                    missing = sorted(set(map(repr, before[section])) - set(map(repr, after[section])))
                    added = sorted(set(map(repr, after[section])) - set(map(repr, before[section])))
                    if missing or added:
                        first_differences[section] = {"source_only": missing[:4], "restore_only": added[:4],
                                                       "source_count": len(before[section]),
                                                       "restore_count": len(after[section])}
                canonical_differences = {}
                for section in before:
                    left = sorted(canonical_catalog_row(section, row) for row in before[section])
                    right = sorted(canonical_catalog_row(section, row) for row in after[section])
                    if left != right:
                        from collections import Counter
                        minus = Counter(left) - Counter(right)
                        plus = Counter(right) - Counter(left)
                        canonical_differences[section] = {
                            "missing": [repr(k) for k in list(minus)[:3]],
                            "added": [repr(k) for k in list(plus)[:3]],
                        }
                self.fail("PHYSICAL_ALEMBIC_CATALOG_MISMATCH " +
                          repr({"canonical": canonical_differences,
                                "raw": first_differences})[:6500])
            self.assertEqual(evidence(c), self.before)
            self.assertGreater(self.schema[1], 30)

    def test_02_real_model_rows_finance_docs_persist(self):
        self.restore()
        with self.dst.connect() as c:
            self.assertEqual(evidence(c), self.before)
            self.assertEqual(tenant_orphans(c), 0)
            self.assertEqual(c.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one(), HEAD)

    def test_03_altered_checksum_denied_before_restore(self):
        with self.assertRaisesRegex(Refused, "DUMP_BYTES_MISMATCH"):
            self.restore(raw=self.dump[:-16])
        with self.dst.connect() as c:
            self.assertEqual(c.exec_driver_sql(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'").scalar_one(), 0)

    def test_04_corrupt_pg_dump_transactionally_rejected(self):
        payload = self.dump[:24]
        with self.assertRaisesRegex(Refused, "PG_NATIVE_RESTORE_FAILED"):
            self.restore(raw=payload, expected_sha=digest(payload))
        with self.dst.connect() as c:
            self.assertEqual(c.exec_driver_sql(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'").scalar_one(), 0)

    def test_05_nonempty_target_replay_rejected(self):
        self.restore()
        with self.assertRaisesRegex(Refused, "PG_NATIVE_RESTORE_FAILED"):
            self.restore()
        with self.dst.connect() as c:
            self.assertEqual(evidence(c), self.before)

    def test_06_wrong_target_denied(self):
        for name in ("postgres", "cabinet", "lot05d_fake_real", "lot05d_fake_restored_extra"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(Refused, "FOREIGN_DATABASE_DENIED"):
                    native(name, data=b"FAKE")

    def test_07_audit_detects_cross_tenant_reference_in_test_transaction(self):
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        from backend import models
        self.restore()
        with self.dst.connect() as c:
            tx = c.begin()
            try:
                patient = c.execute(text("SELECT id,employer_id FROM patients ORDER BY id LIMIT 1")).one()
                owner = c.execute(text("SELECT id FROM users WHERE id <> :id ORDER BY id LIMIT 1"),
                                  {"id": patient.employer_id}).scalar_one()
                # Use genuine ORM defaults so an unrelated NOT NULL constraint
                # cannot fake a successful cross-tenant rejection.
                with Session(bind=c) as fake_session:
                    fake_session.add(models.Appointment(
                        patient_id=patient.id, employer_id=owner,
                        datetime_start=datetime(2026, 12, 1, 9),
                        duration_minutes=30, motif="FAKE_WRONG_TENANT"))
                    fake_session.flush()
                    self.assertEqual(tenant_orphans(c), 1)
            finally:
                tx.rollback()
        with self.dst.connect() as c:
            self.assertEqual(evidence(c), self.before)

    def test_08_source_transaction_changes_never_enter_previous_dump(self):
        from sqlalchemy import text
        with self.engine.connect() as src:
            tx = src.begin()
            try:
                src.execute(text("UPDATE patients SET nom='FAKE_NEW' WHERE id=(SELECT MIN(id) FROM patients)"))
                self.assertNotEqual(evidence(src), self.before)
            finally:
                tx.rollback()
        self.restore()
        with self.dst.connect() as c:
            self.assertEqual(evidence(c), self.before)


    def test_09_known_pg18_deparse_must_be_semantically_constrained(self):
        name = "ck_ngap_mapping_code_kind"
        left = ("CHECK (code_kind::text = ANY "
                "(ARRAY['NGAP'::character varying, 'INTERNAL'::character varying, "
                "'OTHER'::character varying]::text[]))")
        right = ("CHECK (code_kind::text = ANY "
                 "(ARRAY['NGAP'::character varying::text, "
                 "'INTERNAL'::character varying::text, "
                 "'OTHER'::character varying::text]))")
        self.assertEqual(
            canonical_catalog_row("constraints", ("ngap_catalog_mappings", name, "c", left)),
            canonical_catalog_row("constraints", ("ngap_catalog_mappings", name, "c", right)),
        )
        for forged in (right.replace("'NGAP'", "'FOREIGN'"),
                       right.replace("code_kind::text =", "code_kind::text <>"),
                       right + " OR TRUE"):
            with self.subTest(forged=forged), self.assertRaises(Refused):
                canonical_catalog_row("constraints", ("ngap_catalog_mappings", name, "c", forged))

        source = ("CHECK ((event_type::text = ANY (ARRAY['START'::character varying, "
                  "'ENTER_PHASE'::character varying]::text[])) OR phase_key IS NULL)")
        restored = ("CHECK ((event_type::text = ANY (ARRAY['START'::character varying::text, "
                    "'ENTER_PHASE'::character varying::text])) OR phase_key IS NULL)")
        key = ("ortho_phase_events", "ck_ortho_phase_events_phase_only_on_start_or_enter", "c")
        self.assertEqual(
            canonical_catalog_row("constraints", (*key, source)),
            canonical_catalog_row("constraints", (*key, restored)),
        )
        self.assertNotEqual(
            canonical_catalog_row("constraints", (*key, restored)),
            canonical_catalog_row("constraints", (*key, restored.replace("OR phase_key IS NULL", "OR TRUE"))),
        )
        self.assertNotEqual(
            canonical_catalog_row("constraints", (*key, restored)),
            canonical_catalog_row("constraints", (*key, restored.replace("'START'", "'OTHER'"))),
        )



    def test_10_additional_pg18_check_casts_use_exact_allowlist(self):
        for name, (table, values, fmt) in KNOWN_PG18_EXTRA_CHECKS.items():
            inner = ",".join("'" + v + "'::character varying" for v in values)
            array_before = "ARRAY[" + inner + "]::text[]"
            array_after = "ARRAY[" + inner.replace("::character varying",
                                                     "::character varying::text") + "]"
            before = fmt.format(array=array_before)
            after = fmt.format(array=array_after)
            with self.subTest(constraint=name):
                self.assertEqual(
                    canonical_catalog_row("constraints", (table, name, "c", before)),
                    canonical_catalog_row("constraints", (table, name, "c", after)),
                )
                for bad in (
                    after.replace(values[0], "FOREIGN_VALUE"),
                    after.replace("= ANY", "<> ANY"),
                    after + " OR TRUE",
                ):
                    with self.assertRaisesRegex(Refused, "PG18_EXTRA_CHECK_SEMANTICS_CHANGED"):
                        canonical_catalog_row("constraints", (table, name, "c", bad))
                with self.assertRaisesRegex(Refused, "PG18_EXTRA_CHECK_IDENTITY_MISMATCH"):
                    canonical_catalog_row("constraints", ("other_table", name, "c", after))
        # Unknown constraint names stay byte-identical; no generic rewrite.
        sample = ("CHECK (arbitrary::text = ANY "
                  "(ARRAY['A'::character varying]::text[]))")
        row = ("unknown_table", "ck_unknown_name", "c", sample)
        self.assertEqual(canonical_catalog_row("constraints", row), row)



if __name__ == "__main__":
    unittest.main()
