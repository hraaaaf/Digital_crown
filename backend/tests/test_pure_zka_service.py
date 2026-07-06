"""Unit tests for services/zka_service.py — AES-GCM encrypt/decrypt via ZKAService."""
import os
import pytest
import tempfile
from backend.services.zka_service import ZKAService


TEST_KEY = os.urandom(32).hex()  # 256-bit key


class TestEncryptDecrypt:
    def test_encrypt_returns_base64_string(self):
        blob = ZKAService.encrypt_payload({"a": 1}, TEST_KEY)
        assert isinstance(blob, str)
        assert len(blob) > 0

    def test_decrypt_roundtrip(self):
        data = {"patient_id": 42, "secret": "clinical note"}
        blob = ZKAService.encrypt_payload(data, TEST_KEY)
        result = ZKAService.decrypt_payload(blob, TEST_KEY)
        assert result == data

    def test_same_data_different_ciphertext(self):
        data = {"x": "y"}
        blob1 = ZKAService.encrypt_payload(data, TEST_KEY)
        blob2 = ZKAService.encrypt_payload(data, TEST_KEY)
        assert blob1 != blob2  # Different IV each time

    def test_complex_payload(self):
        data = {"nested": {"list": [1, 2, 3]}, "bool": True, "null": None}
        blob = ZKAService.encrypt_payload(data, TEST_KEY)
        result = ZKAService.decrypt_payload(blob, TEST_KEY)
        assert result == data

    def test_wrong_key_raises(self):
        blob = ZKAService.encrypt_payload({"a": 1}, TEST_KEY)
        wrong_key = os.urandom(32).hex()
        with pytest.raises(Exception):
            ZKAService.decrypt_payload(blob, wrong_key)

    def test_tampered_blob_raises(self):
        blob = ZKAService.encrypt_payload({"a": 1}, TEST_KEY)
        tampered = blob[:-4] + "XXXX"
        with pytest.raises(Exception):
            ZKAService.decrypt_payload(tampered, TEST_KEY)


class TestGenerateMasterKey:
    def test_returns_hex_string(self):
        key = ZKAService.generate_master_key()
        assert isinstance(key, str)
        assert len(key) == 64  # 32 bytes = 64 hex chars

    def test_different_keys_each_call(self):
        k1 = ZKAService.generate_master_key()
        k2 = ZKAService.generate_master_key()
        assert k1 != k2

    def test_valid_hex(self):
        key = ZKAService.generate_master_key()
        bytes.fromhex(key)  # Should not raise


class TestRotateMasterKey:
    def test_rotate_creates_key_in_env_file(self):
        svc = ZKAService()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OTHER_KEY=value\n")
            f.write("CABINET_MASTER_KEY_HEX=oldhexkey\n")
            tmp_path = f.name

        try:
            new_key = svc.rotate_master_key(tmp_path)
            assert len(new_key) == 64
            with open(tmp_path, 'r') as f:
                content = f.read()
            assert f"CABINET_MASTER_KEY_HEX={new_key}" in content
            assert "oldhexkey" not in content
        finally:
            os.unlink(tmp_path)

    def test_rotate_adds_key_if_missing(self):
        svc = ZKAService()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OTHER_KEY=value\n")
            tmp_path = f.name

        try:
            new_key = svc.rotate_master_key(tmp_path)
            with open(tmp_path, 'r') as f:
                content = f.read()
            assert f"CABINET_MASTER_KEY_HEX={new_key}" in content
        finally:
            os.unlink(tmp_path)

    def test_rotate_nonexistent_env_file(self):
        svc = ZKAService()
        new_key = svc.rotate_master_key("/nonexistent/path/.env")
        assert len(new_key) == 64  # Should still return a key
