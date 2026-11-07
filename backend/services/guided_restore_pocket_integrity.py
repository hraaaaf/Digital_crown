"""Read-only, fail-closed Pocket document/media checks for guided restore preflight.

Clinical associations are verified on a *staged* decrypted DB and an encrypted
media backup. No patient identifiers, filenames or media content leave this
function; no writes to the source, cabinet DB or restored media occur.

Only the explicit Pocket COMPLETED receipt contract is asserted here. Legacy
document archives without such receipts require a separate completeness policy.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from cryptography.fernet import InvalidToken

from backend.services.guided_restore_archive import (
    MAX_MEDIA_ARCHIVE_ENTRIES,
    _decrypt_streaming_media_archive,
    _is_streaming_media_archive,
    _master_cipher,
    _open_database_for_validation,
    _safe_zip_member,
    _validate_zip_infos,
)

_MAX_PDF_BYTES = 12 * 1024 * 1024
_GENERIC_ERROR = "Archive clinique Pocket non vérifiable : revue manuelle requise."
_LEGACY_MIRROR_TYPES = frozenset({
    "CERTIFICAT", "ORDONNANCE", "DEVIS", "NOTE_HONORAIRES",
})
_TYPES = {
    "certificat": "CERTIFICAT",
    "ordonnance": "ORDONNANCE",
    "devis": "DEVIS",
    "honoraires": "NOTE_HONORAIRES",
    "note": "NOTE_HONORAIRES",
    "libre": "DOCUMENT_LIBRE",
    "lettre": "LETTRE_MEDICALE",
}


def _deny() -> None:
    """No PHI or file paths in the HTTP-facing error message."""
    raise ValueError(_GENERIC_ERROR)


def _safe_canonical(relative: object) -> PurePosixPath:
    if not isinstance(relative, str) or not relative.startswith("static/archives/"):
        _deny()
    path = relative[len("static/"):]
    if (
        not _safe_zip_member(path)
        or PurePosixPath(path).as_posix() != path
        or len(PurePosixPath(path).parts) != 6
        or not path.lower().endswith(".pdf")
    ):
        _deny()
    return PurePosixPath(path)


def _check_pdf(zipfile_obj: zipfile.ZipFile, indexed: dict[str, zipfile.ZipInfo],
               path: PurePosixPath, expected_sha: str, expected_size: int) -> None:
    info = indexed.get(path.as_posix())
    if info is None or info.is_dir() or info.file_size != expected_size:
        _deny()
    if not 5 <= expected_size <= _MAX_PDF_BYTES:
        _deny()
    size = 0
    digest = hashlib.sha256()
    head = b""
    with zipfile_obj.open(info, "r") as media:
        for piece in iter(lambda: media.read(1024 * 1024), b""):
            if not head:
                head = piece[:5]
            size += len(piece)
            if size > _MAX_PDF_BYTES:
                _deny()
            digest.update(piece)
    if (size != expected_size or head != b"%PDF-"
            or not hmac.compare_digest(digest.hexdigest(), expected_sha)):
        _deny()


def inspect_completed_pocket_receipts_in_backup(
    decrypted_db: Path, driver: str, encrypted_media: Path | None,
) -> int:
    """Verify completed receipt -> archive -> canon+historical media; 0 if no Pocket.

    Fails closed for a non-verifiable completed receipt. PROCESSING never
    authorizes replay or pairing with orphaned media.
    """
    conn = _open_database_for_validation(decrypted_db, driver)
    expected: list[tuple[PurePosixPath, str, int, str]] = []
    try:
        conn.execute("PRAGMA query_only=ON")
        tables = {
            str(row[0]) for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "mobile_document_archive_receipts" not in tables:
            return 0
        completed = conn.execute(
            "SELECT id, tenant_id, actor_id, patient_id, archive_id, "
            "archive_sha256, document_type "
            "FROM mobile_document_archive_receipts WHERE state='COMPLETED'"
        ).fetchall()
        if not completed:
            return 0
        if encrypted_media is None or "document_archives" not in tables:
            _deny()
        seen_archive: set[int] = set()
        seen_paths: set[str] = set()
        for (_, tenant_id, actor_id, patient_id, archive_id,
             receipt_hash, receipt_type) in completed:
            if not isinstance(archive_id, int) or archive_id in seen_archive:
                _deny()
            seen_archive.add(archive_id)
            archive = conn.execute(
                "SELECT d.patient_id, d.uploaded_by_id, d.file_path, "
                "d.file_hash, d.file_size, d.document_type, d.status, "
                "p.employer_id FROM document_archives d "
                "LEFT JOIN patients p ON p.id=d.patient_id "
                "WHERE d.id=?", (archive_id,),
            ).fetchone()
            if archive is None:
                _deny()
            (doc_patient, doc_actor, file_path, doc_hash,
             file_size, doc_type, status, employer) = archive
            if (
                not isinstance(receipt_hash, str)
                or not isinstance(doc_hash, str)
                or not re.fullmatch("[a-f0-9]{64}", doc_hash)
                or not hmac.compare_digest(receipt_hash, doc_hash)
                or doc_patient != patient_id
                or doc_actor != actor_id
                or employer != tenant_id
                or doc_type != _TYPES.get(str(receipt_type))
                or status != "ACTIF"
                or not isinstance(file_size, int)
            ):
                _deny()
            path = _safe_canonical(file_path)
            # ArchiveService stores each document under
            # archives/<patient_id>/<DocumentType>/<YYYY>/<M>/filename.pdf.
            # A valid hash cannot authorize crossing a patient's directory.
            if path.parts[1] != str(doc_patient) or path.parts[2] != str(doc_type):
                _deny()
            if path.as_posix() in seen_paths:
                _deny()
            seen_paths.add(path.as_posix())
            expected.append((path, doc_hash, file_size, str(doc_type)))
    except (ValueError, TypeError):
        raise
    except Exception as exc:
        raise ValueError(_GENERIC_ERROR) from exc
    finally:
        conn.close()

    def inspect_zip(archive: zipfile.ZipFile) -> None:
        infos = archive.infolist()
        _validate_zip_infos(infos, max_entries=MAX_MEDIA_ARCHIVE_ENTRIES)
        unique: dict[str, zipfile.ZipInfo] = {}
        for info in infos:
            if not _safe_zip_member(info.filename):
                _deny()
            if info.filename != PurePosixPath(info.filename).as_posix():
                _deny()
            if not info.is_dir():
                if info.filename in unique:
                    _deny()
                unique[info.filename] = info
        checked_mirrors: set[str] = set()
        for canonical, sha, size, doc_type in expected:
            _check_pdf(archive, unique, canonical, sha, size)
            if doc_type in _LEGACY_MIRROR_TYPES:
                # ArchiveService mirrors storage_path.name into YYYY/MM;
                # SQLite has no explicit mirror index, so do not guess a
                # different patient association when this expectation fails.
                year, month = canonical.parts[-3:-1]
                if not year.isdigit() or not month.isdigit() or not 1 <= int(month) <= 12:
                    _deny()
                historical = PurePosixPath("documents") / year / f"{int(month):02d}" / canonical.name
                if historical.as_posix() in checked_mirrors:
                    _deny()
                checked_mirrors.add(historical.as_posix())
                _check_pdf(archive, unique, historical, sha, size)

    try:
        if _is_streaming_media_archive(encrypted_media):
            with tempfile.TemporaryDirectory(prefix="dc-pocket-preflight-") as folder:
                extracted_zip = Path(folder) / "staged-media.zip"
                _decrypt_streaming_media_archive(encrypted_media, extracted_zip)
                with zipfile.ZipFile(extracted_zip, "r") as archive:
                    inspect_zip(archive)
        else:
            clear = _master_cipher().decrypt(encrypted_media.read_bytes())
            with zipfile.ZipFile(io.BytesIO(clear), "r") as archive:
                inspect_zip(archive)
    except (InvalidToken, ValueError, OSError, zipfile.BadZipFile) as exc:
        raise ValueError(_GENERIC_ERROR) from exc
    return len(expected)
