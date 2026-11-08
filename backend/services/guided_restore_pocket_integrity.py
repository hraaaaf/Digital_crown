"""Fail-closed, read-only staged restore integrity for DocumentArchive and Pocket.

This is an experimental security patch: no production clinical data, no
restoration apply, replay, deletion or reclassification of uncertain receipts.
The only error returned to users is generic; no PHI or clinical path leaks.
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

_GENERIC_ERROR = "Archive clinique Pocket non vérifiable : revue manuelle requise."
_MAX_DOCUMENT_BYTES = 128 * 1024 * 1024
_MAX_PDF_BYTES = 12 * 1024 * 1024
_MIRRORED = {"CERTIFICAT", "ORDONNANCE", "DEVIS", "NOTE_HONORAIRES"}
_TYPES = {
    "certificat": "CERTIFICAT",
    "ordonnance": "ORDONNANCE",
    "devis": "DEVIS",
    "honoraires": "NOTE_HONORAIRES",
    "note": "NOTE_HONORAIRES",
    "libre": "DOCUMENT_LIBRE",
    "lettre": "LETTRE_MEDICALE",
}
_ALLOWED_STATES = {"ACTIF", "SUPPRIME", "ARCHIVE"}


def _deny() -> None:
    raise ValueError(_GENERIC_ERROR)


def _safe_document_path(value: object, patient_id: int, document_type: str) -> PurePosixPath:
    """Only a bounded local media path, never an absolute/ambiguous ZIP member."""
    if not isinstance(value, str) or not value.startswith("static/"):
        _deny()
    relative = value[len("static/"):]
    path = PurePosixPath(relative)
    if (
        not _safe_zip_member(relative)
        or path.as_posix() != relative
        or any(":" in part for part in path.parts)
    ):
        _deny()
    if path.parts[0] == "archives":
        if (len(path.parts) != 6 or path.parts[1] != str(patient_id)
                or path.parts[2] != document_type):
            _deny()
    elif path.parts[0] == "documents":
        # Genuine older DocumentArchive rows may point at this unscoped tree.
        # Their SHA+size+path uniqueness is checked, never guessed by patient name.
        if len(path.parts) != 4 or not path.parts[1].isdigit():
            _deny()
    else:
        # Unknown media mappings require human review, not silent acceptance.
        _deny()
    if path.suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".dcm"}:
        _deny()
    return path


def _verify_member(z: zipfile.ZipFile, members: dict[str, zipfile.ZipInfo],
                   path: PurePosixPath, digest: str, size: int) -> None:
    info = members.get(path.as_posix())
    if info is None or info.is_dir() or info.file_size != size:
        _deny()
    limit = _MAX_PDF_BYTES if path.suffix.lower() == ".pdf" else _MAX_DOCUMENT_BYTES
    if not 5 <= size <= limit:
        _deny()
    actual = hashlib.sha256()
    total = 0
    prefix = b""
    with z.open(info) as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            if not prefix:
                prefix = chunk[:5]
            total += len(chunk)
            if total > limit:
                _deny()
            actual.update(chunk)
    if (total != size
            or (path.suffix.lower() == ".pdf" and prefix != b"%PDF-")
            or not hmac.compare_digest(actual.hexdigest(), digest)):
        _deny()


def inspect_completed_pocket_receipts_in_backup(
    decrypted_db: Path, driver: str, encrypted_media: Path | None,
) -> int:
    """Read-only audit of ALL DocumentArchive records and all receipt states.

    An unresolved PROCESSING or REVIEW_REQUIRED receipt mandates human review.
    Legacy records without receipts must have unambiguous, hashed media.
    Files in archives/documents absent from the SQL inventory are orphaned and
    stop restore; no inference, auto-replay, or file deletion is performed.
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
        receipt_table = "mobile_document_archive_receipts" in tables
        archive_table = "document_archives" in tables
        completed_by_id: dict[int, tuple[int, int, int, str, str]] = {}
        if receipt_table:
            records = conn.execute(
                "SELECT tenant_id, actor_id, patient_id, archive_id, "
                "archive_sha256, document_type, state "
                "FROM mobile_document_archive_receipts"
            )
            for tenant_id, actor_id, patient_id, archive_id, sha, kind, state in records:
                if state != "COMPLETED":
                    # A PROCESSING receipt can have an uncommitted PDF. There is
                    # no safe deterministic patient/file pairing for auto-restore.
                    _deny()
                if not isinstance(archive_id, int) or archive_id in completed_by_id:
                    _deny()
                completed_by_id[archive_id] = (tenant_id, actor_id, patient_id, sha, kind)
        if not archive_table:
            if completed_by_id:
                _deny()
        else:
            rows = conn.execute(
                "SELECT d.id, d.patient_id, d.uploaded_by_id, d.file_path, "
                "d.file_hash, d.file_size, d.document_type, d.status, "
                "p.employer_id FROM document_archives d "
                "LEFT JOIN patients p ON p.id=d.patient_id"
            )
            seen_paths: set[str] = set()
            for (doc_id, patient_id, actor_id, file_path, sha, size,
                 document_type, status, tenant_id) in rows:
                if (not isinstance(doc_id, int) or not isinstance(patient_id, int)
                        or tenant_id is None or status not in _ALLOWED_STATES
                        or not isinstance(sha, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", sha)
                        or not isinstance(size, int)):
                    _deny()
                receipt = completed_by_id.pop(doc_id, None)
                if receipt is not None:
                    rt, ra, rp, rh, kind = receipt
                    if (rt != tenant_id or ra != actor_id or rp != patient_id
                            or document_type != _TYPES.get(str(kind))
                            or not isinstance(rh, str)
                            or not hmac.compare_digest(rh, sha)):
                        _deny()
                path = _safe_document_path(file_path, patient_id, str(document_type))
                if path.as_posix().casefold() in seen_paths:
                    _deny()
                seen_paths.add(path.as_posix().casefold())
                expected.append((path, sha, size, str(document_type)))
        if completed_by_id:
            _deny()
    except (ValueError, TypeError):
        raise
    except Exception as exc:
        raise ValueError(_GENERIC_ERROR) from exc
    finally:
        conn.close()

    if expected and encrypted_media is None:
        _deny()

    def check_media(z: zipfile.ZipFile) -> None:
        infos = z.infolist()
        _validate_zip_infos(infos, max_entries=MAX_MEDIA_ARCHIVE_ENTRIES)
        by_name = {info.filename: info for info in infos if not info.is_dir()}
        claimed: dict[str, tuple[str, int]] = {}
        for path, sha, size, kind in expected:
            _verify_member(z, by_name, path, sha, size)
            claimed[path.as_posix().casefold()] = (sha, size)
            if path.parts[0] == "archives" and kind in _MIRRORED:
                year, month = path.parts[-3:-1]
                if not year.isdigit() or not month.isdigit() or not 1 <= int(month) <= 12:
                    _deny()
                mirror = PurePosixPath("documents") / year / f"{int(month):02d}" / path.name
                previous = claimed.get(mirror.as_posix().casefold())
                if previous is not None:
                    # Shared historical namespace is not proof of ownership.
                    _deny()
                _verify_member(z, by_name, mirror, sha, size)
                claimed[mirror.as_posix().casefold()] = (sha, size)
        # Inventory includes unlinked historical and canonical files, even
        # when ZERO Pocket receipts exist. No patient names/paths are logged.
        for name in by_name:
            if name.startswith(("archives/", "documents/")):
                if name.casefold() not in claimed:
                    _deny()

    if encrypted_media is not None:
        try:
            if _is_streaming_media_archive(encrypted_media):
                with tempfile.TemporaryDirectory(prefix="dc-restore-inventory-") as folder:
                    clear_zip = Path(folder) / "media.zip"
                    _decrypt_streaming_media_archive(encrypted_media, clear_zip)
                    with zipfile.ZipFile(clear_zip) as z:
                        check_media(z)
            else:
                decoded = _master_cipher().decrypt(encrypted_media.read_bytes())
                with zipfile.ZipFile(io.BytesIO(decoded)) as z:
                    check_media(z)
        except (InvalidToken, ValueError, OSError, zipfile.BadZipFile) as exc:
            raise ValueError(_GENERIC_ERROR) from exc
    return len(expected)
