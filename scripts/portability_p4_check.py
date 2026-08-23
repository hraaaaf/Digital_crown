from __future__ import annotations

import asyncio
import datetime
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _package(name: str, path: Path) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    module.__package__ = name
    sys.modules[name] = module
    if "." in name:
        parent_name, child = name.rsplit(".", 1)
        parent = sys.modules.get(parent_name)
        if parent is not None:
            setattr(parent, child, module)
    return module


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    if "." in name:
        parent_name, child = name.rsplit(".", 1)
        parent = sys.modules.get(parent_name)
        if parent is not None:
            setattr(parent, child, module)
    spec.loader.exec_module(module)
    return module


def _install_firebase_stub() -> None:
    firebase_admin = types.ModuleType("firebase_admin")
    firebase_admin.firestore = types.SimpleNamespace(client=lambda: None)
    firebase_admin.credentials = types.SimpleNamespace(Certificate=lambda _path: object())
    firebase_admin.initialize_app = lambda _cred: None
    sys.modules["firebase_admin"] = firebase_admin


class _FakeDoc:
    def __init__(self, exists: bool, data: dict | None = None):
        self.exists = exists
        self._data = data or {}

    def to_dict(self):
        return dict(self._data)


class _FakeDocRef:
    def __init__(self, doc: _FakeDoc):
        self._doc = doc

    def get(self):
        return self._doc


class _FakeCollection:
    def __init__(self, doc: _FakeDoc):
        self._doc = doc

    def document(self, _clinic_id: str):
        return _FakeDocRef(self._doc)


class _FakeFirestore:
    def __init__(self, doc: _FakeDoc):
        self._doc = doc

    def collection(self, _name: str):
        return _FakeCollection(self._doc)


async def _exercise_license_policy(LicenseService, root: Path) -> None:
    os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(root / "appdata")
    os.environ.pop("CABINET_MASTER_KEY_HEX", None)
    os.environ.pop("SECRET_KEY", None)

    LicenseService._instance = None
    LicenseService._db = None
    service = LicenseService()
    service._db = None

    try:
        service._get_fernet()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Missing destination-local vault secret was accepted")

    os.environ["SECRET_KEY"] = "default-dc-fallback-key"
    try:
        service._get_fernet()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Historical predictable vault fallback was accepted")

    os.environ["CABINET_MASTER_KEY_HEX"] = "ab" * 32
    os.environ["SECRET_KEY"] = "p4-cert-secret-" + ("x" * 32)
    now = datetime.datetime.now(datetime.timezone.utc)
    expiry = now + datetime.timedelta(days=10)
    proof = {
        "clinic_id": "cabinet-p4",
        "last_validated": (now - datetime.timedelta(hours=1)).isoformat(),
        "expiration_date": expiry.isoformat(),
        "max_seen_time": (now - datetime.timedelta(minutes=1)).isoformat(),
    }
    service._write_local_vault(proof)
    first_vault = service._vault_path()
    assert first_vault.exists()
    if os.name != "nt":
        assert (first_vault.stat().st_mode & 0o777) == 0o600
    assert not list(first_vault.parent.glob(f".{first_vault.name}.*.tmp"))

    result = await service.validate_license_with_expiry("cabinet-p4")
    assert result["active"] is None and result["source"] == "unavailable"
    assert await service.validate_license("cabinet-p4") is True

    service._write_local_vault({
        **proof,
        "last_validated": (now - datetime.timedelta(hours=73)).isoformat(),
        "max_seen_time": (now - datetime.timedelta(minutes=1)).isoformat(),
    })
    assert await service.validate_license("cabinet-p4") is False

    service._write_local_vault({
        **proof,
        "last_validated": now.isoformat(),
        "max_seen_time": (now + datetime.timedelta(minutes=5)).isoformat(),
    })
    assert await service.validate_license("cabinet-p4") is False

    service._write_local_vault(proof)
    service._db = _FakeFirestore(_FakeDoc(True, {"active": False}))
    result = await service.validate_license_with_expiry("cabinet-p4")
    assert result["active"] is False and result["source"] == "firebase"
    assert not service._vault_path().exists()

    service._db = _FakeFirestore(_FakeDoc(True, {"active": True, "expiration_date": expiry}))
    result = await service.validate_license_with_expiry("cabinet-p4")
    assert result["active"] is True and result["source"] == "firebase"
    assert service._read_local_vault()["clinic_id"] == "cabinet-p4"

    source_dir = root / "source-machine"
    destination_dir = root / "destination-machine"
    os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(source_dir)
    os.environ["CABINET_MASTER_KEY_HEX"] = "11" * 32
    service._write_local_vault(proof)
    source_vault = service._vault_path()
    source_blob = source_vault.read_bytes()

    os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(destination_dir)
    os.environ["CABINET_MASTER_KEY_HEX"] = "22" * 32
    destination_vault = service._vault_path()
    destination_vault.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_vault, destination_vault)
    assert service._read_local_vault() == {}
    assert destination_vault.read_bytes() == source_blob


def _exercise_content_marker(rebind_module, root: Path) -> None:
    generic = root / "generic.zip"
    renamed = root / "renamed.zip"
    with zipfile.ZipFile(generic, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "digital-crown-guided-restore",
            "version": 1,
        }))
    with zipfile.ZipFile(renamed, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "digital-crown-guided-restore",
            "version": 1,
            "portable": {"source": {"os": "windows"}, "config": {}},
        }))
    assert rebind_module.is_portable_restore_archive(generic) is False
    assert rebind_module.is_portable_restore_archive(renamed) is True


