"""Orchestrateur unique du backup planifié DB + médias — SCHEDULED-TASK-BACKUP-REPLACE-1.

Usage : python -m backend.scripts.scheduled_backup [--apply-retention] [--dry-run]

Séquence : préflight -> verrou -> backup PostgreSQL -> backup médias -> manifeste ->
rétention. Réutilise BackupService._backup_postgres() et
backup_media._build_media_archive() -- aucune réimplémentation de pg_dump ou du
chiffrement (voir CLAUDE.md, doctrine backup).

Répertoires dédiés, jamais partagés avec les backups manuels (backend/backups/) ni
le scheduler in-app (%APPDATA%/DigitalCrown/backups/) :
  DigitalCrown-Runtime/backups/scheduled/db/
  DigitalCrown-Runtime/backups/scheduled/media/
  DigitalCrown-Runtime/backups/scheduled/manifests/
  DigitalCrown-Runtime/backups/scheduled/logs/

Doctrine : cette tâche exécute toujours son propre backup DB+médias indépendant --
elle ne tente jamais de détecter/sauter sur la base d'un backup déjà produit par le
scheduler in-app (qui ne couvre jamais les médias, donc ne peut jamais constituer un
"backup complet" au sens de cette mission).
"""
import argparse
import json
import logging
import os
import stat
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

RUNTIME_ROOT = Path(os.environ.get("DIGITALCROWN_RUNTIME_ROOT", r"C:\Users\lenovo\DigitalCrown-Runtime"))
SCHEDULED_ROOT = RUNTIME_ROOT / "backups" / "scheduled"
LOCK_PATH = SCHEDULED_ROOT / ".backup.lock"

# SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1 : le dépôt de travail mutable ne doit jamais
# être la source du code réellement exécuté par la tâche planifiée -- seul un venv/
# interpréteur épinglé dans ce dépôt reste temporairement toléré (backlog
# RUNTIME-PYTHON-INDEPENDENCE-1), jamais le code backend.* lui-même.
REPO_ROOT = Path(os.environ.get("DIGITALCROWN_REPO_ROOT", r"C:\Users\lenovo\Documents\Cabinet\DigitalCrown"))

DB_RETENTION_DAYS = int(os.environ.get("SCHEDULED_DB_RETENTION_DAYS", "30"))
MEDIA_RETENTION_DAYS = int(os.environ.get("SCHEDULED_MEDIA_RETENTION_DAYS", "7"))
MIN_BACKUPS_TO_KEEP = int(os.environ.get("SCHEDULED_MIN_BACKUPS_TO_KEEP", "3"))

# Copie hors machine (best-effort, jamais bloquante -- voir _run_offsite_copy).
# Vide/absente = fonctionnalité désactivée (offsite_status: NOT_CONFIGURED), pas une
# erreur. Rétention hors-site séparée de la rétention locale : un NAS n'a pas la même
# contrainte de capacité qu'un disque local.
OFFSITE_DIR = os.environ.get("SCHEDULED_OFFSITE_BACKUP_DIR", "").strip()
OFFSITE_DB_RETENTION_DAYS = int(os.environ.get("SCHEDULED_OFFSITE_DB_RETENTION_DAYS", str(DB_RETENTION_DAYS)))
OFFSITE_MEDIA_RETENTION_DAYS = int(os.environ.get("SCHEDULED_OFFSITE_MEDIA_RETENTION_DAYS", str(MEDIA_RETENTION_DAYS)))

logger = logging.getLogger("scheduled_backup")


# Keep the lock file inode stable across executions. An OS-owned lock is
# released on process exit, including crashes. Never unlink/recreate the path:
# doing so could let concurrent processes lock different inodes.
_LOCK_FD = None


