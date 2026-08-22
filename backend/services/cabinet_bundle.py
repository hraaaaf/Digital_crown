from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from backend.core.media_paths import get_media_root
from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter
from backend.services.backup_service import BackupService
from backend.services.guided_restore_archive import (
    MAX_ARCHIVE_UNCOMPRESSED_BYTES,
    MAX_MEDIA_ARCHIVE_ENTRIES,
    _encrypt_streaming_media_archive,
    _sha256,
    _validate_database_file,
    _validate_zip_infos,
)

BUNDLE_FORMAT = "digital-crown-cabinet-bundle"
BUNDLE_VERSION = 1
PAYLOAD_FORMAT = "digital-crown-cabinet-payload"
PAYLOAD_VERSION = 1
KDF_NAME = "scrypt"
KDF_N = 2**17
KDF_R = 8
KDF_P = 1
SALT_BYTES = 16
NONCE_BYTES = 12
TAG_BYTES = 16
CHUNK_BYTES = 1024 * 1024
MAX_PORTABLE_UPLOAD_BYTES = int(
    os.environ.get("DIGITALCROWN_MAX_PORTABLE_BUNDLE_BYTES", str(20 * 1024**3))
)
EXCLUDED_MACHINE_BOUND = (
    ".env",
    "backup.key",
    "license_vault.bin",
    "runtime locks",
    "logs",
    "caches",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _b64e(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64d(value: str, field: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:
        raise ValueError(f"Manifest bundle invalide : {field}") from exc


def _validate_migration_secret(secret: str) -> bytes:
    normalized = secret.strip()
    encoded = normalized.encode("utf-8")
    if len(encoded) < 16:
        raise ValueError("Phrase de migration trop courte : 16 caractères minimum")
    if len(encoded) > 1024:
        raise ValueError("Phrase de migration trop longue")
    return encoded


def _derive_key(secret: str, salt: bytes, *, n: int = KDF_N, r: int = KDF_R, p: int = KDF_P) -> bytes:
    material = _validate_migration_secret(secret)
    if n != KDF_N or r != KDF_R or p != KDF_P:
        raise ValueError("Paramètres scrypt non supportés")
    return Scrypt(salt=salt, length=32, n=n, r=r, p=p).derive(material)


def _stream_encrypt(source: Path, target: Path, *, key: bytes, nonce: bytes, aad: bytes) -> bytes:
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(aad)
    with source.open("rb") as src, target.open("wb") as dst:
        for chunk in iter(lambda: src.read(CHUNK_BYTES), b""):
            dst.write(encryptor.update(chunk))
        dst.write(encryptor.finalize())
    return bytes(encryptor.tag)


def _stream_decrypt(source: Path, target: Path, *, key: bytes, nonce: bytes, tag: bytes, aad: bytes) -> None:
    if len(tag) != TAG_BYTES:
        raise ValueError("Tag AES-GCM invalide")
    decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
    decryptor.authenticate_additional_data(aad)
    try:
        with source.open("rb") as src, target.open("wb") as dst:
            for chunk in iter(lambda: src.read(CHUNK_BYTES), b""):
                dst.write(decryptor.update(chunk))
            dst.write(decryptor.finalize())
    except InvalidTag as exc:
        target.unlink(missing_ok=True)
        raise ValueError("Phrase de migration incorrecte ou bundle altéré") from exc
    except Exception:
        target.unlink(missing_ok=True)
        raise


def _copy_sqlite_snapshot(source: Path, target: Path) -> None:
    target.unlink(missing_ok=True)
    src_conn = sqlite3.connect(str(source))
    dst_conn = sqlite3.connect(str(target))
    try:
        src_conn.backup(dst_conn)
        user_version = int(src_conn.execute("PRAGMA user_version").fetchone()[0])
        dst_conn.execute(f"PRAGMA user_version = {user_version}")
        dst_conn.commit()
    finally:
        dst_conn.close()
        src_conn.close()


def _export_sqlcipher_plaintext(source: Path, target: Path, passphrase: str) -> None:
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError as exc:
        raise RuntimeError("sqlcipher3 indisponible") from exc
    target.unlink(missing_ok=True)
    conn = sqlcipher.connect(str(source))
    attached = False
    try:
        safe_key = passphrase.replace("'", "''")
        safe_target = str(target).replace("'", "''")
        conn.execute(f"PRAGMA key = '{safe_key}'")
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        conn.execute(f"ATTACH DATABASE '{safe_target}' AS portable KEY ''")
        attached = True
        conn.execute("SELECT sqlcipher_export('portable')")
        conn.execute(f"PRAGMA portable.user_version = {user_version}")
        conn.commit()
        conn.execute("DETACH DATABASE portable")
        attached = False
    finally:
        if attached:
            try:
                conn.execute("DETACH DATABASE portable")
            except Exception:
                pass
        conn.close()
    _validate_database_file(target, "pysqlite")


def _encrypt_plaintext_sqlcipher(source: Path, target: Path, passphrase: str) -> None:
    target.unlink(missing_ok=True)
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError as exc:
        raise RuntimeError("sqlcipher3 indisponible") from exc
    conn = sqlcipher.connect(str(source))
    attached = False
    try:
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        safe_target = str(target).replace("'", "''")
        safe_key = passphrase.replace("'", "''")
        conn.execute(f"ATTACH DATABASE '{safe_target}' AS encrypted KEY '{safe_key}'")
        attached = True
        conn.execute("SELECT sqlcipher_export('encrypted')")
        conn.execute(f"PRAGMA encrypted.user_version = {user_version}")
        conn.commit()
        conn.execute("DETACH DATABASE encrypted")
        attached = False
    finally:
        if attached:
            try:
                conn.execute("DETACH DATABASE encrypted")
            except Exception:
                pass
        conn.close()
    BackupService._verify_sqlcipher_file(target, passphrase)


def _encrypt_plaintext_for_active_database(source: Path, target: Path, driver: str) -> None:
    target.unlink(missing_ok=True)
    if driver != "pysqlcipher":
        _copy_sqlite_snapshot(source, target)
        _validate_database_file(target, "pysqlite")
        return
    from backend.database import engine as active_engine
    passphrase = BackupService._sqlcipher_passphrase(active_engine)
    _encrypt_plaintext_sqlcipher(source, target, passphrase)


def _snapshot_active_database(target: Path) -> tuple[str, str]:
    from backend.database import engine as active_engine
    dialect = str(active_engine.dialect.name)
    driver = str(active_engine.driver)
    if dialect != "sqlite":
        raise RuntimeError("Le bundle cabinet portable requiert le runtime SQLite/SQLCipher du cabinet")
    database = active_engine.url.database
    if not database or database == ":memory:":
        raise RuntimeError("Base cabinet sur disque introuvable")
    source = Path(str(database))
    if not source.exists():
        raise RuntimeError("Base cabinet introuvable")
    if driver == "pysqlcipher":
        passphrase = BackupService._sqlcipher_passphrase(active_engine)
        _export_sqlcipher_plaintext(source, target, passphrase)
    else:
        _copy_sqlite_snapshot(source, target)
        _validate_database_file(target, "pysqlite")
    return dialect, driver


def _create_media_zip(media_root: Path, target: Path) -> tuple[int, int]:
    media_root = media_root.resolve(strict=False)
    if not media_root.exists():
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED):
            pass
        return 0, 0
    if not media_root.is_dir():
        raise ValueError("Racine média invalide")
    files = sorted((p for p in media_root.rglob("*") if p.is_file()), key=lambda p: p.as_posix())
    if len(files) > MAX_MEDIA_ARCHIVE_ENTRIES:
        raise ValueError("Arborescence média trop volumineuse")
    total = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for path in files:
            if path.is_symlink():
                raise ValueError("Lien symbolique média interdit")
            relative = path.relative_to(media_root).as_posix()
            size = path.stat().st_size
            total += size
            if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError("Médias trop volumineux pour un bundle cabinet")
            archive.write(path, relative)
    return len(files), total


def _safe_config() -> dict[str, Any]:
    raw_port = os.environ.get("CABINET_PORT", "8005").strip()
    try:
        port = int(raw_port)
    except ValueError:
        port = 8005
    if not 1 <= port <= 65535:
        port = 8005
    return {
        "version": 1,
        "portable_runtime_preferences": {"cabinet_port": port},
        "destination_policy": {
            "runtime_secrets": "regenerate",
            "allowed_origins": "recompute",
            "license": "rebind",
            "network_identity": "preserve_destination",
        },
    }


def _bundle_header(*, salt: bytes, nonce: bytes) -> dict[str, Any]:
    adapter = get_platform_adapter()
    return {
        "format": BUNDLE_FORMAT,
        "version": BUNDLE_VERSION,
        "created_at": _utc_now(),
        "source": {"os": adapter.kind, "architecture": adapter.architecture},
        "kdf": {"name": KDF_NAME, "salt_b64": _b64e(salt), "n": KDF_N, "r": KDF_R, "p": KDF_P, "length": 32},
        "cipher": {"name": "AES-256-GCM", "nonce_b64": _b64e(nonce), "tag_bytes": TAG_BYTES},
        "machine_bound_excluded": list(EXCLUDED_MACHINE_BOUND),
    }


def _parse_bundle_manifest(manifest: dict[str, Any]) -> tuple[dict[str, Any], bytes, bytes, bytes]:
    if manifest.get("format") != BUNDLE_FORMAT or int(manifest.get("version", 0)) != BUNDLE_VERSION:
        raise ValueError("Format de bundle cabinet incompatible")
    kdf = manifest.get("kdf") or {}
    cipher = manifest.get("cipher") or {}
    if kdf.get("name") != KDF_NAME or cipher.get("name") != "AES-256-GCM":
        raise ValueError("Paramètres cryptographiques du bundle non supportés")
    n, r, p = int(kdf.get("n", 0)), int(kdf.get("r", 0)), int(kdf.get("p", 0))
    if (n, r, p) != (KDF_N, KDF_R, KDF_P) or int(kdf.get("length", 0)) != 32:
        raise ValueError("Paramètres scrypt non supportés")
    if int(cipher.get("tag_bytes", 0)) != TAG_BYTES:
        raise ValueError("Tag AES-GCM non supporté")
    salt = _b64d(str(kdf.get("salt_b64") or ""), "salt")
    nonce = _b64d(str(cipher.get("nonce_b64") or ""), "nonce")
    tag = _b64d(str(cipher.get("tag_b64") or ""), "tag")
    if len(salt) != SALT_BYTES or len(nonce) != NONCE_BYTES or len(tag) != TAG_BYTES:
        raise ValueError("Paramètres cryptographiques du bundle invalides")
    header = json.loads(json.dumps(manifest))
    header["cipher"].pop("tag_b64", None)
    header.pop("payload_sha256", None)
    return header, salt, nonce, tag


def _validate_inner_payload(payload_zip: Path, workdir: Path) -> dict[str, Any]:
    with zipfile.ZipFile(payload_zip, "r") as archive:
        infos = archive.infolist()
        _validate_zip_infos(infos, max_entries=8)
        names = {info.filename for info in infos if not info.is_dir()}
        required = {"payload-manifest.json", "database.sqlite", "config.json"}
        if not required.issubset(names):
            raise ValueError("Payload cabinet incomplet")
        if any(name not in required | {"media.zip"} for name in names):
            raise ValueError("Payload cabinet contient des entrées inconnues")
        payload_manifest = json.loads(archive.read("payload-manifest.json").decode("utf-8"))
        if payload_manifest.get("format") != PAYLOAD_FORMAT or int(payload_manifest.get("version", 0)) != PAYLOAD_VERSION:
            raise ValueError("Version du payload cabinet incompatible")
        db_path = workdir / "database.sqlite"
        with archive.open("database.sqlite") as src, db_path.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=CHUNK_BYTES)
        db_meta = payload_manifest.get("database") or {}
        if _sha256(db_path) != str(db_meta.get("sha256") or ""):
            raise ValueError("Checksum DB portable invalide")
        _validate_database_file(db_path, "pysqlite")
        config_bytes = archive.read("config.json")
        config_meta = payload_manifest.get("config") or {}
        if hashlib.sha256(config_bytes).hexdigest() != str(config_meta.get("sha256") or ""):
            raise ValueError("Checksum configuration portable invalide")
        config = json.loads(config_bytes.decode("utf-8"))
        if not isinstance(config, dict) or int(config.get("version", 0)) != 1:
            raise ValueError("Configuration portable invalide")
        media_path = None
        media_count = 0
        media_meta = payload_manifest.get("media") or {}
        if bool(media_meta.get("included")):
            if "media.zip" not in names:
                raise ValueError("Archive média portable absente")
            media_path = workdir / "media.zip"
            with archive.open("media.zip") as src, media_path.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=CHUNK_BYTES)
            if _sha256(media_path) != str(media_meta.get("sha256") or ""):
                raise ValueError("Checksum médias portables invalide")
            with zipfile.ZipFile(media_path, "r") as media_zip:
                media_infos = media_zip.infolist()
                _validate_zip_infos(media_infos, max_entries=MAX_MEDIA_ARCHIVE_ENTRIES)
                media_count = len([info for info in media_infos if not info.is_dir()])
        elif "media.zip" in names:
            raise ValueError("Payload média incohérent")
    return {"database": db_path, "media": media_path, "media_file_count": media_count, "config": config}