def _exercise_rebind_runtime(rebind_module) -> None:
    class _Column:
        def __eq__(self, _other):
            return True

    class _CabinetConfigModel:
        pass

    class _UserModel:
        id = _Column()

    config = types.SimpleNamespace(owner_id=7, clinic_id="cabinet-p4", public_id="public-p4")
    owner = types.SimpleNamespace(id=7, is_licensed=True, license_expires_at="future")

    class _Query:
        def __init__(self, model):
            self.model = model

        def all(self):
            return [config] if self.model is _CabinetConfigModel else []

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return owner if self.model is _UserModel else None

    class _Session:
        def __init__(self):
            self.flushes = 0

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, model):
            return _Query(model)

        def flush(self):
            self.flushes += 1

    class _Engine:
        def __init__(self):
            self.disposals = 0

        def dispose(self):
            self.disposals += 1

    class _Blacklist:
        def __init__(self, fail=False):
            self.fail = fail
            self.calls = []

        def revoke_mobile_access(self, employer_id, db):
            self.calls.append((employer_id, db))
            if self.fail:
                raise RuntimeError("forced revoke failure")
            return {"pairing_tokens_invalidated": 1}

    backend_pkg = sys.modules["backend"]
    database_mod = types.ModuleType("backend.database")
    models_mod = types.ModuleType("backend.models")
    security_mod = types.ModuleType("backend.security")
    session = _Session()
    engine = _Engine()
    blacklist = _Blacklist()
    database_mod.engine = engine
    database_mod.SessionLocal = lambda: session
    models_mod.CabinetConfig = _CabinetConfigModel
    models_mod.User = _UserModel
    security_mod.token_blacklist = blacklist
    sys.modules["backend.database"] = database_mod
    sys.modules["backend.models"] = models_mod
    sys.modules["backend.security"] = security_mod
    backend_pkg.database = database_mod
    backend_pkg.models = models_mod
    backend_pkg.security = security_mod

    result = rebind_module.rebind_portable_restore()
    assert result["cabinet_count"] == 1
    assert result["licence_revalidation_required"] is True
    assert owner.is_licensed is False and owner.license_expires_at is None
    assert blacklist.calls == [(7, session)]
    assert session.flushes == 1
    assert engine.disposals == 2

    owner.is_licensed = True
    owner.license_expires_at = "future"
    failing_engine = _Engine()
    database_mod.engine = failing_engine
    security_mod.token_blacklist = _Blacklist(fail=True)
    try:
        rebind_module.rebind_portable_restore()
    except RuntimeError as exc:
        assert "forced revoke failure" in str(exc)
    else:
        raise AssertionError("Rebind failure did not propagate")
    assert failing_engine.disposals == 2


def _assert_source_contracts() -> None:
    route = (ROOT / "backend/routers/license_portability_p4.py").read_text(encoding="utf-8")
    routers = (ROOT / "backend/routers/__init__.py").read_text(encoding="utf-8")
    rebind = (ROOT / "backend/services/portability_license_rebind.py").read_text(encoding="utf-8")
    security = (ROOT / "backend/security.py").read_text(encoding="utf-8")
    worker = (ROOT / "backend/services/guided_restore_worker.py").read_text(encoding="utf-8")
    bundle = (ROOT / "backend/services/cabinet_bundle.py").read_text(encoding="utf-8")

    assert 'os.getenv("CLINIC_ID"' not in route
    assert "current_user.get_employer_id()" in route
    assert "models.CabinetConfig.owner_id == employer_id" in route
    assert "validate_license_with_expiry(clinic_id)" in route
    assert 'result.get("active") is None' in route
    assert "status_code=503" in route
    assert "owner.is_licensed = license_ok" in route
    assert 'getattr(route, "path", None) == "/recheck-license"' in routers
    assert "clinics.router.include_router(license_portability_p4.router)" in routers

    assert "token_blacklist.revoke_mobile_access(owner.id, db)" in rebind
    assert "finally:" in rebind and "database.engine.dispose()" in rebind
    assert "def revoke_mobile_access" in security
    assert "token_blacklist = TokenBlacklist()" in security

    assert 'endswith(".dcbundle")' not in worker
    assert 'is_portable_restore_archive(job_dir / "source.upload")' in worker
    assert "_rescue_license_vault" in worker
    assert "_restore_license_vault" in worker
    assert "rebind_portable_restore()" in worker
    assert '"portable": {' in bundle

    for forbidden in (".env", "backup.key", "license_vault.bin"):
        assert forbidden in bundle


def main() -> None:
    _package("backend", ROOT / "backend")
    _package("backend.core", ROOT / "backend" / "core")
    _package("backend.services", ROOT / "backend" / "services")
    _install_firebase_stub()
    _load("backend.core.platform", ROOT / "backend/core/platform.py")
    _load("backend.core.paths", ROOT / "backend/core/paths.py")
    license_module = _load("backend.services.license_service", ROOT / "backend/services/license_service.py")
    rebind_module = _load(
        "backend.services.portability_license_rebind",
        ROOT / "backend/services/portability_license_rebind.py",
    )

    with tempfile.TemporaryDirectory(prefix="digitalcrown-p4-cert-") as temp_name:
        root = Path(temp_name)
        asyncio.run(_exercise_license_policy(license_module.LicenseService, root))
        _exercise_content_marker(rebind_module, root)

    _exercise_rebind_runtime(rebind_module)
    _assert_source_contracts()
    print("PORTABILITY_P4_OK")


if __name__ == "__main__":
    main()
