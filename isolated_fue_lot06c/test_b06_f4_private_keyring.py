"""F4 private DCM2 keyring configuration; synthetic keys only."""
import json
import os
import pytest
from backend.services.clinical_media_crypto_v2 import configured_keyring, MediaCryptoV2Denied

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX permission gate")


@pytest.fixture
def keyfile(monkeypatch, tmp_path):
    for name in ("DC_MEDIA_V2_ACTIVE_KEY_ID", "DC_MEDIA_V2_LOCATOR_KEY_ID",
                 "DC_MEDIA_V2_MEDIA_KEY_HEX", "DC_MEDIA_V2_LOCATOR_KEY_HEX",
                 "DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON", "DC_MEDIA_V2_RETAINED_LOCATOR_KEYS_JSON"):
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / "synthetic-keyring.json"
    data = {
        "active_media_id": "media2", "active_locator_id": "loc2",
        "media_keys": {"media1": "01" * 32, "media2": "03" * 32},
        "locator_keys": {"loc1": "02" * 32, "loc2": "04" * 32},
    }
    path.write_text(json.dumps(data))
    path.chmod(0o600)
    monkeypatch.setenv("DC_MEDIA_V2_KEYRING_FILE", str(path))
    return path, data


def test_f4_01_private_file_loads_active_and_historical_keys(keyfile):
    ring, media_id, locator_id = configured_keyring()
    assert (media_id, locator_id) == ("media2", "loc2")
    assert set(ring.media_keys) == {"media1", "media2"}
    assert set(ring.locator_keys) == {"loc1", "loc2"}


def test_f4_02_world_readable_file_denied(keyfile):
    path, _ = keyfile
    path.chmod(0o644)
    with pytest.raises(MediaCryptoV2Denied, match="INSECURE_KEYRING_FILE"):
        configured_keyring()


def test_f4_03_symlink_denied(keyfile, monkeypatch, tmp_path):
    path, _ = keyfile
    link = tmp_path / "link"
    link.symlink_to(path)
    monkeypatch.setenv("DC_MEDIA_V2_KEYRING_FILE", str(link))
    with pytest.raises(MediaCryptoV2Denied, match="INSECURE_KEYRING_FILE"):
        configured_keyring()


def test_f4_04_mixed_environment_source_denied(keyfile, monkeypatch):
    monkeypatch.setenv("DC_MEDIA_V2_MEDIA_KEY_HEX", "03" * 32)
    with pytest.raises(MediaCryptoV2Denied, match="MIXED_KEYRING_SOURCES"):
        configured_keyring()


def test_f4_05_malformed_file_denied(keyfile):
    path, _ = keyfile
    path.write_text("{")
    with pytest.raises(MediaCryptoV2Denied, match="INVALID_KEYRING_FILE"):
        configured_keyring()


def test_f4_06_key_purpose_reuse_denied(keyfile):
    path, data = keyfile
    data["locator_keys"]["loc2"] = data["media_keys"]["media2"]
    path.write_text(json.dumps(data))
    with pytest.raises(MediaCryptoV2Denied, match="KEY_PURPOSE_REUSE_DENIED"):
        configured_keyring()


def test_f4_07_missing_active_key_denied(keyfile):
    path, data = keyfile
    del data["media_keys"]["media2"]
    path.write_text(json.dumps(data))
    with pytest.raises(MediaCryptoV2Denied, match="KEY_UNAVAILABLE"):
        configured_keyring()
