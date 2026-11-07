"""Copie best-effort des backups planifiés (DB + médias, déjà chiffrés) vers une
destination hors machine (partage réseau) configurable.

Module pur, entièrement paramétré par l'appelant (backend/scripts/scheduled_backup.py)
-- aucune lecture d'env ici, contrairement à backup_db.py/backup_media.py qui lisent
CABINET_MASTER_KEY_HEX en interne : ce module ne manipule que des octets déjà
chiffrés, aucun secret à charger.

Doctrine produit (verrouillée) : cette copie ne doit JAMAIS faire échouer ni
bloquer le backup local principal. Toute erreur ici se traduit par un statut
structuré, jamais par une exception qui remonterait à l'appelant.
"""
import hashlib
import logging
import os
import errno
import shutil
import stat
import time
import uuid
from pathlib import Path

logger = logging.getLogger("backup_offsite")


def _regular_nonreparse(mode_stat) -> bool:
    """Reject FIFO, symlink, socket, directory and Windows reparse handles."""
    return stat.S_ISREG(mode_stat.st_mode) and not (
        getattr(mode_stat, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _safe_directory_chain(target: Path) -> bool:
    """Read-only lexical ancestor audit, before any directory creation/open.

    Refuse symlinked paths and Windows junction/reparse ancestors rather than
    resolving them into a different offsite storage root. Permission failures
    fail closed. This is not an attestation of ACLs or an active path-swap race.
    """
    if not target.is_absolute() or ".." in target.parts:
        return False
    for entry in (target, *target.parents):
        try:
            metadata = entry.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return False
        if not stat.S_ISDIR(metadata.st_mode):
            return False
        if getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return False
    return True


def _open_regular_readonly(path: Path):
    """Open nonblocking to avoid hanging on FIFO; O_NOFOLLOW when supported."""
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        if not _regular_nonreparse(os.fstat(fd)):
            raise OSError(errno.EPERM, "Not a regular non-reparse file")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def _copy_one(source: Path, expected_checksum: str, dest_dir: Path) -> tuple[bool, str | None, str | None]:
    """Copie atomiquement une sauvegarde déjà chiffrée vers le hors-site.

    Temporaire unique, créé en mode exclusif : aucune troncature d'un autre
    transfert simultané (ni d'un ancien .tmp_*). Lecture et re-hash par blocs
    pour ne jamais charger une grosse archive médicale entière en mémoire.
    Le fichier final n'est remplacé qu'après vérification SHA-256.
    Ne lève pas d'erreur d'E/S : la sauvegarde locale reste indépendante.
    """
    if not _safe_directory_chain(dest_dir):
        return False, "DEST_DIRECTORY_UNSAFE", "Destination ou parent symbolique, jonction ou non-répertoire"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, "DEST_UNREACHABLE", f"Destination inaccessible : {type(e).__name__}"
    if not _safe_directory_chain(dest_dir):
        return False, "DEST_DIRECTORY_UNSAFE", "Destination modifiée ou non autorisée"

    try:
        source_stat = source.lstat()
        if not _regular_nonreparse(source_stat):
            return False, "SOURCE_UNSAFE_FILE_TYPE", "La source n'est pas un fichier régulier"
    except OSError as e:
        return False, "COPY_FAILED", f"Source non lisible : {type(e).__name__}"

    dest_path = dest_dir / source.name
    temp_path = dest_dir / f".tmp_{uuid.uuid4().hex}_{source.name}"
    try:
        try:
            with _open_regular_readonly(source) as reader, temp_path.open("xb") as writer:
                shutil.copyfileobj(reader, writer, length=1024 * 1024)
            # copy2's historical metadata behavior, without reopening the
            # uniquely created destination for writing.
            shutil.copystat(source, temp_path)
        except OSError as e:
            return False, "COPY_FAILED", f"Échec de la copie : {type(e).__name__}"

        try:
            digest = hashlib.sha256()
            with temp_path.open("rb") as copied:
                while True:
                    block = copied.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
            if digest.hexdigest() != expected_checksum:
                return False, "CHECKSUM_MISMATCH", "Le fichier copié ne correspond pas au checksum attendu"
            # Atomic no-clobber publication. os.replace() is unsafe here:
            # another backup with the same filename may already exist, and
            # the most recent transfer must never destroy that recovery point.
            # Hard-link creation within this directory is atomic and fails
            # closed if the target exists or the filesystem cannot support it.
            if not _safe_directory_chain(dest_dir):
                return False, "DEST_DIRECTORY_UNSAFE", "Destination modifiée avant publication"
            try:
                os.link(temp_path, dest_path)
            except FileExistsError:
                try:
                    dest_metadata = dest_path.lstat()
                    if not _regular_nonreparse(dest_metadata):
                        return False, "EXISTING_BACKUP_UNSAFE_FILE_TYPE", "Destination finale non régulière"
                except OSError as e:
                    return False, "EXISTING_BACKUP_UNREADABLE", f"Destination finale non vérifiable : {type(e).__name__}"
                existing_hash = hashlib.sha256()
                try:
                    with _open_regular_readonly(dest_path) as existing:
                        while True:
                            chunk = existing.read(1024 * 1024)
                            if not chunk:
                                break
                            existing_hash.update(chunk)
                except OSError as e:
                    return False, "EXISTING_BACKUP_UNREADABLE", f"Destination existante non vérifiable : {type(e).__name__}"
                if existing_hash.hexdigest() != expected_checksum:
                    return False, "DESTINATION_NAME_COLLISION", "Un autre backup validé porte déjà ce nom"
                # Same bytes are already committed; re-copy is idempotent.
            except OSError as e:
                return False, "ATOMIC_PUBLICATION_UNAVAILABLE", f"Publication sans écrasement impossible : {type(e).__name__}"
        except OSError as e:
            return False, "VERIFY_FAILED", f"Échec de vérification/finalisation : {type(e).__name__}"

        return True, None, None
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def copy_to_offsite(
    db_source: Path | None, db_checksum: str | None,
    media_source: Path | None, media_checksum: str | None,
    dest_root: Path,
) -> dict:
    """Copie best-effort des fichiers de backup déjà produits localement vers
    dest_root/db et dest_root/media. Ne lève jamais -- toute erreur devient un champ
    structuré du dict retourné.

    Retourne : {
      "status": "SUCCESS"|"PARTIAL"|"FAILED"|"UNREACHABLE",
      "db_copied": bool, "media_copied": bool,
      "error_code": str|None, "error_message": str|None,
      "duration_seconds": float,
    }

    NOT_CONFIGURED n'est jamais retourné par cette fonction -- c'est à l'appelant
    (scheduled_backup.py) de court-circuiter avant d'appeler cette fonction quand
    aucune destination n'est configurée.
    """
    started = time.monotonic()
    result = {
        "status": "FAILED", "db_copied": False, "media_copied": False,
        "error_code": None, "error_message": None, "duration_seconds": 0.0,
    }

    def _record_error(code: str, message: str):
        if result["error_code"] is None:
            result["error_code"] = code
            result["error_message"] = message

    if not _safe_directory_chain(dest_root):
        result["error_code"] = "DEST_DIRECTORY_UNSAFE"
        result["error_message"] = "Destination hors-site ou parent symbolique/jonction/non-répertoire"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.warning("Backup hors-site : destination injoignable (%s).", type(e).__name__)
        result["status"] = "UNREACHABLE"
        result["error_code"] = "DEST_UNREACHABLE"
        result["error_message"] = f"Destination injoignable : {type(e).__name__}"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    if not _safe_directory_chain(dest_root):
        result["error_code"] = "DEST_DIRECTORY_UNSAFE"
        result["error_message"] = "Destination modifiée ou non autorisée"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    attempted = 0

    if db_source is not None:
        attempted += 1
        if db_checksum is None:
            _record_error("DB_CHECKSUM_MISSING", "Empreinte du backup DB absente, copie refusée")
        elif not db_source.exists():
            _record_error("DB_SOURCE_MISSING", "Fichier de backup DB local introuvable")
            logger.warning("Backup hors-site : source DB introuvable (%s).", db_source)
        else:
            ok, code, msg = _copy_one(db_source, db_checksum, dest_root / "db")
            result["db_copied"] = ok
            if not ok:
                _record_error(code, msg)
                logger.warning("Backup hors-site : copie DB échouée (%s : %s).", code, msg)

    if media_source is not None:
        attempted += 1
        if media_checksum is None:
            _record_error("MEDIA_CHECKSUM_MISSING", "Empreinte du backup médias absente, copie refusée")
        elif not media_source.exists():
            _record_error("MEDIA_SOURCE_MISSING", "Fichier de backup médias local introuvable")
            logger.warning("Backup hors-site : source médias introuvable (%s).", media_source)
        else:
            ok, code, msg = _copy_one(media_source, media_checksum, dest_root / "media")
            result["media_copied"] = ok
            if not ok:
                _record_error(code, msg)
                logger.warning("Backup hors-site : copie médias échouée (%s : %s).", code, msg)

    copied_count = int(result["db_copied"]) + int(result["media_copied"])
    if attempted == 0:
        result["status"] = "FAILED"
        _record_error("NOTHING_TO_COPY", "Aucun fichier de backup local à copier")
    elif result["db_copied"] and result["media_copied"]:
        result["status"] = "SUCCESS"
        logger.info("Backup hors-site : copie DB + médias réussie (paire complète)")
    elif copied_count == 0:
        result["status"] = "FAILED"
    else:
        result["status"] = "PARTIAL"
        if attempted < 2:
            _record_error("INCOMPLETE_BACKUP_PAIR", "Succès partiel : base DB et médias requis")

    result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result
