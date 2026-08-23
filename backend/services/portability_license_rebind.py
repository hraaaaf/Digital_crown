from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any


def is_portable_restore_archive(source: Path) -> bool:
    """Identify a validated portable restore by its staged manifest, never its filename."""
    if not source.exists() or not zipfile.is_zipfile(source):
        return False
    with zipfile.ZipFile(source, "r") as archive:
        if "manifest.json" not in archive.namelist():
            return False
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    return (
        manifest.get("format") == "digital-crown-guided-restore"
        and isinstance(manifest.get("portable"), dict)
    )


def rebind_portable_restore() -> dict[str, Any]:
    """Rebind machine-local security state after a portable cabinet restore."""
    from backend import database, models
    from backend.security import token_blacklist

    database.engine.dispose()
    try:
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

                owner.is_licensed = False
                owner.license_expires_at = None
                db.flush()
                token_blacklist.revoke_mobile_access(owner.id, db)
                rebound.append({
                    "owner_id": owner.id,
                    "clinic_id": clinic_id,
                    "mobile_access_revoked": True,
                })

        return {
            "cabinet_count": len(rebound),
            "licence_revalidation_required": True,
            "mobile_access_revoked": True,
            "cabinets": rebound,
        }
    finally:
        database.engine.dispose()
