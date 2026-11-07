"""Local-only, read-only diagnostic manifest for historical Pocket/DocumentArchive media.

FUE-0: accepts an already isolated SQLite/SQLCipher connection and opened ZIP.
Never writes, restores, deletes, reassigns patient ownership, or exports data.
Names and patient IDs are not included in the output: only path SHA-256 tokens.
A byte match is NOT clinical acceptance or restoration approval.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import stat
import zipfile
from pathlib import PurePosixPath

MAX_ENTRIES = 40000
MAX_PDF = 12 * 1024 * 1024
MAX_OTHER = 128 * 1024 * 1024
MEDIA_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".dcm"}
STATES = {"ACTIF", "SUPPRIME", "ARCHIVE"}


def _token(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8", errors="surrogatepass")).hexdigest()


def _safe_member(path: str) -> bool:
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path or ":" in path:
        return False
    posix = PurePosixPath(path)
    return (not posix.is_absolute() and posix.as_posix() == path
            and all(x not in {"", ".", ".."} for x in path.split("/")))


def _valid_claim(path: str, patient_id: object, document_type: object) -> bool:
    if not isinstance(path, str) or not path.startswith("static/"):
        return False
    rel = path[7:]
    if not _safe_member(rel):
        return False
    p = PurePosixPath(rel)
    if p.suffix.lower() not in MEDIA_TYPES:
        return False
    parts = p.parts
    if (len(parts) == 6 and parts[0] == "archives"
            and str(patient_id) == parts[1] and str(document_type) == parts[2]):
        year, month = parts[3:5]
    elif len(parts) == 4 and parts[0] == "documents":
        year, month = parts[1:3]
    else:
        return False
    return (len(year) == 4 and year.isdigit() and month.isdigit()
            and 1 <= int(month) <= 12)


def _digest_member(media: zipfile.ZipFile, info: zipfile.ZipInfo) -> tuple[str | None, str | None]:
    """Bounded streaming only. No extraction, no symlink traversal."""
    mode = (info.external_attr >> 16) & 0o170000
    if info.is_dir() or mode == stat.S_IFLNK:
        return None, "UNSAFE_MEMBER"
    cap = MAX_PDF if info.filename.lower().endswith(".pdf") else MAX_OTHER
    if info.file_size > cap or info.file_size < 0:
        return None, "FILE_TOO_LARGE"
    digest = hashlib.sha256()
    total = 0
    head = b""
    try:
        with media.open(info, "r") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                if not head:
                    head = chunk[:5]
                total += len(chunk)
                if total > cap:
                    return None, "FILE_TOO_LARGE"
                digest.update(chunk)
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, EOFError):
        return None, "UNREADABLE_MEMBER"
    if total != info.file_size:
        return None, "SIZE_DISAGREEMENT"
    if info.filename.lower().endswith(".pdf") and head != b"%PDF-":
        return digest.hexdigest(), "INVALID_PDF_HEADER"
    return digest.hexdigest(), None


def inventory_pocket_archive_readonly(db, media: zipfile.ZipFile) -> dict:
    """Build an in-memory manifest; caller protects it in the cabinet.

    Only SELECT queries and streaming ZIP reads. Do not treat as a restore
    preflight substitute. Unsupported names and unlinked bytes require humans.
    """
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    records: list[dict] = []
    infos = media.infolist()
    if len(infos) > MAX_ENTRIES:
        return {"status": "REVIEW_REQUIRED", "entries": [], "reason": "ENTRY_LIMIT"}
    by_name: dict[str, zipfile.ZipInfo] = {}
    collisions: set[str] = set()
    for info in infos:
        if info.is_dir():
            continue
        folded = info.filename.casefold()
        if not _safe_member(info.filename) or folded in by_name:
            collisions.add(folded)
        else:
            by_name[folded] = info
    claimed: set[str] = set()
    if "document_archives" not in tables:
        records.append({"source": "SQL", "status": "REVIEW_REQUIRED",
                        "reason": "NO_ARCHIVE_TABLE"})
    if "document_archives" in tables:
        sql = ("SELECT id, patient_id, document_type, file_path, file_hash, file_size, status "
               "FROM document_archives ORDER BY id")
        for doc_id, patient_id, document_type, raw_path, expected_sha, expected_size, state in db.execute(sql):
            relative = raw_path[7:] if isinstance(raw_path, str) and raw_path.startswith("static/") else ""
            folded = relative.casefold()
            item = {"source": "SQL", "archive_row": doc_id,
                    "path_sha256": _token(raw_path if isinstance(raw_path, str) else "<null>"),
                    "expected_sha256": expected_sha if isinstance(expected_sha, str) else None,
                    "expected_size": expected_size if isinstance(expected_size, int) else None,
                    "actual_sha256": None, "actual_size": None,
                    "document_status": state, "status": "REVIEW_REQUIRED", "reason": None}
            if not _valid_claim(raw_path, patient_id, document_type):
                item["reason"] = "UNSUPPORTED_SQL_PATH"
            elif folded in claimed or folded in collisions:
                item["reason"] = "AMBIGUOUS_PATH"
            else:
                claimed.add(folded)
                info = by_name.get(folded)
                if info is None:
                    item["reason"] = "MISSING_MEDIA"
                elif info.filename != relative:
                    item["reason"] = "CASE_ALIAS"
                else:
                    actual, problem = _digest_member(media, info)
                    item["actual_sha256"] = actual
                    item["actual_size"] = info.file_size
                    if problem:
                        item["reason"] = problem
                    elif (state not in STATES or not isinstance(expected_sha, str)
                          or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None
                          or not isinstance(expected_size, int)):
                        item["reason"] = "BAD_SQL_METADATA"
                    elif expected_size != info.file_size:
                        item["reason"] = "SIZE_MISMATCH"
                    elif not hmac.compare_digest(expected_sha, actual or ""):
                        item["reason"] = "SHA256_MISMATCH"
                    else:
                        item["status"] = "MATCHED"
            records.append(item)
    if "mobile_document_archive_receipts" in tables:
        for row_id, state in db.execute("SELECT id, state FROM mobile_document_archive_receipts ORDER BY id"):
            if state != "COMPLETED":
                records.append({"source": "RECEIPT", "archive_row": None,
                                "path_sha256": None, "expected_sha256": None,
                                "actual_sha256": None, "status": "REVIEW_REQUIRED",
                                "reason": "INCOMPLETE_RECEIPT", "receipt_row": row_id})
    for folded, info in sorted(by_name.items()):
        if not info.filename.startswith(("archives/", "documents/")) or folded in claimed:
            continue
        if folded in collisions:
            reason = "AMBIGUOUS_ZIP_MEMBER"
            actual = None
        else:
            actual, reason = _digest_member(media, info)
            reason = reason or "UNLINKED_MEDIA"
        records.append({"source": "ZIP", "archive_row": None,
                        "path_sha256": _token(info.filename), "expected_sha256": None,
                        "actual_sha256": actual, "size": info.file_size,
                        "status": "REVIEW_REQUIRED", "reason": reason})
    for folded in sorted(collisions):
        records.append({"source": "ZIP", "archive_row": None,
                        "path_sha256": _token(folded), "expected_sha256": None,
                        "actual_sha256": None, "status": "REVIEW_REQUIRED",
                        "reason": "AMBIGUOUS_OR_UNSAFE_MEMBER"})
    review = any(r["status"] != "MATCHED" for r in records)
    return {"status": "REVIEW_REQUIRED" if review
            else "BYTE_INVENTORY_MATCHED_NOT_RESTORE_APPROVED", "entries": records,
            "reason": "LOCAL_OPERATOR_REVIEW_REQUIRED" if review else None}
