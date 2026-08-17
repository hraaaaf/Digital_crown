"""Admin router compatibility wrapper for fail-closed Settings security fixes.

The historical admin router remains byte-for-byte in ``admin_legacy``. Only the
mobile revoke and manual database export endpoints are replaced here so unrelated
admin behavior is not rewritten as part of the Settings hardening.
"""
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse

from backend.core.paths import AppPaths
from backend.security import token_blacklist
from backend.services.backup_service import BackupService
from . import admin_legacy as _legacy
from .admin_legacy import *  # noqa: F401,F403


# Remove historical implementations that either left issued mobile JWTs alive or
# bypassed the verified/encrypted BackupService contract.
router = _legacy.router
router.routes[:] = [
    route for route in router.routes
    if getattr(route, "path", None) not in {"/revoke-mobile", "/export-db"}
]


@router.post("/revoke-mobile")
def revoke_mobile_access(
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Immediately revoke this cabinet's existing mobile sessions."""
    emp_id = current_user.get_employer_id()
    try:
        revocation = token_blacklist.revoke_mobile_access(emp_id, db)
    except Exception as exc:
        _legacy.logger.error("Mobile revocation epoch persistence failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Échec de la révocation") from exc

    try:
        env_path = _legacy.current_backend_env_path()
        _legacy.zka_service.rotate_master_key(env_path)
    except Exception as exc:
        _legacy.logger.error("Mobile sessions revoked but ZKA key rotation failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Accès mobiles révoqués, mais rotation de la clé locale échouée.",
        ) from exc

    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=emp_id,
        action="MOBILE_ACCESS_REVOKED",
        resource_type="ZKAMasterKey",
        resource_id=None,
        severity="CRITICAL",
        details=(
            "Révocation mobile tenant-scopée persistée, codes d'appairage en attente "
            "invalidés et clé maître ZKA renouvelée."
        ),
    )
    _legacy.logger.info("Mobile access revoked for cabinet %s by user %s", emp_id, current_user.id)
    return {
        "status": "success",
        "message": "Accès mobiles révoqués. Scannez un nouveau code pour vous reconnecter.",
        "revoked_at": revocation["revoked_at"],
        "pairing_tokens_invalidated": revocation["pairing_tokens_invalidated"],
    }


@router.get("/export-db")
def export_database(
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Create and download the verified encrypted backup for the active DB engine."""
    result = BackupService.backup_active_database()
    if result.get("status") != "SUCCESS" or not result.get("backup_filename"):
        _legacy.logger.error(
            "Manual verified backup failed: engine=%s code=%s",
            result.get("engine"),
            result.get("error_code"),
        )
        raise HTTPException(
            status_code=500,
            detail="La sauvegarde chiffrée n'a pas pu être créée et vérifiée.",
        )

    filename = str(result["backup_filename"])
    backup_path = AppPaths.get_user_data_dir() / "backups" / filename
    if not backup_path.exists() or backup_path.stat().st_size <= 0:
        raise HTTPException(status_code=500, detail="Fichier de sauvegarde vérifié introuvable.")

    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="EXPORT_DB",
        resource_type="DatabaseBackup",
        resource_id=None,
        severity="CRITICAL",
        details=(
            f"Sauvegarde chiffrée vérifiée téléchargée ({result.get('engine')}, "
            f"{result.get('size_bytes', 0)} octets)."
        ),
    )
    return FileResponse(
        path=backup_path,
        filename=filename,
        media_type="application/octet-stream",
    )
