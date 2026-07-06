"""Tests services/zka_crypto.py — AES-256-GCM encrypt/decrypt."""
import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def set_master_key(monkeypatch):
    # 32 bytes = 256-bit AES key
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "0" * 64)


class TestZkaCrypto:
    def test_encrypt_returns_payload(self):
        from backend.services.zka_crypto import encrypt_payload
        result = encrypt_payload({"hello": "world"})
        assert "payload" in result
        assert isinstance(result["payload"], str)
        assert len(result["payload"]) > 0

    def test_decrypt_roundtrip(self):
        from backend.services.zka_crypto import encrypt_payload, decrypt_payload
        data = {"patient_id": 42, "note": "confidentiel"}
        encrypted = encrypt_payload(data)
        decrypted = decrypt_payload(encrypted["payload"])
        assert decrypted == data

    def test_different_encryptions_of_same_data_differ(self):
        from backend.services.zka_crypto import encrypt_payload
        data = {"key": "value"}
        r1 = encrypt_payload(data)
        r2 = encrypt_payload(data)
        # IV is random, so ciphertexts should differ
        assert r1["payload"] != r2["payload"]

    def test_missing_master_key_raises(self, monkeypatch):
        monkeypatch.delenv("CABINET_MASTER_KEY_HEX", raising=False)
        from backend.services import zka_crypto
        import importlib
        importlib.reload(zka_crypto)
        with pytest.raises(ValueError, match="CABINET_MASTER_KEY_HEX"):
            zka_crypto.get_master_key_bytes()

    def test_encrypt_nested_dict(self):
        from backend.services.zka_crypto import encrypt_payload, decrypt_payload
        data = {"a": {"b": [1, 2, 3]}, "c": True}
        result = decrypt_payload(encrypt_payload(data)["payload"])
        assert result == data
