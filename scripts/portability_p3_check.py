from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
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


# Load the portability slice without executing backend/__init__.py.  The
# tri-OS workflow intentionally installs only stdlib-adjacent dependencies;
# loading the full application here would turn this contract test into a second
# copy of the heavyweight backend CI.
_package("backend", ROOT / "backend")
_package("backend.core", ROOT / "backend" / "core")
_package("backend.services", ROOT / "backend" / "services")

platform_module = _load("backend.core.platform", ROOT / "backend" / "core" / "platform.py")
_load("backend.core.paths", ROOT / "backend" / "core" / "paths.py")
_load("backend.core.media_paths", ROOT / "backend" / "core" / "media_paths.py")
backup_module = _load("backend.services.backup_service", ROOT / "backend" / "services" / "backup_service.py")
archive_module = _load(
    "backend.services.guided_restore_archive",
    ROOT / "backend" / "services" / "guided_restore_archive.py",
)
bundle_module = _load("backend.services.cabinet_bundle", ROOT / "backend" / "services" / "cabinet_bundle.py")

get_platform_adapter = platform_module.get_platform_adapter
BackupService = backup_module.BackupService
CabinetBundleService = bundle_module.CabinetBundleService
_extract_encrypted_media = archive_module._extract_encrypted_media

SECRET = "portable bundle certification phrase 2026"


def make_database(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
    conn.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, nom TEXT)")
    conn.execute("CREATE TABLE truth (value TEXT NOT NULL)")
    conn.execute("INSERT INTO truth(value) VALUES ('portable-ok')")
    conn.execute("PRAGMA user_version = 63")
    conn.commit()
    conn.close()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="digitalcrown-p3-cert-") as temp_name:
        root = Path(temp_name)
        os.environ["DIGITALCROWN_USER_DATA_DIR"] = str(root / "appdata")
        os.environ["CABINET_MASTER_KEY_HEX"] = "ab" * 32
        os.environ["CABINET_PORT"] = "8005"

        database = root / "source.db"
        make_database(database)
        media = root / "media"
        (media / "radios").mkdir(parents=True)
        (media / "radios" / "pano.jpg").write_bytes(b"portable-media")

        bundle = root / "cabinet.dcbundle"
        CabinetBundleService.create_bundle(bundle, SECRET, database_path=database, media_root=media)
        local_restore = root / "local.zip"
        CabinetBundleService.to_local_guided_restore_archive(
            bundle,
            SECRET,
            local_restore,
            active_engine=("sqlite", "pysqlite"),
        )

        with zipfile.ZipFile(bundle, "r") as archive:
            manifest = json.loads(archive.read("manifest.json"))
            assert manifest["source"]["os"] == get_platform_adapter().kind
            assert manifest["source"]["architecture"] == get_platform_adapter().architecture
            assert manifest["kdf"]["n"] == 2**17
            assert manifest["cipher"]["name"] == "AES-256-GCM"

        with zipfile.ZipFile(local_restore, "r") as archive:
            db_encrypted = archive.read("database.db.enc")
            plain = root / "restored.db"
            plain.write_bytes(BackupService._get_or_create_key().decrypt(db_encrypted))
            conn = sqlite3.connect(str(plain))
            try:
                assert conn.execute("SELECT value FROM truth").fetchone()[0] == "portable-ok"
                assert conn.execute("PRAGMA user_version").fetchone()[0] == 63
            finally:
                conn.close()
            media_encrypted = root / "media.enc"
            media_encrypted.write_bytes(archive.read("media.zip.enc"))

        restored_media = root / "restored-media"
        _extract_encrypted_media(media_encrypted, restored_media)
        assert (restored_media / "radios" / "pano.jpg").read_bytes() == b"portable-media"

        try:
            CabinetBundleService.to_local_guided_restore_archive(
                bundle,
                "wrong portable bundle phrase",
                root / "must-not-exist.zip",
                active_engine=("sqlite", "pysqlite"),
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong migration secret was accepted")

    print(f"PORTABILITY_P3_OK runner={get_platform_adapter().kind}")


if __name__ == "__main__":
    main()
