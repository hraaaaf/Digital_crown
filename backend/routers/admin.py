"""Admin router compatibility wrapper for fail-closed mobile revocation.

The historical admin router remains byte-for-byte in ``admin_legacy``.  Only
``POST /revoke-mobile`` is replaced here so unrelated admin behavior is not
rewritten as part of the Settings security hardening.
"""
from fastapi import Depends, HTTPException

from backend.security import token_blacklist
from . import admin_legacy as _legacy
from .admin_legacy import *  # noqa: F401,F403


# Remove the historical route whose implementation rotated a key and then called
# the now-local-first sync no-op, leaving already-issued mobile JWTs valid.
router = _legacy.router
router.routes[:] = [
    route for route in router.routes
    if getattr(route, "path", None) != "/revoke-mobile"
]


@router.post("/revoke-mobile")
def revoke_mobile_access(
    db=Depends(_legacy.database.get_db),
    current_user=Depends(_legacy.require_permission("admin")),
):
    """Immediately revoke this cabinet's existing mobile sessions.

    Revocation is persisted before key rotation.  Therefore even if rotation
    fails, previously issued mobile JWTs and unconsumed pairing codes are already
    invalidated (fail closed).
    """
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
