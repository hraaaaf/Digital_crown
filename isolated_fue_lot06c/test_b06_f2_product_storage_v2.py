"""F2: synthetic product-storage integration FUE (no database, no clinical data)."""
import hashlib
from pathlib import PurePosixPath
from types import SimpleNamespace

import pytest

from backend.services import clinical_asset_storage as storage

PLAINTEXT = b"synthetic-dental-imaging-f2-no-patient"
DIGEST = hashlib.sha256(PLAINTEXT).hexdigest()


class FakeDB:
    def flush(self):
        pass


@pytest.fixture
def asset_fixture(monkeypatch, tmp_path):
    asset = SimpleNamespace(
        id=101, employer_id=7, patient_id=23,
        sha256=None, byte_size=None, storage_key=None,
        storage_format=None, stored_at=None,
    )
    monkeypatch.setattr(
        storage, "get_clinical_asset_for_patient",
        lambda _db, *, employer_id, patient_id, asset_id: asset
        if (employer_id, patient_id, asset_id) == (7, 23, 101) else None,
    )
    monkeypatch.setenv("DC_MEDIA_V2_OPT_IN", "true")
    monkeypatch.setenv("DC_MEDIA_V2_ACTIVE_KEY_ID", "media1")
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_ID", "loc1")
    monkeypatch.setenv("DC_MEDIA_V2_MEDIA_KEY_HEX", "01" * 32)
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_HEX", "02" * 32)
    return asset, FakeDB(), tmp_path


def _path(root, asset):
    return root.joinpath(*PurePosixPath(asset.storage_key).parts)


def _store(asset, db, root):
    return storage.store_clinical_asset_bytes(
        db, employer_id=7, patient_id=23, asset_id=101,
        content=PLAINTEXT, media_root=root,
    )


def _read(asset, db, root):
    return storage.read_clinical_asset_bytes(
        db, employer_id=7, patient_id=23, asset_id=101, media_root=root,
    )


def test_f2_01_product_dcm2_store_read_and_metadata(asset_fixture):
    asset, db, root = asset_fixture
    assert _store(asset, db, root).deduplicated is False
    assert asset.storage_format == "AESGCM_V2"
    assert asset.sha256 == DIGEST
    assert asset.storage_key.startswith("clinical-assets/v2-loc1-t-")
    assert DIGEST not in asset.storage_key
    assert _path(root, asset).read_bytes().startswith(b"DCM2")
    assert _read(asset, db, root) == PLAINTEXT


def test_f2_02_dedup_and_tamper_denied(asset_fixture):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    assert _store(asset, db, root).deduplicated is True
    path = _path(root, asset)
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(payload)
    with pytest.raises(storage.ClinicalAssetIntegrityError):
        _read(asset, db, root)
    with pytest.raises(storage.ClinicalAssetIntegrityError):
        _store(asset, db, root)


def test_f2_03_wrong_media_key_denied(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    monkeypatch.setenv("DC_MEDIA_V2_MEDIA_KEY_HEX", "03" * 32)
    with pytest.raises(storage.ClinicalAssetIntegrityError):
        _read(asset, db, root)


def test_f2_04_wrong_locator_key_denied(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_HEX", "04" * 32)
    with pytest.raises(storage.ClinicalAssetStorageError, match="locator mismatch"):
        _read(asset, db, root)


def test_f2_05_cross_tenant_denied(asset_fixture):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    with pytest.raises(storage.ClinicalAssetStorageError):
        storage.read_clinical_asset_bytes(
            db, employer_id=8, patient_id=23, asset_id=101, media_root=root,
        )


def test_f2_06_missing_configuration_denied_before_write(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    monkeypatch.delenv("DC_MEDIA_V2_LOCATOR_KEY_HEX")
    with pytest.raises(storage.ClinicalAssetStorageError):
        _store(asset, db, root)
    assert list(root.rglob("*.dcm")) == []


def test_f2_07_v2_read_independent_of_opt_in_write_switch(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    monkeypatch.delenv("DC_MEDIA_V2_OPT_IN")
    assert _read(asset, db, root) == PLAINTEXT


def test_f3_01_read_old_blob_after_both_key_rotations(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    old_key = asset.storage_key
    monkeypatch.setenv("DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON", '{"media1":"' + "01" * 32 + '"}')
    monkeypatch.setenv("DC_MEDIA_V2_RETAINED_LOCATOR_KEYS_JSON", '{"loc1":"' + "02" * 32 + '"}')
    monkeypatch.setenv("DC_MEDIA_V2_ACTIVE_KEY_ID", "media2")
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_ID", "loc2")
    monkeypatch.setenv("DC_MEDIA_V2_MEDIA_KEY_HEX", "03" * 32)
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_HEX", "04" * 32)
    assert _read(asset, db, root) == PLAINTEXT
    assert asset.storage_key == old_key


def test_f3_02_missing_retained_media_key_denied(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    monkeypatch.setenv("DC_MEDIA_V2_RETAINED_LOCATOR_KEYS_JSON", '{"loc1":"' + "02" * 32 + '"}')
    monkeypatch.setenv("DC_MEDIA_V2_ACTIVE_KEY_ID", "media2")
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_ID", "loc2")
    monkeypatch.setenv("DC_MEDIA_V2_MEDIA_KEY_HEX", "03" * 32)
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_HEX", "04" * 32)
    with pytest.raises(storage.ClinicalAssetIntegrityError):
        _read(asset, db, root)


def test_f3_03_missing_retained_locator_key_denied(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    _store(asset, db, root)
    monkeypatch.setenv("DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON", '{"media1":"' + "01" * 32 + '"}')
    monkeypatch.setenv("DC_MEDIA_V2_ACTIVE_KEY_ID", "media2")
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_ID", "loc2")
    monkeypatch.setenv("DC_MEDIA_V2_MEDIA_KEY_HEX", "03" * 32)
    monkeypatch.setenv("DC_MEDIA_V2_LOCATOR_KEY_HEX", "04" * 32)
    with pytest.raises(storage.ClinicalAssetStorageError):
        _read(asset, db, root)


def test_f3_04_conflicting_active_key_registry_denied(asset_fixture, monkeypatch):
    asset, db, root = asset_fixture
    monkeypatch.setenv("DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON", '{"media1":"' + "ff" * 32 + '"}')
    with pytest.raises(storage.ClinicalAssetStorageError):
        _store(asset, db, root)
    assert list(root.rglob("*.dcm")) == []
