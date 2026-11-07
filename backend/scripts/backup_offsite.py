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


def _directory_chain_failure(target: Path) -> str | None:
    """Return a stable denial code; None means no unsafe ancestor was observed.

    Symlink/junction/reparse redirects are security failures. Ordinary blocking
    files and unreachable parents preserve the historical UNREACHABLE status.
    This lexical check alone does not solve concurrent path-swap attacks.
    """
    if not target.is_absolute() or ".." in target.parts:
        return "DEST_DIRECTORY_UNSAFE"
    for entry in (target, *target.parents):
        try:
            metadata = entry.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return "DEST_UNREACHABLE"
        if stat.S_ISLNK(metadata.st_mode) or (
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            return "DEST_DIRECTORY_UNSAFE"
        if not stat.S_ISDIR(metadata.st_mode):
            return "DEST_UNREACHABLE"
    return None


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


def _posix_descriptor_backend_available() -> bool:
    """Whether Python can anchor path operations to an already-open directory.

    Windows needs a native, independently tested handle-relative backend:
    the lexical fallback below remains a **non-approved** candidate there.
    """
    return (
        os.name == "posix"
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and os.open in os.supports_dir_fd
        and os.mkdir in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.unlink in os.supports_dir_fd
        and os.link in os.supports_dir_fd
    )


def _open_pinned_directory(directory: Path, *, create: bool = True) -> int:
    """Safely walk/create ancestors without following a path component symlink.

    Caller owns returned fd. Each child is opened relative to its parent fd,
    so replacing a path with a symlink cannot redirect subsequent operations
    to the injected target. Does not establish Windows SMB/ACL semantics.
    """
    if not directory.is_absolute() or ".." in directory.parts:
        raise OSError(errno.EPERM, "Unsafe target directory path")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    current = os.open(os.path.sep, flags)
    try:
        for part in directory.parts:
            if part in ("", os.path.sep):
                continue
            try:
                child = os.open(part, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, 0o700, dir_fd=current)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=current)
            except NotADirectoryError as e:
                # Linux returns ENOTDIR (not ELOOP) for O_NOFOLLOW +
                # O_DIRECTORY on a symbolic link. Distinguish it from a
                # regular-file ancestor, which remains DEST_UNREACHABLE.
                try:
                    entry = os.stat(part, dir_fd=current, follow_symlinks=False)
                except OSError:
                    raise e
                if stat.S_ISLNK(entry.st_mode):
                    raise OSError(errno.ELOOP, "Symlink ancestor denied") from e
                raise
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def _pinned_directory_matches_path(directory: Path, pinned_fd: int) -> bool:
    """Reject path replacement/remapping even when a pinned fd stays valid."""
    try:
        check_fd = _open_pinned_directory(directory, create=False)
    except OSError:
        return False
    try:
        expected = os.fstat(pinned_fd)
        observed = os.fstat(check_fd)
        return (expected.st_dev, expected.st_ino) == (observed.st_dev, observed.st_ino)
    finally:
        os.close(check_fd)


