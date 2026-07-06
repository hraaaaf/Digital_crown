"""Nineteenth batch — ZKAService pure crypto methods,
medication_dict._strengths_mg and validate_dosage."""
import pytest


# ── ZKAService pure crypto ─────────────────────────────────────────────────────

class TestZKAServiceGenerateMasterKey:
    def _svc(self):
        from backend.services.zka_service import ZKAService
        return ZKAService()

    def test_returns_64_char_hex_string(self):
        key = self._svc().generate_master_key()
        assert isinstance(key, str)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_returns_different_key_each_call(self):
        svc = self._svc()
        k1 = svc.generate_master_key()
        k2 = svc.generate_master_key()
        assert k1 != k2


class TestZKAServiceEncryptDecrypt:
    def _svc(self):
        from backend.services.zka_service import ZKAService
        return ZKAService()

    def _valid_key(self):
        from backend.services.zka_service import ZKAService
        return ZKAService.generate_master_key()

    def test_encrypt_returns_string(self):
        key = self._valid_key()
        result = self._svc().encrypt_payload({"foo": "bar"}, key)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypt_then_decrypt_round_trip(self):
        key = self._valid_key()
        payload = {"clinic": "test", "value": 42}
        blob = self._svc().encrypt_payload(payload, key)
        recovered = self._svc().decrypt_payload(blob, key)
        assert recovered == payload

    def test_decrypt_with_wrong_key_raises(self):
        key1 = self._valid_key()
        key2 = self._valid_key()
        blob = self._svc().encrypt_payload({"data": "secret"}, key1)
        with pytest.raises(Exception):
            self._svc().decrypt_payload(blob, key2)

    def test_encrypt_empty_dict(self):
        key = self._valid_key()
        blob = self._svc().encrypt_payload({}, key)
        recovered = self._svc().decrypt_payload(blob, key)
        assert recovered == {}

    def test_encrypt_nested_dict(self):
        key = self._valid_key()
        payload = {"patient": {"id": 1, "name": "Dr. Smith"}, "count": 10}
        blob = self._svc().encrypt_payload(payload, key)
        recovered = self._svc().decrypt_payload(blob, key)
        assert recovered == payload

    def test_encrypt_different_blobs_same_payload(self):
        # Due to random IV, same plaintext produces different ciphertexts
        key = self._valid_key()
        b1 = self._svc().encrypt_payload({"x": 1}, key)
        b2 = self._svc().encrypt_payload({"x": 1}, key)
        assert b1 != b2  # Different IVs → different blobs

    def test_invalid_key_hex_raises(self):
        with pytest.raises(Exception):
            self._svc().encrypt_payload({"data": "x"}, "not_a_valid_hex_key")


# ── medication_dict._strengths_mg ─────────────────────────────────────────────

class TestStrengthsMg:
    def _fn(self, rec):
        from backend.services.medication_dict import _strengths_mg
        return _strengths_mg(rec)

    def test_single_dose_returns_list(self):
        result = self._fn({"dosage": "500", "unite": "MG"})
        assert isinstance(result, list)

    def test_association_dose_parses_both(self):
        # "1 / 60" should parse two values
        result = self._fn({"dosage": "1 / 60", "unite": "G"})
        assert len(result) == 2

    def test_empty_dosage_returns_empty(self):
        result = self._fn({"dosage": "", "unite": "MG"})
        assert result == []

    def test_missing_dosage_returns_empty(self):
        result = self._fn({})
        assert result == []

    def test_gram_dosage_converts_to_mg(self):
        result = self._fn({"dosage": "1", "unite": "G"})
        assert 1000.0 in result


# ── medication_dict.validate_dosage ───────────────────────────────────────────

class TestValidateDosage:
    def _fn(self, name, dosage_mg):
        from backend.services.medication_dict import validate_dosage
        return validate_dosage(name, dosage_mg)

    def test_unknown_drug_returns_known_false(self):
        result = self._fn("ZZZZNOTADRUG9999", 500.0)
        assert result == {"known": False}

    def test_known_drug_returns_known_true(self):
        result = self._fn("DOLIPRANE", 500.0)
        assert result.get("known") is True

    def test_returns_dci_for_known_drug(self):
        result = self._fn("DOLIPRANE", 500.0)
        if result.get("known"):
            assert "dci" in result

    def test_returns_available_mg_list(self):
        result = self._fn("DOLIPRANE", 500.0)
        if result.get("known"):
            assert "available_mg" in result
            assert isinstance(result["available_mg"], list)

    def test_dosage_none_skips_exists_key(self):
        result = self._fn("DOLIPRANE", None)
        assert "exists" not in result

    def test_valid_dosage_adds_exists_key(self):
        result = self._fn("DOLIPRANE", 500.0)
        if result.get("known") and result.get("available_mg"):
            assert "exists" in result
