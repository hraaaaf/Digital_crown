from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, got {count}: {old[:80]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_clinics() -> None:
    path = ROOT / "backend/routers/clinics.py"
    text = path.read_text(encoding="utf-8")

    marker = "router = APIRouter()\n\n"
    helper = '''router = APIRouter()\n\n\ndef _has_settings_write_access(current_user: models.User) -> bool:\n    if is_superadmin_user(current_user):\n        return True\n    if current_user.role == models.UserRole.ADMIN:\n        return True\n    if current_user.role == models.UserRole.DENTISTE and current_user.employer_id is None:\n        return True\n    permissions = current_user.permissions or {}\n    return permissions.get(\"settings\") is True\n\n\ndef _require_settings_write(\n    current_user: models.User = Depends(get_current_user),\n) -> models.User:\n    if not _has_settings_write_access(current_user):\n        raise HTTPException(status_code=403, detail=\"Permission Réglages requise.\")\n    return current_user\n\n\ndef _require_setup_owner(\n    current_user: models.User = Depends(get_current_user),\n) -> models.User:\n    if is_superadmin_user(current_user):\n        return current_user\n    if current_user.role not in (models.UserRole.ADMIN, models.UserRole.DENTISTE) or current_user.employer_id is not None:\n        raise HTTPException(status_code=403, detail=\"Initialisation réservée au compte principal.\")\n    return current_user\n\n'''
    if text.count(marker) != 1:
        raise SystemExit("clinics.py: router marker mismatch")
    text = text.replace(marker, helper, 1)

    old_sig = '''def create_clinic(\n    config: schemas.CabinetConfigCreate,\n    db: Session = Depends(get_db)\n):'''
    new_sig = '''def create_clinic(\n    config: schemas.CabinetConfigCreate,\n    db: Session = Depends(get_db),\n    current_user: models.User = Depends(_require_setup_owner),\n):'''
    if old_sig not in text:
        raise SystemExit("clinics.py: create signature mismatch")
    text = text.replace(old_sig, new_sig, 1)

    pattern = re.compile(
        r'''    admin_user = db\.query\(models\.User\)\.filter\(.*?\n    existing_cabinet = db\.query\(models\.CabinetConfig\)\.filter\(models\.CabinetConfig\.owner_id == admin_user\.id\)\.first\(\)''',
        re.S,
    )
    replacement = '''    admin_user = current_user\n\n    existing_cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == admin_user.id).first()'''
    text, n = pattern.subn(replacement, text, count=1)
    if n != 1:
        raise SystemExit(f"clinics.py: ownership block mismatch ({n})")

    get_start = text.index('@router.get("/me")')
    put_start = text.index('@router.put("/me")')
    get_block = text[get_start:put_start]
    get_block_new, n = re.subn(
        r'''    if not config:\n        config = models\.CabinetConfig\(.*?        db\.refresh\(config\)\n''',
        '''    if not config:\n        raise HTTPException(status_code=404, detail=\"Cabinet non configuré\")\n''',
        get_block,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("clinics.py: GET /me create-on-read block mismatch")
    text = text[:get_start] + get_block_new + text[put_start:]

    text = text.replace(
        'current_user: models.User = Depends(get_current_user)\n):\n    """Mettre à jour la configuration du cabinet."""',
        'current_user: models.User = Depends(_require_settings_write)\n):\n    """Mettre à jour la configuration du cabinet."""',
        1,
    )

    put_start = text.index('@router.put("/me")')
    logo_start = text.index('@router.post("/me/logo")')
    put_block = text[put_start:logo_start]
    put_block_new, n = re.subn(
        r'''    if not config:\n        config = models\.CabinetConfig\(.*?        db\.flush\(\)\n''',
        '''    if not config:\n        raise HTTPException(status_code=404, detail=\"Cabinet non configuré\")\n''',
        put_block,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("clinics.py: PUT /me implicit create block mismatch")
    text = text[:put_start] + put_block_new + text[logo_start:]

    text = text.replace(
        'current_user: models.User = Depends(get_current_user)\n):\n    """Uploader le logo du cabinet."""',
        'current_user: models.User = Depends(_require_settings_write)\n):\n    """Uploader le logo du cabinet."""',
        1,
    )
    text = text.replace(
        'current_user: models.User = Depends(get_current_user)\n):\n    """Uploader le papier en-tête (Letterhead) du cabinet."""',
        'current_user: models.User = Depends(_require_settings_write)\n):\n    """Uploader le papier en-tête (Letterhead) du cabinet."""',
        1,
    )

    path.write_text(text, encoding="utf-8")


def patch_schema() -> None:
    replace_once(
        "backend/schemas/cabinet.py",
        '    specialty_ids: List[str] = Field(default_factory=list)\n',
        '    specialty_ids: List[str] = Field(default_factory=list)\n    custom_specialty_fr: Optional[str] = Field(default=None, max_length=255)\n    custom_specialty_ar: Optional[str] = Field(default=None, max_length=255)\n    header_customized: bool = Field(default=False)\n',
    )
    replace_once("backend/schemas/cabinet.py", '    font_fr: str = Field(default="Helvetica", max_length=50)\n', '    font_fr: str = Field(default="inter", max_length=50)\n')
    replace_once("backend/schemas/cabinet.py", '    selected_template: str = Field(default="classic", max_length=20)\n', '    selected_template: str = Field(default="swiss", max_length=20)\n')
    replace_once("backend/schemas/cabinet.py", 'class CabinetConfigCreate(CabinetConfigBase):\n    pass\n', 'class CabinetConfigCreate(CabinetConfigBase):\n    model_config = ConfigDict(extra="forbid", populate_by_name=True)\n')


def patch_models() -> None:
    replace_once(
        "backend/models.py",
        '    specialty_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)\n',
        '    specialty_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)\n    custom_specialty_fr: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)\n    custom_specialty_ar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)\n    header_customized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)\n',
    )
    replace_once("backend/models.py", '    font_fr: Mapped[str] = mapped_column(String(50), default="Helvetica")\n', '    font_fr: Mapped[str] = mapped_column(String(50), default="inter")\n')
    replace_once("backend/models.py", '    selected_template: Mapped[str] = mapped_column(String(20), default="classic", nullable=False)\n', '    selected_template: Mapped[str] = mapped_column(String(20), default="swiss", nullable=False)\n')


def patch_settings_store() -> None:
    replace_once(
        "frontend/src/features/admin/Settings/hooks/useSettingsStore.ts",
        '''      const payload = {\n        ...profile,\n        footer_phones: contactString,\n        contacts_json: contacts\n      };''',
        '''      const { logo_path: _logoPath, ...persistableProfile } = profile;\n      const payload = {\n        ...persistableProfile,\n        footer_phones: contactString,\n        contacts_json: contacts\n      };''',
    )


def patch_offline_ack() -> None:
    replace_once(
        "frontend/src/services/api.ts",
        '''          toast.success('📡 Mode hors-ligne : Action mise en file d\\'attente. Elle sera synchronisée.', { id: 'offline-queue', duration: 4000 });\n          // Résoudre silencieusement pour éviter le crash UI (Background Sync s'en chargera)\n          return Promise.resolve({ data: { _offline: true }, status: 200, statusText: 'OK', headers: {}, config: original });''',
        '''          toast.error('Mode hors-ligne : sauvegarde impossible sans confirmation serveur.', { id: 'offline-write-blocked', duration: 4000 });\n          return Promise.reject(error);''',
    )


patch_clinics()
patch_schema()
patch_models()
patch_settings_store()
patch_offline_ack()
print("P4A deterministic patch applied")
