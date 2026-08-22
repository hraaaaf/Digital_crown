from __future__ import annotations

import hashlib
import io
import os
import shutil
import sqlite3
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from cryptography.fernet import InvalidToken

from backend.services.backup_service import BackupService

MAX_ARCHIVE_ENTRIES = 8
MAX_MEDIA_ARCHIVE_ENTRIES = int(os.environ.get("GUIDED_RESTORE_MAX_MEDIA_ENTRIES", "250000"))
MAX_ARCHIVE_UNCOMPRESSED_BYTES = int(
    os.environ.get("GUIDED_RESTORE_MAX_UNCOMPRESSED_BYTES", str(20 * 1024**3))
)

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_job_id(value: str) -> str:
    try:
        return uuid.UUID(value).hex
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("Identifiant de restauration invalide") from exc


def _safe_zip_member(name: str) -> bool:
    if not name or "\\" in name or "\x00" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    first = path.parts[0] if path.parts else ""
    if ":" in first:
        return False
    return True


def _validate_zip_infos(infos: list[zipfile.ZipInfo], *, max_entries: int = MAX_ARCHIVE_ENTRIES) -> None:
    if not infos or len(infos) > max_entries:
        raise ValueError("Archive non reconnue ou trop complexe")
    total = 0
    for info in infos:
        if not _safe_zip_member(info.filename):
            raise ValueError("Archive refusée : chemin interne non sûr")
        # Unix symlink bit in external attributes. Never follow links from a backup.
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise ValueError("Archive refusée : lien symbolique interdit")
        total += int(info.file_size)
        if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise ValueError("Archive refusée : contenu décompressé trop volumineux")


def _sqlite_integrity(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        if not row or str(row[0]).lower() != "ok":
            raise ValueError("Intégrité SQLite invalide")
    finally:
        conn.close()


def _validate_database_file(path: Path, driver: str) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise ValueError("Sauvegarde base de données vide")
    if driver == "pysqlcipher":
        from backend.database import engine as active_engine

        passphrase = BackupService._sqlcipher_passphrase(active_engine)
        BackupService._verify_sqlcipher_file(path, passphrase)
    else:
        _sqlite_integrity(path)


def _decrypt_backup_key(source: Path, target: Path) -> None:
    cipher = BackupService._get_or_create_key()
    try:
        decrypted = cipher.decrypt(source.read_bytes())
    except InvalidToken as exc:
        raise ValueError("Sauvegarde chiffrée invalide ou clé locale incompatible") from exc
    if not decrypted:
        raise ValueError("Sauvegarde déchiffrée vide")
    target.write_bytes(decrypted)


def _master_cipher():
    from backend.scripts.backup_db import get_cipher

    try:
        return get_cipher()
    except SystemExit as exc:
        raise ValueError("Clé maître cabinet indisponible") from exc


def _inspect_encrypted_media(source: Path) -> int:
    try:
        decrypted = _master_cipher().decrypt(source.read_bytes())
    except InvalidToken as exc:
        raise ValueError("Archive média chiffrée invalide ou clé cabinet incompatible") from exc
    with zipfile.ZipFile(io.BytesIO(decrypted), "r") as media_zip:
        infos = media_zip.infolist()
        _validate_zip_infos(infos, max_entries=MAX_MEDIA_ARCHIVE_ENTRIES)
        return len([info for info in infos if not info.is_dir()])


def _extract_encrypted_media(source: Path, destination: Path) -> None:
    try:
        decrypted = _master_cipher().decrypt(source.read_bytes())
    except InvalidToken as exc:
        raise RuntimeError("Impossible de déchiffrer les médias restaurés") from exc
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(decrypted), "r") as media_zip:
        infos = media_zip.infolist()
        _validate_zip_infos(infos, max_entries=MAX_MEDIA_ARCHIVE_ENTRIES)
        for info in infos:
            target = destination / PurePosixPath(info.filename)
            target_resolved = target.resolve(strict=False)
            try:
                target_resolved.relative_to(destination.resolve())
            except ValueError as exc:
                raise RuntimeError("Chemin média hors destination") from exc
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with media_zip.open(info, "r") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)

