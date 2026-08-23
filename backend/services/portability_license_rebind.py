from __future__ import annotations

from typing import Any


def rebind_portable_restore() -> dict[str, Any]:
    """
    Rebind machine-local security state after a .dcbundle restore.

    Cabinet/business identity remains in the restored database. Machine secrets
    are destination-owned (P3 excludes .env/backup.key/license_vault.bin), so the
    restored owner must re-prove the licence and all mobile pairing state is
    revoked before the application restarts.
    """
    from backend import database, models
    from backend.security import token_blacklist

    # Never reuse a pooled handle opened before the DB file replacement.
    database.engine.dispose()

    rebound: list[dict[str, Any]] = []
    with database.SessionLocal() as db:
        configs = db.query(models.CabinetConfig).all()
        if not configs:
            raise RuntimeError("Cabinet restauré sans CabinetConfig : rebind refusé")

        for config in configs:
            owner = db.query(models.User).filter(models.User.id == config.owner_id).first()
            if not owner:
                raise RuntimeError(
                    f"Cabinet restauré sans propriétaire valide (owner_id={config.owner_id})"
                )

            clinic_id = str(config.clinic_id or config.public_id or "").strip()
            if not clinic_id:
                raise RuntimeError(
                    f"Cabinet restauré sans identité de licence (owner_id={config.owner_id})"
                )

            # The source machine's cached licence state is not portable. Startup
            # will revalidate online, or fail closed if no destination vault exists.
            owner.is_licensed = False
            owner.license_expires_at = None
            db.flush()

            # Invalidates all mobile JWTs issued before this epoch and destroys
            # unused ZKA pairing tokens copied inside the restored database.
            token_blacklist.revoke_mobile_access(owner.id, db)

            rebound.append(
                {
                    "owner_id": owner.id,
                    "clinic_id": clinic_id,
                    "mobile_access_revoked": True,
                }
            )

    database.engine.dispose()
    return {
        "cabinet_count": len(rebound),
        "licence_revalidation_required": True,
        "mobile_access_revoked": True,
        "cabinets": rebound,
    }
