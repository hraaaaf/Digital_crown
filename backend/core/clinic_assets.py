from pathlib import Path, PureWindowsPath

from backend.core.media_paths import get_media_root


def resolve_clinic_asset(value, legacy_root, public_id=None):
    """Read mutable branding from media storage, retaining legacy installations."""
    if not value:
        return None
    relative = str(value).replace("\\", "/")
    path = Path(relative)
    if path.is_absolute() or PureWindowsPath(relative).drive or ".." in path.parts:
        return None
    if "\x00" in relative:
        return None
    if public_id and path.parts and path.parts[0] == "clinics":
        if len(path.parts) < 3 or path.parts[1] != str(public_id):
            return None
    for root in (get_media_root(), Path(legacy_root)):
        root = root.resolve()
        candidate = (root / path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return str(candidate)
    return None