class CabinetBundleService:
    @staticmethod
    def create_bundle(target: Path, migration_secret: str, *, database_path: Path | None = None, media_root: Path | None = None) -> dict[str, Any]:
        _validate_migration_secret(migration_secret)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.unlink(missing_ok=True)
        bundle_tmp = target.parent / f".tmp-{uuid.uuid4().hex}-{target.name}"
        bundle_tmp.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix="digitalcrown-portable-export-") as temp_name:
            workdir = Path(temp_name)
            portable_db = workdir / "database.sqlite"
            if database_path is None:
                dialect, driver = _snapshot_active_database(portable_db)
            else:
                _copy_sqlite_snapshot(database_path, portable_db)
                _validate_database_file(portable_db, "pysqlite")
                dialect, driver = "sqlite", "pysqlite"
            media_zip = workdir / "media.zip"
            media_count, media_bytes = _create_media_zip(media_root or get_media_root(), media_zip)
            config_bytes = _canonical_json(_safe_config())
            check_conn = sqlite3.connect(str(portable_db))
            try:
                user_version = int(check_conn.execute("PRAGMA user_version").fetchone()[0])
            finally:
                check_conn.close()
            payload_manifest = {
                "format": PAYLOAD_FORMAT,
                "version": PAYLOAD_VERSION,
                "created_at": _utc_now(),
                "database": {"filename": "database.sqlite", "engine": dialect, "source_driver": driver, "sha256": _sha256(portable_db), "user_version": user_version},
                "media": {"included": media_count > 0, "filename": "media.zip" if media_count > 0 else None, "sha256": _sha256(media_zip) if media_count > 0 else None, "file_count": media_count, "uncompressed_bytes": media_bytes},
                "config": {"filename": "config.json", "sha256": hashlib.sha256(config_bytes).hexdigest()},
            }
            payload_zip = workdir / "payload.zip"
            with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_STORED, allowZip64=True) as payload:
                payload.writestr("payload-manifest.json", _canonical_json(payload_manifest))
                payload.write(portable_db, "database.sqlite")
                payload.writestr("config.json", config_bytes)
                if media_count > 0:
                    payload.write(media_zip, "media.zip")
            salt = os.urandom(SALT_BYTES)
            nonce = os.urandom(NONCE_BYTES)
            header = _bundle_header(salt=salt, nonce=nonce)
            key = _derive_key(migration_secret, salt)
            ciphertext = workdir / "payload.enc"
            tag = _stream_encrypt(payload_zip, ciphertext, key=key, nonce=nonce, aad=_canonical_json(header))
            manifest = json.loads(json.dumps(header))
            manifest["cipher"]["tag_b64"] = _b64e(tag)
            manifest["payload_sha256"] = _sha256(ciphertext)
            try:
                with zipfile.ZipFile(bundle_tmp, "w", zipfile.ZIP_STORED, allowZip64=True) as bundle:
                    bundle.writestr("manifest.json", _canonical_json(manifest))
                    bundle.write(ciphertext, "payload.enc")
                os.replace(bundle_tmp, target)
                if not get_platform_adapter().is_windows:
                    target.chmod(0o600)
            finally:
                bundle_tmp.unlink(missing_ok=True)
        return {"path": target, "filename": target.name, "size_bytes": target.stat().st_size, "sha256": _sha256(target), "media_file_count": media_count, "source_os": header["source"]["os"], "source_architecture": header["source"]["architecture"]}

    @staticmethod
    def export_active_cabinet(migration_secret: str) -> dict[str, Any]:
        export_dir = AppPaths.get_user_data_dir() / "exports"
        get_platform_adapter().ensure_private_directory(export_dir)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = export_dir / f"digital-crown-cabinet-{stamp}-{uuid.uuid4().hex[:8]}.dcbundle"
        return CabinetBundleService.create_bundle(target, migration_secret)

    @staticmethod
    def to_local_guided_restore_archive(bundle_path: Path, migration_secret: str, target_archive: Path, *, active_engine: tuple[str, str] | None = None) -> dict[str, Any]:
        _validate_migration_secret(migration_secret)
        if not bundle_path.exists() or bundle_path.stat().st_size <= 0:
            raise ValueError("Bundle cabinet vide ou introuvable")
        if bundle_path.stat().st_size > MAX_PORTABLE_UPLOAD_BYTES:
            raise ValueError("Bundle cabinet trop volumineux")
        with tempfile.TemporaryDirectory(prefix="digitalcrown-portable-import-") as temp_name:
            workdir = Path(temp_name)
            with zipfile.ZipFile(bundle_path, "r") as bundle:
                infos = bundle.infolist()
                _validate_zip_infos(infos, max_entries=4)
                names = {info.filename for info in infos if not info.is_dir()}
                if names != {"manifest.json", "payload.enc"}:
                    raise ValueError("Bundle cabinet non reconnu")
                manifest = json.loads(bundle.read("manifest.json").decode("utf-8"))
                header, salt, nonce, tag = _parse_bundle_manifest(manifest)
                ciphertext = workdir / "payload.enc"
                with bundle.open("payload.enc") as src, ciphertext.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=CHUNK_BYTES)
            expected_sha = str(manifest.get("payload_sha256") or "")
            if not expected_sha or _sha256(ciphertext) != expected_sha:
                raise ValueError("Checksum du payload chiffré invalide")
            key = _derive_key(migration_secret, salt, n=int(manifest["kdf"]["n"]), r=int(manifest["kdf"]["r"]), p=int(manifest["kdf"]["p"]))
            payload_zip = workdir / "payload.zip"
            _stream_decrypt(ciphertext, payload_zip, key=key, nonce=nonce, tag=tag, aad=_canonical_json(header))
            parsed = _validate_inner_payload(payload_zip, workdir)
            if active_engine is None:
                active_engine = BackupService._detect_engine()
            dialect, driver = active_engine
            if dialect != "sqlite":
                raise ValueError("Destination incompatible : runtime SQLite/SQLCipher requis")
            local_db = workdir / "database.local"
            if (dialect, driver) == ("sqlite", "pysqlite"):
                _copy_sqlite_snapshot(parsed["database"], local_db)
                _validate_database_file(local_db, "pysqlite")
            else:
                _encrypt_plaintext_for_active_database(parsed["database"], local_db, driver)
            local_db_enc = workdir / "database.db.enc"
            local_db_enc.write_bytes(BackupService._get_or_create_key().encrypt(local_db.read_bytes()))
            media_path = parsed["media"]
            local_media_enc = None
            media_encryption = None
            if media_path is not None:
                local_media_enc = workdir / "media.zip.enc"
                _encrypt_streaming_media_archive(media_path, local_media_enc)
                media_encryption = "master_key"
            restore_manifest = {
                "format": "digital-crown-guided-restore",
                "version": 1,
                "created_at": manifest.get("created_at"),
                "database": {"filename": "database.db.enc", "sha256": _sha256(local_db_enc), "encryption": "backup_key", "engine": "sqlite"},
                "media": {"included": local_media_enc is not None, "filename": "media.zip.enc" if local_media_enc is not None else "", "sha256": _sha256(local_media_enc) if local_media_enc is not None else "", "encryption": media_encryption, "storage_format": "aesgcm-stream-v1" if local_media_enc is not None else None},
                "portable": {"source": manifest.get("source"), "config": parsed["config"], "machine_bound_excluded": manifest.get("machine_bound_excluded") or []},
            }
            target_archive.parent.mkdir(parents=True, exist_ok=True)
            target_archive.unlink(missing_ok=True)
            with zipfile.ZipFile(target_archive, "w", zipfile.ZIP_STORED, allowZip64=True) as restore:
                restore.writestr("manifest.json", _canonical_json(restore_manifest))
                restore.write(local_db_enc, "database.db.enc")
                if local_media_enc is not None:
                    restore.write(local_media_enc, "media.zip.enc")
        return {"path": target_archive, "source": manifest.get("source"), "media_file_count": int(parsed["media_file_count"]), "config": parsed["config"], "machine_bound_excluded": list(manifest.get("machine_bound_excluded") or [])}

    @staticmethod
    async def preflight_upload(upload, migration_secret: str, *, owner_employer_id: int | None = None) -> dict[str, Any]:
        from backend.services.guided_restore import GuidedRestoreService
        temp_root = AppPaths.get_user_data_dir() / "portable-imports"
        get_platform_adapter().ensure_private_directory(temp_root)
        token = uuid.uuid4().hex
        source = temp_root / f"{token}.dcbundle"
        local_restore = temp_root / f"{token}.guided-restore.zip"
        size = 0
        try:
            with source.open("wb") as target:
                while True:
                    chunk = await upload.read(CHUNK_BYTES)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_PORTABLE_UPLOAD_BYTES:
                        raise ValueError("Bundle cabinet trop volumineux")
                    target.write(chunk)
            if size <= 0:
                raise ValueError("Bundle cabinet vide")
            CabinetBundleService.to_local_guided_restore_archive(source, migration_secret, local_restore)
            result = GuidedRestoreService.preflight_file(local_restore, original_name=Path(getattr(upload, "filename", "cabinet.dcbundle") or "cabinet.dcbundle").name, owner_employer_id=owner_employer_id)
            result["portable_bundle"] = True
            return result
        finally:
            source.unlink(missing_ok=True)
            local_restore.unlink(missing_ok=True)
            try:
                await upload.close()
            except Exception:
                pass
