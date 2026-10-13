"""LOT05.6 fake SQLite download/upload contract: actual bytes, actual rows, zero cabinet IO."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
import unittest

from sqlalchemy import MetaData

from test_legacy_sql_migration_scenarios_v15 import _real_declared_model_only

ROOT = Path(__file__).resolve().parents[1]
# Load gateway as ordinary backend.services module, not backend database.
from backend.services import legacy_migration_synthetic_file_v15 as fixture


class OfficialSyntheticFileFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta=_real_declared_model_only()
        cls.official=fixture.build_synthetic_fixture_bytes()

    def test_01_official_download_is_a_real_sqlite_with_exact_three_tables(self):
        self.assertTrue(self.official.startswith(b"SQLite format 3\x00"))
        self.assertLess(len(self.official),fixture.MAX_FIXTURE_BYTES)
        conn=sqlite3.connect(":memory:")
        try:
            conn.deserialize(self.official)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM legacy_patients").fetchone()[0],100)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM legacy_appointments").fetchone()[0],200)
            self.assertEqual(conn.execute("SELECT version FROM dc_fixture_marker").fetchone()[0],
                             fixture._MARKER)
        finally: conn.close()

    def test_02_same_download_recreates_exact_bytes_for_sha_gate(self):
        self.assertEqual(self.official,fixture.build_synthetic_fixture_bytes())

    def test_03_upload_all_300_fake_rows_and_links_zero_persisted(self):
        out=fixture.rehearse_uploaded_synthetic_sqlite(self.official,self.meta)
        self.assertEqual(out["mode"],"OFFICIAL_SYNTHETIC_SQLITE_FILE_ONLY")
        self.assertEqual(tuple(out[x] for x in (
            "source_patients","source_appointments","verified_patients",
            "verified_appointments","verified_patient_links","orphan_appointments",
            "cross_tenant_links","after_rollback_patients","after_rollback_appointments",
        )),(100,200,100,200,200,0,0,0,0))
        for key in ("cabinet_rows_read","cabinet_rows_written","source_persisted","import_permitted"):
            self.assertIs(out[key],False)
        self.assertEqual(len(out["source_sha256"]),64)

    def test_04_two_independent_requests_do_not_share_temp_db(self):
        first=fixture.rehearse_uploaded_synthetic_sqlite(self.official,self.meta)
        second=fixture.rehearse_uploaded_synthetic_sqlite(self.official,self.meta)
        self.assertEqual(first,second)
        self.assertEqual(second["after_rollback_appointments"],0)

    def test_05_other_sqlite_even_same_schema_and_fake_marker_refused(self):
        db=sqlite3.connect(":memory:")
        try:
            db.deserialize(self.official)
            db.execute("UPDATE legacy_patients SET first_name='PERSONNE IDENTIFIABLE' WHERE id=10001")
            db.commit()
            altered=db.serialize()
        finally: db.close()
        with self.assertRaisesRegex(fixture.SyntheticFileRefused,"ONLY_OFFICIAL"):
            fixture.rehearse_uploaded_synthetic_sqlite(altered,self.meta)

    def test_06_modified_appointment_relation_refused(self):
        db=sqlite3.connect(":memory:")
        try:
            db.deserialize(self.official)
            db.execute("UPDATE legacy_appointments SET patient_ref=999999 WHERE id=50001")
            db.commit()
            altered=db.serialize()
        finally: db.close()
        with self.assertRaises(fixture.SyntheticFileRefused):
            fixture.rehearse_uploaded_synthetic_sqlite(altered,self.meta)

    def test_07_malicious_extra_table_rejected_before_deserialize(self):
        db=sqlite3.connect(":memory:")
        try:
            db.deserialize(self.official)
            db.execute("CREATE TABLE secrets (private_data TEXT)")
            db.commit()
            altered=db.serialize()
        finally: db.close()
        with self.assertRaisesRegex(fixture.SyntheticFileRefused,"ONLY_OFFICIAL"):
            fixture.rehearse_uploaded_synthetic_sqlite(altered,self.meta)

    def test_08_wrong_mime_bytes_and_truncated_header_refused(self):
        for contents in (b"",b"HELLO",b"SQLite format 3\x00",
                         self.official[:15], b'<?xml version="1.0"?>'):
            with self.subTest(size=len(contents)):
                with self.assertRaises(fixture.SyntheticFileRefused):
                    fixture.rehearse_uploaded_synthetic_sqlite(contents,self.meta)

    def test_09_oversize_file_refused_before_any_sqlite_parsing(self):
        with self.assertRaisesRegex(fixture.SyntheticFileRefused,"HEADER_OR_SIZE"):
            fixture.rehearse_uploaded_synthetic_sqlite(
                self.official + b"x"*(fixture.MAX_FIXTURE_BYTES+1),self.meta
            )

    def test_10_invalid_schema_metadata_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"DECLARED_TABLE_MISSING"):
            fixture.rehearse_uploaded_synthetic_sqlite(self.official,MetaData())

    def test_11_router_download_and_upload_are_owner_gated_and_bounded(self):
        router=(ROOT/"routers"/"legacy_migration_v15.py").read_text()
        self.assertIn('"/synthetic-fixture"',router)
        self.assertIn('"/synthetic-file-dryrun"',router)
        self.assertGreaterEqual(router.count("Depends(_owner_only)"),4)
        self.assertIn("MAX_FIXTURE_BYTES",router)
        self.assertIn("request.stream()",router)
        self.assertNotIn("db.commit(",router)
        self.assertIn("inspect_cabinet_schema_read_only(",router)

    def test_12_only_backend_fixture_bytes_are_accepted_not_vendor_db(self):
        # Even other 100x200 all-fake SQLite files aren't allowed. This is a
        # deliberately narrow path, *not* a general SQLite import capability.
        with self.assertRaisesRegex(fixture.SyntheticFileRefused,"ONLY_OFFICIAL"):
            fixture.rehearse_uploaded_synthetic_sqlite(
                self.official + b"x",self.meta
            )

if __name__=="__main__":
    unittest.main()