def _acquire_lock() -> tuple[bool, str]:
    global _LOCK_FD
    if _LOCK_FD is not None:
        return False, "Verrou déjà détenu par ce processus"
    try:
        SCHEDULED_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            entry = LOCK_PATH.lstat()
        except FileNotFoundError:
            entry = None
        if entry is not None and (
            not stat.S_ISREG(entry.st_mode)
            or getattr(entry, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            return False, "Verrou non régulier / redirection refusée"
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(LOCK_PATH, flags, 0o600)
    except OSError as exc:
        return False, f"Verrou inaccessible : {type(exc).__name__}"

    try:
        pinned = os.fstat(fd)
        named = LOCK_PATH.lstat()
        if not stat.S_ISREG(pinned.st_mode) or (
            getattr(named, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ) or (pinned.st_dev, pinned.st_ino) != (named.st_dev, named.st_ino):
            raise OSError("Verrou substitué pendant ouverture")
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        elif os.name == "posix":
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            raise OSError("Plateforme de verrouillage non certifiée")
        # Never trust a stale JSON/PID file to reclaim a live lock. Ownership
        # is the actual kernel lock on this persistent file descriptor.
        _LOCK_FD = fd
        return True, ""
    except (OSError, ValueError) as exc:
        os.close(fd)
        return False, f"Verrou détenu ou refusé : {type(exc).__name__}"


def _release_lock():
    global _LOCK_FD
    fd = _LOCK_FD
    _LOCK_FD = None
    if fd is None:
        return
    # Closing the owned fd releases flock/msvcrt.locking, also after a crash.
    # Do not unlink the lock filename: deleting it can create split-brain.
    try:
        os.close(fd)
    except OSError as exc:
        logger.warning("Impossible de fermer le verrou (%s).", type(exc).__name__)


def _check_execution_provenance() -> dict:
    """Refuse de continuer si un module backend.* critique a été chargé depuis le
    dépôt de travail mutable plutôt que depuis une release. sys.executable (le venv)
    reste une exception explicite -- seule sa dépendance résiduelle est tolérée
    (backlog RUNTIME-PYTHON-INDEPENDENCE-1), jamais le code lui-même.

    Les imports sont faits ici (pas au niveau module) pour que ce module lui-même
    fasse partie de la vérification -- son propre __file__ est inspecté en premier.
    """
    import backend.scripts.scheduled_backup as _self
    from backend.services import backup_service as _backup_service_mod
    from backend.scripts import backup_db as _backup_db_mod
    from backend.scripts import backup_media as _backup_media_mod
    from backend.scripts import backup_offsite as _backup_offsite_mod
    from backend import database as _database_mod

    modules = {
        "scheduled_backup": _self,
        "backup_service": _backup_service_mod,
        "backup_db": _backup_db_mod,
        "backup_media": _backup_media_mod,
        "backup_offsite": _backup_offsite_mod,
        "database": _database_mod,
    }

    violations = {}
    for name, mod in modules.items():
        mod_path = Path(mod.__file__).resolve()
        try:
            mod_path.relative_to(REPO_ROOT.resolve())
            violations[name] = str(mod_path)
        except ValueError:
            pass  # not under REPO_ROOT -- OK

    result = {
        "status": "VIOLATION" if violations else "OK",
        "cwd": os.getcwd(),
        "python_executable": sys.executable,
        "repo_root_checked": str(REPO_ROOT),
        "violations": violations,
    }
    if violations:
        logger.error(
            "Provenance d'exécution violée : %d module(s) chargé(s) depuis le dépôt "
            "de travail (%s) au lieu d'une release : %s",
            len(violations), REPO_ROOT, ", ".join(violations.keys()),
        )
    return result


def _run_db_backup(timestamp: str) -> dict:
    from backend.services.backup_service import BackupService
    dialect_name, _driver = BackupService._detect_engine()
    if dialect_name != "postgresql":
        return {
            "status": "SKIPPED_UNSUPPORTED_ENGINE", "backup_filename": None, "size_bytes": 0,
            "checksum": None, "error_code": "UNSUPPORTED_ENGINE",
            "error_message": f"Moteur non supporté pour le backup planifié : {dialect_name}",
        }
    db_dir = SCHEDULED_ROOT / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return BackupService._backup_postgres(db_dir, timestamp)


def _run_media_backup(timestamp: str) -> dict:
    from backend.scripts.backup_media import _build_media_archive
    media_dir = SCHEDULED_ROOT / "media"
    return _build_media_archive(media_dir, timestamp)


def _apply_retention(
    target_dir: Path, prefix: str, suffix: str, retention_days: int, dry_run: bool,
    min_to_keep: int | None = None,
) -> dict:
    """Ne supprime que dans target_dir (toujours un sous-dossier de scheduled/ ou de
    la destination hors-site), protège toujours les min_to_keep fichiers les plus
    récents quel que soit leur âge (défaut : MIN_BACKUPS_TO_KEEP, le même plancher
    que pour les dossiers locaux), journalise chaque candidat avant toute suppression
    réelle."""
    if min_to_keep is None:
        min_to_keep = MIN_BACKUPS_TO_KEEP
    report = {"dir": str(target_dir), "dry_run": dry_run, "candidates": [], "deleted": []}
    if not dry_run:
        # MAJ-02 containment: until anchored local deletion is reviewed on
        # Windows and POSIX, fail CLOSED. Never follow a mutable directory
        # path into unrelated archives merely to free disk space.
        logger.warning("Local retention DELETE disabled pending SEC/OPS certification")
        report["dry_run"] = True
        report["status"] = "BLOCKED_UNCERTIFIED_LOCAL_DELETE"
        return report
    if not target_dir.exists():
        return report

    files = sorted(
        [f for f in target_dir.glob(f"{prefix}*{suffix}") if f.is_file()],
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    protected = {f.name for f in files[:min_to_keep]}
    cutoff = time.time() - retention_days * 86400

    for f in files:
        if f.name in protected:
            continue
        if f.stat().st_mtime < cutoff:
            report["candidates"].append(f.name)
            logger.info("Rétention : candidat %s à suppression (dry_run=%s).", f.name, dry_run)
            if not dry_run:
                try:
                    f.unlink()
                    report["deleted"].append(f.name)
                except Exception as e:
                    logger.warning("Rétention : échec suppression %s (%s).", f.name, type(e).__name__)
    return report


def _apply_retention_all(dry_run: bool) -> list:
    return [
        _apply_retention(SCHEDULED_ROOT / "db", "db_backup_", ".sql.enc", DB_RETENTION_DAYS, dry_run),
        _apply_retention(SCHEDULED_ROOT / "media", "media_backup_", ".zip.enc", MEDIA_RETENTION_DAYS, dry_run),
    ]


def _apply_retention_all_offsite(offsite_dir_str: str, dry_run: bool) -> list:
    """Fail closed: NEVER enumerate or delete remote backup paths before an
    audited handle-relative NAS/SMB deletion gate.

    The offsite copy's pinned directory handles do not protect a later
    glob/stat/unlink from symlink swaps. This is a no-I/O policy sentinel,
    including if called directly with dry_run=False.
    """
    offsite_root = Path(offsite_dir_str)
    if not dry_run:
        logger.warning("Remote retention disabled pending audited NAS/SMB path-race safety")
    return [
        {
            "dir": str(offsite_root / folder),
            "dry_run": True,
            "candidates": [],
            "deleted": [],
            "status": "BLOCKED_UNCERTIFIED_REMOTE_DELETE",
        }
        for folder in ("db", "media")
    ]


def _run_offsite_copy(manifest: dict) -> dict:
    """Copie best-effort vers SCHEDULED_OFFSITE_BACKUP_DIR si configuré. Ne lève
    jamais -- double filet de sécurité (try/except interne à copy_to_offsite() ET
    ici) puisque cette étape ne doit JAMAIS affecter le succès du backup principal."""
    empty = {
        "status": "NOT_CONFIGURED", "db_copied": False, "media_copied": False,
        "error_code": None, "error_message": None, "duration_seconds": 0.0,
    }
    if not OFFSITE_DIR:
        return empty
    try:
        from backend.scripts.backup_offsite import copy_to_offsite
        db_source = (
            SCHEDULED_ROOT / "db" / manifest["db_backup_filename"]
            if manifest.get("db_backup_filename") else None
        )
        media_source = (
            SCHEDULED_ROOT / "media" / manifest["media_backup_filename"]
            if manifest.get("media_backup_filename") else None
        )
        return copy_to_offsite(
            db_source, manifest.get("db_checksum"),
            media_source, manifest.get("media_checksum"),
            Path(OFFSITE_DIR),
        )
    except Exception as e:
        logger.warning(
            "Backup hors-site : exception inattendue, traitée comme un échec "
            "best-effort sans impact sur le backup principal (%s).", type(e).__name__,
        )
        return {
            "status": "FAILED", "db_copied": False, "media_copied": False,
            "error_code": "UNEXPECTED_EXCEPTION", "error_message": str(type(e).__name__),
            "duration_seconds": 0.0,
        }


def _write_manifest(manifest: dict):
    manifests_dir = SCHEDULED_ROOT / "manifests"
    logs_dir = SCHEDULED_ROOT / "logs"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    path = manifests_dir / f"manifest_{manifest['run_id']}.json"
    text = json.dumps(manifest, indent=2, default=str)
    path.write_text(text, encoding="utf-8")
    (manifests_dir / "latest.json").write_text(text, encoding="utf-8")

    log_path = logs_dir / f"run_{manifest['run_id']}.log"
    log_path.write_text(
        f"run_id={manifest['run_id']}\n"
        f"started_at={manifest['started_at']}\n"
        f"completed_at={manifest['completed_at']}\n"
        f"lock_status={manifest['lock_status']}\n"
        f"db_status={manifest['db_status']} file={manifest['db_backup_filename']} size={manifest['db_size_bytes']}\n"
        f"media_status={manifest['media_status']} file={manifest['media_backup_filename']} "
        f"size={manifest['media_size_bytes']} count={manifest['media_file_count']}\n"
        f"offsite_status={manifest['offsite_status']} db_copied={manifest['offsite_db_copied']} "
        f"media_copied={manifest['offsite_media_copied']}\n"
        f"overall_status={manifest['overall_status']}\n"
        f"error_code={manifest['error_code']}\n"
        f"error_message={manifest['error_message']}\n",
        encoding="utf-8",
    )


def run(*, apply_retention: bool = False, dry_run: bool = False) -> dict:
    run_id = uuid.uuid4().hex[:12]
    # Unique per attempt even when jobs start within the same second.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + run_id
    manifest = {
        "run_id": run_id,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "provenance_status": None,
        "provenance_violations": {},
        "lock_status": None,
        "db_status": None, "db_backup_filename": None, "db_size_bytes": 0, "db_checksum": None,
        "media_status": None, "media_backup_filename": None, "media_size_bytes": 0,
        "media_file_count": 0, "media_checksum": None,
        "overall_status": None,
        "offsite_status": "NOT_CONFIGURED", "offsite_db_copied": False, "offsite_media_copied": False,
        "offsite_error_code": None, "offsite_error_message": None, "offsite_duration_seconds": 0.0,
        "offsite_retention_candidates": [],
        "offsite_retention_status": "NOT_CONFIGURED",
        "retention_dry_run": not apply_retention,
        "retention_status": "BLOCKED_UNCERTIFIED_LOCAL_DELETE" if apply_retention else "DRY_RUN",
        "retention_candidates": [],
        "error_code": None, "error_message": None,
    }

    # Vérifié avant même le verrou : aucun backup ne doit être tenté si le code
    # exécuté ne provient pas d'une release (SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1).
    provenance = _check_execution_provenance()
    manifest["provenance_status"] = provenance["status"]
    manifest["provenance_violations"] = provenance["violations"]
    if provenance["status"] != "OK":
        manifest["overall_status"] = "FAILED"
        manifest["error_code"] = "EXECUTION_PROVENANCE_VIOLATION"
        manifest["error_message"] = (
            f"{len(provenance['violations'])} module(s) chargé(s) depuis le dépôt de travail"
        )
        manifest["completed_at"] = datetime.utcnow().isoformat() + "Z"
        _write_manifest(manifest)
        return manifest

    acquired, reason = _acquire_lock()
    if not acquired:
        manifest["lock_status"] = "SKIPPED_LOCKED"
        manifest["overall_status"] = "FAILED"
        manifest["error_code"] = "LOCK_HELD"
        manifest["error_message"] = reason
        manifest["completed_at"] = datetime.utcnow().isoformat() + "Z"
        _write_manifest(manifest)
        return manifest

    manifest["lock_status"] = "ACQUIRED"
    try:
        if dry_run:
            manifest["db_status"] = "SKIPPED_DRY_RUN"
            manifest["media_status"] = "SKIPPED_DRY_RUN"
            manifest["offsite_status"] = "SKIPPED_DRY_RUN"
            manifest["overall_status"] = "SKIPPED_DRY_RUN"
        else:
            db_result = _run_db_backup(timestamp)
            manifest["db_status"] = db_result["status"]
            manifest["db_backup_filename"] = db_result.get("backup_filename")
            manifest["db_size_bytes"] = db_result.get("size_bytes", 0)
            manifest["db_checksum"] = db_result.get("checksum")
            if db_result["status"] != "SUCCESS":
                manifest["error_code"] = db_result.get("error_code")
                manifest["error_message"] = db_result.get("error_message")

            media_result = _run_media_backup(timestamp)
            manifest["media_status"] = media_result["status"]
            manifest["media_backup_filename"] = media_result.get("backup_filename")
            manifest["media_size_bytes"] = media_result.get("size_bytes", 0)
            manifest["media_file_count"] = media_result.get("file_count", 0)
            manifest["media_checksum"] = media_result.get("checksum")
            if media_result["status"] != "SUCCESS" and not manifest["error_message"]:
                manifest["error_code"] = media_result.get("error_code")
                manifest["error_message"] = media_result.get("error_message")

            db_ok = manifest["db_status"] == "SUCCESS"
            media_ok = manifest["media_status"] == "SUCCESS"
            if db_ok and media_ok:
                manifest["overall_status"] = "SUCCESS"
            elif db_ok or media_ok:
                manifest["overall_status"] = "PARTIAL"
            else:
                manifest["overall_status"] = "FAILED"

            # Copie hors-site best-effort -- ne touche jamais overall_status ci-dessus,
            # calculé uniquement depuis db_status/media_status. Tentée même si le run
            # local est PARTIAL (copie ce qui a réussi) ; sautée seulement si ni DB ni
            # médias n'ont produit de fichier local.
            if db_ok or media_ok:
                offsite_result = _run_offsite_copy(manifest)
                manifest["offsite_status"] = offsite_result["status"]
                manifest["offsite_db_copied"] = offsite_result["db_copied"]
                manifest["offsite_media_copied"] = offsite_result["media_copied"]
                manifest["offsite_error_code"] = offsite_result["error_code"]
                manifest["offsite_error_message"] = offsite_result["error_message"]
                manifest["offsite_duration_seconds"] = offsite_result["duration_seconds"]

        manifest["retention_candidates"] = _apply_retention_all(dry_run=not apply_retention)

        # Retention of remote recovery points is forbidden unless this run
        # published a complete new DB+media pair. Local retention remains
        # separately governed by the existing local policy.
        if (
            OFFSITE_DIR
            and manifest["overall_status"] == "SUCCESS"
            and manifest["offsite_status"] == "SUCCESS"
            and manifest["offsite_db_copied"]
            and manifest["offsite_media_copied"]
        ):
            try:
                # A complete copy does not authorize an unvalidated remote deletion.
                # The callee also fails closed when invoked with dry_run=False.
                manifest["offsite_retention_candidates"] = _apply_retention_all_offsite(
                    OFFSITE_DIR, dry_run=True,
                )
                manifest["offsite_retention_status"] = "BLOCKED_UNCERTIFIED_REMOTE_DELETE"
            except Exception as e:
                logger.warning(
                    "Rétention hors-site : échec, sans impact sur le backup principal (%s).",
                    type(e).__name__,
                )
    finally:
        _release_lock()

    manifest["completed_at"] = datetime.utcnow().isoformat() + "Z"
    _write_manifest(manifest)
    return manifest


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Orchestrated PostgreSQL + media backup for Task Scheduler.")
    parser.add_argument(
        "--apply-retention", action="store_true",
        help="Apply retention to LOCAL scheduled backups only. Remote deletion is blocked pending NAS/SMB certification.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate lock/preflight only; do not actually run pg_dump or the media backup.",
    )
    args = parser.parse_args()

    manifest = run(apply_retention=args.apply_retention, dry_run=args.dry_run)
    print(json.dumps(manifest, indent=2, default=str))
    sys.exit(0 if manifest["overall_status"] in ("SUCCESS", "SKIPPED_DRY_RUN") else 1)


if __name__ == "__main__":
    main()
