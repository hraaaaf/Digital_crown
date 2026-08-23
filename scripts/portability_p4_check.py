from __future__ import annotations

import asyncio
import importlib.util
import os
import shutil
import sys
import tempfile
import types
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
    firebase = types.ModuleType("firebase_admin")
    firebase.firestore = types.SimpleNamespace(client=lambda: None)
    firebase.credentials = types.SimpleNamespace(Certificate=lambda _path: object())
    firebase.initialize_app = lambda _cred: None
    sys.modules["firebase_admin"] = firebase


_package("backend", ROOT / "backend")
_package("backend.core", ROOT / "backend" / "core")
_package("backend.services", ROOT / "backend" / "services")
_install_firebase_stub()

platform_module = _load("backend.core.platform", ROOT / "backend" / "core" / "platform.py")
paths_module = _load("backend.core.paths", ROOT / "backend" / "core" / "paths.py")
license_module = _load(
    "backend.services.license_service",
    ROOT / "backend" / "services" / "license_service.py",
)

AppPaths = paths_module.AppPaths
LicenseService = license_module.LicenseService
get_platform_adapter = platform_module.get_platform_adapter


class _ActiveLicenseDocument:
    exists = True

    def to_dict(self):
        return {"active": True, "expiration_date": None}


class _ActiveLicenseDocumentRef:
    def get(self):
        return _ActiveLicenseDocument()


class _ActiveLicenseCollection:
    def document(self, _clinic_id: str):
        return _ActiveLicenseDocumentRef()


class _ActiveLicenseDb:
    def collection(self, name: str):
        assert name == "licenses"
        return _ActiveLicenseCollection()


def _fresh_service():
    LicenseService._instance = None
    LicenseService._db = None
    service = LicenseService()
    service._db = None
    return service


def _set_local_machine(root: Path, secret: str) -> None:
    os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(root)
    os.environ["CABINET_MASTER_KEY_HEX"] = secret
    os.environ["SECRET_KEY"] = f"jwt-{secret}"


def _clear_local_secrets() -> None:
    os.environ.pop("CABINET_MASTER_KEY_HEX", None)
    os.environ.pop("SECRET_KEY", None)


def _authoritative_rebind(service, clinic_id: str) -> None:
    service._db = _ActiveLicenseDb()
    try:
        assert asyncio.run(service.validate_license(clinic_id)) is True
    finally:
        service._db = None
    assert service._read_local_vault()["clinic_id"] == clinic_id


def main() -> None:
    clinic_id = "portable-cabinet-p4"

    with tempfile.TemporaryDirectory(prefix="digitalcrown-p4-cert-") as temp_name:
        root = Path(temp_name)
        source = root / "source-machine"
        destination = root / "destination-machine"
        source_secret = "11" * 32
        destination_secret = "22" * 32

        # Source machine: exercise the real authoritative validation path so the
        # offline proof is created by production logic, not by the harness.
        _set_local_machine(source, source_secret)
        source_service = _fresh_service()
        _authoritative_rebind(source_service, clinic_id)
        assert asyncio.run(source_service.validate_license(clinic_id)) is True
        source_vault = AppPaths.get_user_data_dir() / "license_vault.bin"
        assert source_vault.exists() and source_vault.stat().st_size > 0

        # A copied source vault must be unusable with destination-local keys.
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_vault, destination / "license_vault.bin")
        _set_local_machine(destination, destination_secret)
        destination_service = _fresh_service()
        assert destination_service._read_local_vault() == {}
        assert asyncio.run(destination_service.validate_license(clinic_id)) is False

        # Destination rebind uses the actual authoritative path and creates a
        # fresh vault encrypted with the destination secret.
        assert destination_service.clear_local_vault_for_rebind() is True
        assert not (destination / "license_vault.bin").exists()
        _authoritative_rebind(destination_service, clinic_id)
        assert asyncio.run(destination_service.validate_license(clinic_id)) is True

        # Reboot/update semantics: a fresh service instance can still use the
        # destination-local offline proof without source-machine material.
        restarted_service = _fresh_service()
        assert restarted_service._read_local_vault()["clinic_id"] == clinic_id
        assert asyncio.run(restarted_service.validate_license(clinic_id)) is True

        # If the anti-rollback marker cannot be persisted, offline validation
        # must fail closed rather than silently weakening the clock defense.
        persistence_failure_service = _fresh_service()
        assert persistence_failure_service._read_local_vault()["clinic_id"] == clinic_id
        persistence_failure_service._write_local_vault = lambda _data: False
        assert asyncio.run(persistence_failure_service.validate_license(clinic_id)) is False

        # Corrupt local state fails closed offline, but authoritative online
        # validation can safely recover it by writing a new destination proof.
        (destination / "license_vault.bin").write_bytes(b"corrupt-vault")
        corrupt_service = _fresh_service()
        assert corrupt_service._read_local_vault() == {}
        assert asyncio.run(corrupt_service.validate_license(clinic_id)) is False
        _authoritative_rebind(corrupt_service, clinic_id)
        assert asyncio.run(corrupt_service.validate_license(clinic_id)) is True

        # Missing or known weak key material must never resurrect the historical
        # predictable fallback.
        _clear_local_secrets()
        missing_service = _fresh_service()
        try:
            missing_service._get_fernet()
        except RuntimeError:
            pass
        else:
            raise AssertionError("Missing local secret unexpectedly produced a licence vault key")

        os.environ["SECRET_KEY"] = "default-dc-fallback-key"
        weak_service = _fresh_service()
        try:
            weak_service._get_fernet()
        except RuntimeError:
            pass
        else:
            raise AssertionError("Predictable fallback key was accepted")

        # Static migration/session boundary.
        bundle_source = (ROOT / "backend" / "services" / "cabinet_bundle.py").read_text(encoding="utf-8")
        launcher_source = (ROOT / "run.py").read_text(encoding="utf-8")
        security_source = (ROOT / "backend" / "security.py").read_text(encoding="utf-8")
        licence_source = (ROOT / "backend" / "services" / "license_service.py").read_text(encoding="utf-8")

        assert '"license_vault.bin"' in bundle_source
        assert '"runtime_secrets": "regenerate"' in bundle_source
        assert '"license": "rebind"' in bundle_source
        assert "SECRET_KEY={secrets.token_hex(32)}" in launcher_source
        assert "CABINET_MASTER_KEY_HEX={secrets.token_hex(32)}" in launcher_source
        assert "SECRET_KEY = settings.SECRET_KEY" in security_source
        assert "jwt.encode(to_encode, SECRET_KEY" in security_source
        assert 'os.getenv("SECRET_KEY", "default-dc-fallback-key")' not in licence_source
        assert get_platform_adapter().kind in {"windows", "macos", "linux"}

    print(f"PORTABILITY_P4_OK runner={get_platform_adapter().kind}")


if __name__ == "__main__":
    main()
