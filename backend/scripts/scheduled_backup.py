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
import socket
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

RUNTIME_ROOT = Path(os.environ.get("DIGITALCROWN_RUNTIME_ROOT", r"C:\Users\lenovo\DigitalCrown-Runtime"))
SCHEDULED_ROOT = RUNTIME_ROOT / "backups" / "scheduled"
LOCK_PATH = SCHEDULED_ROOT / ".backup.lock"
LOCK_MAX_AGE_SECONDS = 2 * 60 * 60  # 2h - durée max raisonnable d'un backup DB+médias

DB_RETENTION_DAYS = int(os.environ.get("SCHEDULED_DB_RETENTION_DAYS", "30"))
MEDIA_RETENTION_DAYS = int(os.environ.get("SCHEDULED_MEDIA_RETENTION_DAYS", "7"))
MIN_BACKUPS_TO_KEEP = int(os.environ.get("SCHEDULED_MIN_BACKUPS_TO_KEEP", "3"))

logger = logging.getLogger("scheduled_backup")


def _pid_alive(pid: int) -> bool:
    """Vérification Windows-only (tasklist) — ce projet est on-premise Windows,
    voir CLAUDE.md. Pas de dépendance psutil ajoutée pour un seul appel/jour."""
    if not pid:
        return False
    try:
        import subprocess
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
        return str(pid) in r.stdout
    except Exception:
        return False


def _acquire_lock() -> tuple[bool, str]:
    SCHEDULED_ROOT.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        try:
            existing = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
            age = time.time() - existing.get("started_at_epoch", 0)
            pid = existing.get("pid")
            pid_alive = _pid_alive(pid) if pid else False
            if pid_alive and age < LOCK_MAX_AGE_SECONDS:
                return False, f"Verrou actif (pid={pid}, age={int(age)}s)"
            logger.warning(
                "Verrou périmé détecté (pid_alive=%s, age=%ds) — écrasé.", pid_alive, int(age)
            )
        except Exception as e:
            logger.warning("Verrou illisible, écrasé (%s).", type(e).__name__)

    payload = {
        "pid": os.getpid(), "host": socket.gethostname(),
        "started_at_epoch": time.time(), "started_at": datetime.utcnow().isoformat() + "Z",
    }
    LOCK_PATH.write_text(json.dumps(payload), encoding="utf-8")
    return True, ""


def _release_lock():
    try:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()
    except Exception as e:
        logger.warning("Impossible de libérer le verrou (%s).", type(e).__name__)


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


def _apply_retention(target_dir: Path, prefix: str, suffix: str, retention_days: int, dry_run: bool) -> dict:
    """Ne supprime que dans target_dir (toujours un sous-dossier de scheduled/),
    protège toujours les MIN_BACKUPS_TO_KEEP fichiers les plus récents quel que soit
    leur âge, journalise chaque candidat avant toute suppression réelle."""
    report = {"dir": str(target_dir), "dry_run": dry_run, "candidates": [], "deleted": []}
    if not target_dir.exists():
        return report

    files = sorted(
        [f for f in target_dir.glob(f"{prefix}*{suffix}") if f.is_file()],
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    protected = {f.name for f in files[:MIN_BACKUPS_TO_KEEP]}
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
        f"overall_status={manifest['overall_status']}\n"
        f"error_code={manifest['error_code']}\n"
        f"error_message={manifest['error_message']}\n",
        encoding="utf-8",
    )


def run(*, apply_retention: bool = False, dry_run: bool = False) -> dict:
    run_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = {
        "run_id": run_id,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "lock_status": None,
        "db_status": None, "db_backup_filename": None, "db_size_bytes": 0, "db_checksum": None,
        "media_status": None, "media_backup_filename": None, "media_size_bytes": 0,
        "media_file_count": 0, "media_checksum": None,
        "overall_status": None,
        "retention_dry_run": not apply_retention,
        "retention_candidates": [],
        "error_code": None, "error_message": None,
    }

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

        manifest["retention_candidates"] = _apply_retention_all(dry_run=not apply_retention)
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
        help="Actually delete old scheduled backups beyond retention. Default: dry-run only, deletes nothing.",
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
