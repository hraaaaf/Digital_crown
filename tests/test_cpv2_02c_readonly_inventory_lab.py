"""Synthetic-only read-only inventory FUE-0. Never uses real clinic data."""
import hashlib
import io
import sqlite3
import unittest
import warnings
import zipfile

from backend.services.pocket_document_inventory import inventory_pocket_archive_readonly

PDF = b'%PDF-1.4\nfictional content\n%%EOF\n'
CANON = 'archives/101/CERTIFICAT/2026/11/example.pdf'
LEGACY = 'documents/2026/11/example.pdf'


def database(path='static/' + CANON, sha=None, size=None, receipt=None):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE document_archives(id INTEGER, patient_id INTEGER, document_type TEXT, file_path TEXT, file_hash TEXT, file_size INTEGER, status TEXT)')
    db.execute('INSERT INTO document_archives VALUES(1,101,?,?,?,?,?)', (
        'CERTIFICAT', path, sha if sha is not None else hashlib.sha256(PDF).hexdigest(),
        len(PDF) if size is None else size, 'ACTIF'))
    if receipt:
        db.execute('CREATE TABLE mobile_document_archive_receipts (id INTEGER, state TEXT)')
        db.execute('INSERT INTO mobile_document_archive_receipts VALUES(1,?)', (receipt,))
    db.commit()
    return db


def media_zip(items):
    b = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(b, 'w') as archive:
            for path, contents in items:
                archive.writestr(path, contents)
    b.seek(0)
    return zipfile.ZipFile(b)


class TestInventory(unittest.TestCase):
    def test_matched_legacy_without_receipts_is_only_byte_match(self):
        db, media = database(path='static/' + LEGACY), media_zip([(LEGACY, PDF)])
        try:
            before = tuple(db.iterdump())
            result = inventory_pocket_archive_readonly(db, media)
            self.assertEqual('BYTE_INVENTORY_MATCHED_NOT_RESTORE_APPROVED', result['status'])
            self.assertEqual('MATCHED', result['entries'][0]['status'])
            self.assertEqual(before, tuple(db.iterdump()))
            self.assertNotIn(LEGACY, str(result))
        finally:
            db.close(); media.close()

    def test_orphan_has_sha256_without_patient_path(self):
        orphan = 'documents/2026/11/orphan.pdf'
        db, media = database(), media_zip([(CANON, PDF), (orphan, PDF + b'orphan')])
        try:
            result = inventory_pocket_archive_readonly(db, media)
            self.assertEqual('REVIEW_REQUIRED', result['status'])
            self.assertEqual('MATCHED', result['entries'][0]['status'])
            entries = [x for x in result['entries'] if x['reason'] == 'UNLINKED_MEDIA']
            self.assertEqual(1, len(entries))
            self.assertEqual(hashlib.sha256(PDF + b'orphan').hexdigest(), entries[0]['actual_sha256'])
            self.assertNotIn(orphan, str(result))
        finally:
            db.close(); media.close()

    def test_same_size_sha_mismatch_flagged(self):
        changed = PDF.replace(b'fictional', b'fictionXl')
        self.assertEqual(len(PDF), len(changed))
        db, media = database(path='static/' + LEGACY), media_zip([(LEGACY, changed)])
        try:
            row = inventory_pocket_archive_readonly(db, media)['entries'][0]
            self.assertEqual('SHA256_MISMATCH', row['reason'])
            self.assertEqual(hashlib.sha256(changed).hexdigest(), row['actual_sha256'])
        finally:
            db.close(); media.close()

    def test_missing_sql_linked_media(self):
        db, media = database(), media_zip([])
        try:
            self.assertEqual('MISSING_MEDIA', inventory_pocket_archive_readonly(db, media)['entries'][0]['reason'])
        finally:
            db.close(); media.close()

    def test_unrecognized_historical_mapping(self):
        db, media = database(path='static/other/legacy.pdf'), media_zip([('other/legacy.pdf', PDF)])
        try:
            self.assertEqual('UNSUPPORTED_SQL_PATH', inventory_pocket_archive_readonly(db, media)['entries'][0]['reason'])
        finally:
            db.close(); media.close()

    def test_processing_receipt_never_silently_repaired(self):
        db, media = database(receipt='PROCESSING'), media_zip([(CANON, PDF)])
        try:
            result = inventory_pocket_archive_readonly(db, media)
            self.assertEqual('REVIEW_REQUIRED', result['status'])
            self.assertTrue(any(x['reason'] == 'INCOMPLETE_RECEIPT' for x in result['entries']))
        finally:
            db.close(); media.close()

    def test_casefold_alias_collision(self):
        db, media = database(), media_zip([(CANON, PDF), (CANON.upper(), PDF)])
        try:
            result = inventory_pocket_archive_readonly(db, media)
            self.assertEqual('REVIEW_REQUIRED', result['status'])
            self.assertTrue(any(x['reason'] == 'AMBIGUOUS_PATH' for x in result['entries']))
        finally:
            db.close(); media.close()

    def test_exact_zip_duplicate(self):
        db, media = database(), media_zip([(CANON, PDF), (CANON, PDF)])
        try:
            result = inventory_pocket_archive_readonly(db, media)
            self.assertEqual('REVIEW_REQUIRED', result['status'])
            self.assertTrue(any(x['reason'] == 'AMBIGUOUS_PATH' for x in result['entries']))
        finally:
            db.close(); media.close()

    def test_orphan_without_archive_table(self):
        db, media = sqlite3.connect(':memory:'), media_zip([(LEGACY, PDF)])
        try:
            result = inventory_pocket_archive_readonly(db, media)
            self.assertEqual('REVIEW_REQUIRED', result['status'])
            self.assertTrue(any(x['reason'] == 'UNLINKED_MEDIA' for x in result['entries']))
        finally:
            db.close(); media.close()
