from __future__ import annotations

import os
from pathlib import Path

from backend.core.paths import AppPaths


# Historique : n'acceptait que le literal exact "e2e_install_rehearsal". Généralisé
# (REAL-BUILD-RUNTIME-ISOLATION-GUARD-1) après la Phase B de Treatment Journey — un
# environnement rehearsal ad hoc nommé différemment (ex. "treatment_journey_rehearsal")
# passait à côté de cette validation stricte. Tout ENVIRONMENT contenant "rehearsal"
# (insensible à la casse) est désormais traité comme un rehearsal.
REHEARSAL_ENVIRONMENT = "e2e_install_rehearsal"  # conservé pour compat/référence historique


def get_real_media_root() -> Path:
    return AppPaths.get_user_data_dir() / "media"


def is_rehearsal_environment(environment: str | None = None) -> bool:
    value = (environment or os.environ.get("ENVIRONMENT", "")).strip().lower()
    return "rehearsal" in value


def _is_unsafe_rehearsal_media_root(media_root: Path) -> bool:
    normalized = str(media_root.resolve(strict=False)).replace("\\", "/").lower()
    real_media = str(get_real_media_root().resolve(strict=False)).replace("\\", "/").lower()
    return normalized == real_media or "digitalcrown/media" in normalized


def validate_media_root(media_root: Path, environment: str | None = None) -> Path:
    resolved = media_root.expanduser().resolve(strict=False)
    if is_rehearsal_environment(environment):
        if _is_unsafe_rehearsal_media_root(resolved):
            raise RuntimeError("Unsafe MEDIA_ROOT for rehearsal")
        # Le dossier de sortie doit lui-même être identifiable comme un dossier de
        # rehearsal (contenir "rehearsal") — pas seulement "ne pas être le dossier réel".
        if "rehearsal" not in str(resolved).replace("\\", "/").lower():
            raise RuntimeError("Unsafe MEDIA_ROOT for rehearsal")
    return resolved


def get_media_root() -> Path:
    media_root_env = os.environ.get("MEDIA_ROOT", "").strip()
    environment = os.environ.get("ENVIRONMENT", "")
    if is_rehearsal_environment(environment):
        if not media_root_env:
            raise RuntimeError("Unsafe MEDIA_ROOT for rehearsal")
        return validate_media_root(Path(media_root_env), environment)

    if media_root_env:
        return validate_media_root(Path(media_root_env), environment)

    return get_real_media_root()
