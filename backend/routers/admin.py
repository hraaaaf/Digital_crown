"""Admin router compatibility wrapper for fail-closed Settings security fixes.

The historical admin router remains byte-for-byte in ``admin_legacy``. Only the
mobile revoke, verified backup/portable bundle and guided restore endpoints are
owned here so unrelated admin behavior is not rewritten as part of hardening.
"""
from fastapi import Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from backend.core.paths import AppPaths
from backend.security import token_blacklist
from backend.services.backup_service import BackupService
from backend.services.cabinet_bundle import CabinetBundleService
from backend.services.guided_restore import GuidedRestoreService
from . import admin_legacy as _legacy
from .admin_legacy import *  # noqa: F401,F403


router = _legacy.router
router.routes[:] = [
    route for route in router.routes
    if getattr(route, "path", None) not in {"/revoke-mobile", "/export-db"}
]


class GuidedRestoreApplyRequest(BaseModel):
    confirmation: str


class CabinetBundleExportRequest(BaseModel):
    migration_secret: str


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


@router.post("/export-cabinet")
def export_portable_cabinet(
    payload: CabinetBundleExportRequest,
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Create a portable Windows/macOS cabinet bundle protected by a migration phrase."""
    try:
        result = CabinetBundleService.export_active_cabinet(payload.migration_secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        _legacy.logger.error("Portable cabinet export refused: %s", type(exc).__name__)
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        _legacy.logger.error("Portable cabinet export failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Export portable du cabinet impossible.") from exc

    bundle_path = result["path"]
    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="EXPORT_PORTABLE_CABINET",
        resource_type="CabinetBundle",
        resource_id=None,
        severity="CRITICAL",
        details=(
            f"Bundle cabinet portable créé ({result.get('size_bytes', 0)} octets, "
            f"{result.get('media_file_count', 0)} médias); secrets machine-bound exclus."
        ),
    )
    return FileResponse(
        path=bundle_path,
        filename=result["filename"],
        media_type="application/vnd.digitalcrown.cabinet-bundle",
        background=BackgroundTask(bundle_path.unlink, missing_ok=True),
    )


def _restore_not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail="Restauration introuvable.")


@router.post("/restore/preflight")
async def guided_restore_preflight(
    backup: UploadFile = File(...),
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Stage and inspect a local backup without mutating the active cabinet state."""
    employer_id = current_user.get_employer_id()
    try:
        result = await GuidedRestoreService.preflight_upload(backup, owner_employer_id=employer_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        _legacy.logger.error("Guided restore preflight failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Préflight de restauration impossible.") from exc

    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="GUIDED_RESTORE_PREFLIGHT",
        resource_type="BackupRestore",
        resource_id=result["restore_id"],
        severity="CRITICAL",
        details=(
            f"Préflight restauration: compatible={result.get('compatible')} "
            f"type={result.get('archive_type')} taille={result.get('size_bytes', 0)}."
        ),
    )
    return result


@router.post("/restore/portable/preflight")
async def portable_cabinet_preflight(
    migration_secret: str = Form(...),
    backup: UploadFile = File(...),
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Convert a portable bundle to destination-local staging, then reuse Guided Restore."""
    employer_id = current_user.get_employer_id()
    try:
        result = await CabinetBundleService.preflight_upload(
            backup,
            migration_secret,
            owner_employer_id=employer_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        _legacy.logger.error("Portable cabinet preflight failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Préflight du bundle cabinet impossible.") from exc

    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PORTABLE_CABINET_PREFLIGHT",
        resource_type="BackupRestore",
        resource_id=result["restore_id"],
        severity="CRITICAL",
        details=(
            f"Bundle portable converti vers staging local; compatible={result.get('compatible')} "
            f"médias={result.get('media_file_count', 0)}; aucun secret de migration journalisé."
        ),
    )
    return result


@router.post("/restore/{restore_id}/prepare")
def guided_restore_prepare(
    restore_id: str,
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Create and verify the safety point before strong confirmation becomes available."""
    employer_id = current_user.get_employer_id()
    try:
        result = GuidedRestoreService.prepare(restore_id, owner_employer_id=employer_id)
    except (FileNotFoundError, PermissionError) as exc:
        raise _restore_not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="GUIDED_RESTORE_PREPARED",
        resource_type="BackupRestore",
        resource_id=restore_id,
        severity="CRITICAL",
        details=(
            "Package revalidé; point de secours DB créé et vérifié; "
            "empreinte média figée lorsqu'une restauration média est prévue."
        ),
    )
    return result


@router.get("/restore/{restore_id}/status")
def guided_restore_status(
    restore_id: str,
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Return the persisted, non-sensitive audit status for a restore job."""
    try:
        job = GuidedRestoreService.get_owned_job(restore_id, current_user.get_employer_id())
        return GuidedRestoreService.public_job(job)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _restore_not_found(exc) from exc


@router.delete("/restore/{restore_id}")
def guided_restore_cancel(
    restore_id: str,
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Discard a staged restore while it is still reversible."""
    employer_id = current_user.get_employer_id()
    try:
        GuidedRestoreService.cancel(restore_id, owner_employer_id=employer_id)
    except (FileNotFoundError, ValueError, PermissionError) as exc:
        raise _restore_not_found(exc) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _legacy.audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="GUIDED_RESTORE_CANCELLED",
        resource_type="BackupRestore",
        resource_id=restore_id,
        severity="INFO",
        details="Restauration préparée annulée avant toute bascule destructive.",
    )
    return {"status": "cancelled"}


@router.post("/restore/{restore_id}/apply")
def guided_restore_apply(
    restore_id: str,
    payload: GuidedRestoreApplyRequest,
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Arm the detached cabinet worker; the live process never edits its own DB."""
    employer_id = current_user.get_employer_id()
    try:
        if payload.confirmation != "RESTAURER":
            raise ValueError("Confirmation exacte requise : RESTAURER")
        if not GuidedRestoreService.runtime_apply_supported():
            raise RuntimeError("Apply hors-processus disponible uniquement dans l'exécutable cabinet")
        job = GuidedRestoreService.get_owned_job(restore_id, employer_id)
        if not job.get("compatible") or job.get("status") != "prepared":
            raise ValueError("Préparation sécurisée requise avant restauration")

        _legacy.audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=employer_id,
            action="GUIDED_RESTORE_APPLY_REQUESTED",
            resource_type="BackupRestore",
            resource_id=restore_id,
            severity="CRITICAL",
            details=(
                "Apply restauration explicitement confirmé par le token RESTAURER; "
                "secours local, apply hors-processus, smoke check et rollback obligatoires."
            ),
        )
        result = GuidedRestoreService.request_apply(
            restore_id,
            payload.confirmation,
            owner_employer_id=employer_id,
        )
    except (FileNotFoundError, PermissionError) as exc:
        raise _restore_not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        _legacy.logger.error("Guided restore apply scheduling failed: %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Impossible d'engager la restauration guidée.") from exc

    return JSONResponse(status_code=202, content=result)
