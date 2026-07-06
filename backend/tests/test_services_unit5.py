"""Fifth batch — prescription_service pure methods, zka_crypto, zka_service helpers."""


# ── prescription_service._normalize_to_molecule ───────────────────────────────

class TestNormalizeToMolecule:
    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def _fn(self, name):
        return self._svc()._normalize_to_molecule(name)

    def test_doliprane_is_paracetamol(self):
        assert self._fn("DOLIPRANE") == "PARACETAMOL"

    def test_advil_is_ibuprofene(self):
        assert self._fn("ADVIL") == "IBUPROFENE"

    def test_augmentin_is_amoxicilline_clavulanique(self):
        assert self._fn("AUGMENTIN") == "AMOXICILLINE/ACIDE_CLAVULANIQUE"

    def test_flagyl_is_metronidazole(self):
        assert self._fn("FLAGYL") == "METRONIDAZOLE"

    def test_voltarene_is_diclofenac(self):
        assert self._fn("VOLTARENE") == "DICLOFENAC"

    def test_cordarone_is_amiodarone(self):
        assert self._fn("CORDARONE") == "AMIODARONE"

    def test_sintrom_is_warfarine(self):
        assert self._fn("SINTROM") == "WARFARINE"

    def test_xarelto_is_rivaroxaban(self):
        assert self._fn("XARELTO") == "RIVAROXABAN"

    def test_ibuprofene_generic(self):
        assert self._fn("IBUPROFENE 400MG") == "IBUPROFENE"

    def test_paracetamol_generic(self):
        assert self._fn("PARACETAMOL 1G") == "PARACETAMOL"

    def test_amoxicilline_generic(self):
        assert self._fn("AMOXICILLINE 500") == "AMOXICILLINE"

    def test_ketoprofene_generic(self):
        assert self._fn("KETOPROFENE 100MG") == "KETOPROFENE"

    def test_clarithromycine_generic(self):
        assert self._fn("CLARITHROMYCINE 500") == "CLARITHROMYCINE"

    def test_unknown_returns_self(self):
        result = self._fn("PRODUIT_INCONNU_XYZ")
        assert result == "PRODUIT_INCONNU_XYZ"

    def test_lowercase_input_normalized(self):
        assert self._fn("doliprane") == "PARACETAMOL"


# ── prescription_service.check_drug_interactions ──────────────────────────────

class TestCheckDrugInteractions:
    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def _fn(self, drugs):
        return self._svc().check_drug_interactions(drugs)

    def test_empty_list_returns_empty(self):
        assert self._fn([]) == []

    def test_single_drug_returns_empty(self):
        assert self._fn(["DOLIPRANE"]) == []

    def test_no_interactions_safe_combo(self):
        result = self._fn(["DOLIPRANE", "FLAGYL"])
        ddi_types = [w["drug"] for w in result]
        assert "ains-ains" not in ddi_types

    def test_macrolide_simvastatine_critical(self):
        result = self._fn(["ZECLAR", "TAHOR"])
        assert any(w["severity"] == "high" and "rhabdomyolyse" in w["message"].lower() or "simvastatine" in w["drug"] for w in result)

    def test_metronidazole_alcool_critical(self):
        result = self._fn(["FLAGYL", "ALCOOL"])
        assert any(w["severity"] == "high" for w in result)
        assert any("alcool" in w["drug"].lower() or "metronidazole" in w["message"].lower() for w in result)

    def test_two_ains_duplication_warning(self):
        result = self._fn(["ADVIL", "VOLTARENE"])
        ddi_drugs = [w["drug"] for w in result]
        assert "ains-ains" in ddi_drugs

    def test_ains_aspirine_warning(self):
        result = self._fn(["ADVIL", "ASPIRINE"])
        ddi_drugs = [w["drug"] for w in result]
        assert "ains-aspirine" in ddi_drugs

    def test_ains_anticoagulant_warning(self):
        result = self._fn(["ADVIL", "SINTROM"])
        ddi_drugs = [w["drug"] for w in result]
        assert "ains-anticoagulant" in ddi_drugs

    def test_macrolide_amiodarone_critical(self):
        result = self._fn(["ZECLAR", "CORDARONE"])
        assert any(w["severity"] == "high" for w in result)
        assert any("amiodarone" in w["drug"].lower() for w in result)

    def test_returns_list_of_dicts(self):
        result = self._fn(["ADVIL", "SINTROM"])
        assert isinstance(result, list)
        if result:
            assert "type" in result[0]
            assert "severity" in result[0]
            assert "message" in result[0]


# ── zka_service pure helpers ──────────────────────────────────────────────────

class TestZkaService:
    def test_class_importable(self):
        from backend.services.zka_service import ZKAService
        assert ZKAService is not None

    def test_generate_master_key_returns_string(self):
        from backend.services.zka_service import ZKAService
        key = ZKAService.generate_master_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_generate_master_key_is_hex(self):
        from backend.services.zka_service import ZKAService
        key = ZKAService.generate_master_key()
        int(key, 16)  # raises ValueError if not valid hex

    def test_generate_master_key_is_64_chars(self):
        from backend.services.zka_service import ZKAService
        key = ZKAService.generate_master_key()
        assert len(key) == 64  # 32 bytes × 2 hex chars

    def test_two_keys_are_different(self):
        from backend.services.zka_service import ZKAService
        k1 = ZKAService.generate_master_key()
        k2 = ZKAService.generate_master_key()
        assert k1 != k2


# ── zka_service encrypt/decrypt ───────────────────────────────────────────────

class TestZkaServiceEncryptDecrypt:
    def _key(self):
        from backend.services.zka_service import ZKAService
        return ZKAService.generate_master_key()

    def test_encrypt_decrypt_roundtrip(self):
        from backend.services.zka_service import ZKAService
        key = self._key()
        data = {"patient": "confidentiel", "age": 42}
        blob = ZKAService.encrypt_payload(data, key)
        result = ZKAService.decrypt_payload(blob, key)
        assert result == data

    def test_encrypt_returns_string(self):
        from backend.services.zka_service import ZKAService
        key = self._key()
        blob = ZKAService.encrypt_payload({"x": 1}, key)
        assert isinstance(blob, str)
        assert len(blob) > 0

    def test_encrypt_same_data_different_blobs(self):
        from backend.services.zka_service import ZKAService
        key = self._key()
        b1 = ZKAService.encrypt_payload({"x": 1}, key)
        b2 = ZKAService.encrypt_payload({"x": 1}, key)
        # random IV → different ciphertext each time
        assert b1 != b2

    def test_unicode_content_roundtrip(self):
        from backend.services.zka_service import ZKAService
        key = self._key()
        data = {"nom": "محمد الأمين", "note": "données patient"}
        result = ZKAService.decrypt_payload(ZKAService.encrypt_payload(data, key), key)
        assert result == data


# ── backup_service pure helpers ───────────────────────────────────────────────

class TestBackupService:
    def test_imports_cleanly(self):
        from backend.services.backup_service import BackupService
        assert BackupService is not None

    def test_is_instantiable(self):
        from backend.services.backup_service import BackupService
        svc = BackupService()
        assert svc is not None

    def test_has_run_daily_backup(self):
        from backend.services.backup_service import BackupService
        assert callable(BackupService.run_daily_backup)

    def test_has_restore_backup(self):
        from backend.services.backup_service import BackupService
        assert callable(BackupService.restore_backup)