def _copy_one_pinned_posix(
    source: Path, expected_checksum: str, dest_dir: Path,
) -> tuple[bool, str | None, str | None]:
    """Copy, hash and publish via pinned directory and file descriptors.

    No source, temp or existing-target pathname is reopened for blocking I/O.
    The /proc/self/fd link source ties publication to the already-validated
    temporary *inode*, even if its directory entry is replaced concurrently.
    No destructive rename fallback is permitted.
    """
    try:
        directory_fd = _open_pinned_directory(dest_dir)
    except OSError as e:
        code = "DEST_DIRECTORY_UNSAFE" if e.errno in (
            errno.ELOOP, errno.EPERM, errno.EACCES,
        ) else "DEST_UNREACHABLE"
        return False, code, f"Ouverture ancrée impossible : {type(e).__name__}"

    temp_name = f".tmp_{uuid.uuid4().hex}_{source.name}"
    temp_inode = None
    try:
        # Preserve the structured SOURCE_UNSAFE_FILE_TYPE contract for an
        # already-present FIFO, socket, directory or symlink. The fd-based
        # _open_regular_readonly below independently rechecks against races.
        try:
            source_metadata = source.lstat()
        except OSError as e:
            return False, "COPY_FAILED", f"Source indisponible : {type(e).__name__}"
        if not _regular_nonreparse(source_metadata):
            return False, "SOURCE_UNSAFE_FILE_TYPE", "La source n'est pas un fichier régulier"
        try:
            with _open_regular_readonly(source) as reader:
                flags = (os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                         | getattr(os, "O_CLOEXEC", 0))
                temp_fd = os.open(temp_name, flags, 0o600, dir_fd=directory_fd)
                with os.fdopen(temp_fd, "w+b", buffering=0) as temp:
                    st = os.fstat(temp.fileno())
                    temp_inode = (st.st_dev, st.st_ino)
                    shutil.copyfileobj(reader, temp, length=1024 * 1024)
                    temp.flush()
                    os.fsync(temp.fileno())
                    temp.seek(0)
                    digest = hashlib.sha256()
                    while True:
                        chunk = temp.read(1024 * 1024)
                        if not chunk:
                            break
                        digest.update(chunk)
                    if digest.hexdigest() != expected_checksum:
                        return False, "CHECKSUM_MISMATCH", "La copie chiffrée ne correspond pas au SHA-256"
                    # The name can be swapped by another actor while the fd
                    # stays pinned. Never link or open the replacement entry.
                    temp_entry = os.stat(
                        temp_name, dir_fd=directory_fd, follow_symlinks=False,
                    )
                    if (temp_entry.st_dev, temp_entry.st_ino) != temp_inode or not _regular_nonreparse(temp_entry):
                        return False, "TEMP_PATH_TAMPERED", "Fichier temporaire substitué"
                    if not _pinned_directory_matches_path(dest_dir, directory_fd):
                        return False, "DEST_DIRECTORY_UNSAFE", "Répertoire remplacé pendant la copie"
                    # Linux proc-fd is a trusted kernel path to the open inode.
                    # Without it, fail closed rather than re-linking by a
                    # potentially attacker-controlled temp pathname.
                    proc_source = f"/proc/self/fd/{temp.fileno()}"
                    if not os.path.exists(proc_source):
                        return False, "ATOMIC_PUBLICATION_UNAVAILABLE", "Lien fd atomique indisponible"
                    try:
                        os.link(
                            proc_source, source.name,
                            dst_dir_fd=directory_fd, follow_symlinks=True,
                        )
                    except FileExistsError:
                        existing_flags = (os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
                                          | getattr(os, "O_CLOEXEC", 0))
                        try:
                            existing_fd = os.open(
                                source.name, existing_flags, dir_fd=directory_fd,
                            )
                            with os.fdopen(existing_fd, "rb") as existing:
                                if not _regular_nonreparse(os.fstat(existing.fileno())):
                                    return False, "EXISTING_BACKUP_UNSAFE_FILE_TYPE", "Destination finale non régulière"
                                existing_digest = hashlib.sha256()
                                while True:
                                    piece = existing.read(1024 * 1024)
                                    if not piece:
                                        break
                                    existing_digest.update(piece)
                        except OSError:
                            return False, "EXISTING_BACKUP_UNREADABLE", "Destination existante non lisible"
                        if existing_digest.hexdigest() != expected_checksum:
                            return False, "DESTINATION_NAME_COLLISION", "Nom final déjà utilisé par une archive différente"
                    except OSError as e:
                        return False, "ATOMIC_PUBLICATION_UNAVAILABLE", f"Publication sûre impossible : {type(e).__name__}"
                    if not _pinned_directory_matches_path(dest_dir, directory_fd):
                        return False, "DEST_DIRECTORY_UNSAFE", "Répertoire modifié après publication"
                    return True, None, None
        except OSError as e:
            return False, "COPY_FAILED", f"Copie ou validation ancrée impossible : {type(e).__name__}"
    finally:
        # Never unlink an injected FIFO/symlink/alternate inode. Cleanup only
        # the exact temporary inode created by this invocation.
        if temp_inode is not None:
            try:
                candidate = os.stat(temp_name, dir_fd=directory_fd, follow_symlinks=False)
                if (candidate.st_dev, candidate.st_ino) == temp_inode:
                    os.unlink(temp_name, dir_fd=directory_fd)
            except OSError:
                pass
        os.close(directory_fd)


def _copy_one(source: Path, expected_checksum: str, dest_dir: Path) -> tuple[bool, str | None, str | None]:
    """Copie atomiquement une sauvegarde déjà chiffrée vers le hors-site.

    Temporaire unique, créé en mode exclusif : aucune troncature d'un autre
    transfert simultané (ni d'un ancien .tmp_*). Lecture et re-hash par blocs
    pour ne jamais charger une grosse archive médicale entière en mémoire.
    Le fichier final n'est remplacé qu'après vérification SHA-256.
    Ne lève pas d'erreur d'E/S : la sauvegarde locale reste indépendante.
    """
    if _posix_descriptor_backend_available():
        return _copy_one_pinned_posix(source, expected_checksum, dest_dir)
    # A native Windows directory-handle implementation is still required
    # to make the active-adversary guarantee portable. Never advertise the
    # lexical fallback below as Windows TOCTOU-safe.
    directory_failure = _directory_chain_failure(dest_dir)
    if directory_failure is not None:
        return False, directory_failure, "Destination non sûre ou inaccessible"
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, "DEST_UNREACHABLE", f"Destination inaccessible : {type(e).__name__}"
    directory_failure = _directory_chain_failure(dest_dir)
    if directory_failure is not None:
        return False, directory_failure, "Destination modifiée ou inaccessible"

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
            directory_failure = _directory_chain_failure(dest_dir)
            if directory_failure is not None:
                return False, directory_failure, "Destination modifiée avant publication"
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

    directory_failure = _directory_chain_failure(dest_root)
    if directory_failure is not None:
        result["status"] = "UNREACHABLE" if directory_failure == "DEST_UNREACHABLE" else "FAILED"
        result["error_code"] = directory_failure
        result["error_message"] = "Destination hors-site non sûre ou inaccessible"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    try:
        if _posix_descriptor_backend_available():
            root_fd = _open_pinned_directory(dest_root)
            os.close(root_fd)
        else:
            dest_root.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.warning("Backup hors-site : destination injoignable (%s).", type(e).__name__)
        result["status"] = "UNREACHABLE"
        result["error_code"] = "DEST_UNREACHABLE"
        result["error_message"] = f"Destination injoignable : {type(e).__name__}"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    directory_failure = _directory_chain_failure(dest_root)
    if directory_failure is not None:
        result["status"] = "UNREACHABLE" if directory_failure == "DEST_UNREACHABLE" else "FAILED"
        result["error_code"] = directory_failure
        result["error_message"] = "Destination modifiée ou inaccessible"
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
