"""Seventeenth batch — HabitsEngine.get_recommended_duration (pure),
prescription_service generic molecule branches,
LicenseService._get_fernet."""


# ── HabitsEngine.get_recommended_duration ─────────────────────────────────────

class TestGetRecommendedDuration:
    def _eng(self):
        from backend.services.habits_engine import HabitsEngine
        return HabitsEngine()

    # Endodontic / canal acts
    def test_canal_molaire_returns_60(self):
        assert self._eng().get_recommended_duration("TRAITEMENT CANAL MOLAIRE") == 60

    def test_canal_pluri_returns_60(self):
        assert self._eng().get_recommended_duration("TRAITEMENT CANAL PLURIRADICULAIRE") == 60

    def test_canal_simple_returns_45(self):
        assert self._eng().get_recommended_duration("TRAITEMENT CANAL INCISIVE") == 45

    def test_endo_molaire_returns_60(self):
        assert self._eng().get_recommended_duration("ENDODONTIE MOLAIRE") == 60

    def test_endo_simple_returns_45(self):
        assert self._eng().get_recommended_duration("ENDODONTIE SIMPLE") == 45

    # Implant
    def test_implant_returns_90(self):
        assert self._eng().get_recommended_duration("POSE IMPLANT DENTAIRE") == 90

    # Surgery
    def test_chirurgie_returns_60(self):
        assert self._eng().get_recommended_duration("CHIRURGIE MUCO-GINGIVALE") == 60

    def test_biopsie_returns_60(self):
        assert self._eng().get_recommended_duration("BIOPSIE LABIALE") == 60

    # Extractions
    def test_extraction_sagesse_returns_45(self):
        assert self._eng().get_recommended_duration("EXTRACTION DENT DE SAGESSE") == 45

    def test_extraction_inclus_returns_45(self):
        assert self._eng().get_recommended_duration("EXTRACTION DENT INCLUSE") == 45

    def test_extraction_complexe_returns_45(self):
        assert self._eng().get_recommended_duration("EXTRACTION COMPLEXE") == 45

    def test_extraction_simple_returns_30(self):
        assert self._eng().get_recommended_duration("EXTRACTION SIMPLE") == 30

    def test_avulsion_returns_30(self):
        assert self._eng().get_recommended_duration("AVULSION DENTAIRE") == 30

    # Prosthetics / cosmetics
    def test_couronne_returns_45(self):
        assert self._eng().get_recommended_duration("COURONNE CERAMIQUE") == 45

    def test_composite_returns_30(self):
        assert self._eng().get_recommended_duration("COMPOSITE DIRECT") == 30

    def test_reconstruction_returns_30(self):
        assert self._eng().get_recommended_duration("RECONSTRUCTION CORONO-RADICULAIRE") == 30

    # Prevention
    def test_detartrage_returns_30(self):
        assert self._eng().get_recommended_duration("DÉTARTRAGE COMPLET") == 30

    def test_consultation_returns_15(self):
        assert self._eng().get_recommended_duration("CONSULTATION") == 15

    def test_examen_returns_15(self):
        assert self._eng().get_recommended_duration("EXAMEN CLINIQUE") == 15

    def test_bilan_returns_15(self):
        assert self._eng().get_recommended_duration("BILAN RADIOLOGIQUE") == 15

    # Default fallback
    def test_unknown_act_returns_30(self):
        assert self._eng().get_recommended_duration("ACTE_INCONNU_XYZ") == 30

    def test_empty_string_returns_30(self):
        assert self._eng().get_recommended_duration("") == 30


# ── PrescriptionService._normalize_to_molecule (generic branches) ─────────────

class TestNormalizeToMoleculeGeneric:
    """Cover the generic-name fallthrough branches not hit by brand-name tests."""

    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def test_ibuprofene_generic(self):
        assert self._svc()._normalize_to_molecule("IBUPROFENE 400MG") == "IBUPROFENE"

    def test_ibuprofen_english_spelling(self):
        assert self._svc()._normalize_to_molecule("IBUPROFEN 200MG") == "IBUPROFENE"

    def test_ketoprofene_generic(self):
        assert self._svc()._normalize_to_molecule("KETOPROFENE 100MG") == "KETOPROFENE"

    def test_ketoprofen_english(self):
        assert self._svc()._normalize_to_molecule("KETOPROFEN 50MG") == "KETOPROFENE"

    def test_diclofenac_generic(self):
        assert self._svc()._normalize_to_molecule("DICLOFENAC 50MG") == "DICLOFENAC"

    def test_clarithromycine_generic(self):
        assert self._svc()._normalize_to_molecule("CLARITHROMYCINE 250MG") == "CLARITHROMYCINE"

    def test_clarithromycin_english(self):
        assert self._svc()._normalize_to_molecule("CLARITHROMYCIN 500MG") == "CLARITHROMYCINE"

    def test_metronidazole_generic(self):
        assert self._svc()._normalize_to_molecule("METRONIDAZOLE 250MG") == "METRONIDAZOLE"

    def test_spiramycine_generic(self):
        assert self._svc()._normalize_to_molecule("SPIRAMYCINE 3MUI") == "SPIRAMYCINE"

    def test_amiodarone_generic(self):
        assert self._svc()._normalize_to_molecule("AMIODARONE 200MG") == "AMIODARONE"

    def test_simvastatine_generic(self):
        assert self._svc()._normalize_to_molecule("SIMVASTATINE 20MG") == "SIMVASTATINE"

    def test_simvastatin_english(self):
        assert self._svc()._normalize_to_molecule("SIMVASTATIN 40MG") == "SIMVASTATINE"

    def test_aspirine_generic(self):
        assert self._svc()._normalize_to_molecule("ASPIRINE 500MG") == "ASPIRINE"

    def test_aspirin_english(self):
        assert self._svc()._normalize_to_molecule("ASPIRIN 100MG") == "ASPIRINE"


# ── PrescriptionService.check_drug_interactions — AINS + Aspirine ─────────────

class TestCheckDrugInteractionsAinsAspirin:
    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def test_ains_aspirine_medium_warning(self):
        result = self._svc().check_drug_interactions(["ADVIL", "ASPIRINE 100MG"])
        severities = [w["severity"] for w in result]
        assert "medium" in severities

    def test_ains_aspirine_warning_type(self):
        result = self._svc().check_drug_interactions(["VOLTARENE", "ASPIRIN 100MG"])
        types = [w["type"] for w in result]
        assert "ddi" in types


# ── LicenseService._get_fernet ────────────────────────────────────────────────

class TestLicenseServiceGetFernet:
    def _svc(self):
        from backend.services.license_service import LicenseService
        return LicenseService()

    def test_returns_fernet_instance(self):
        from cryptography.fernet import Fernet
        f = self._svc()._get_fernet()
        assert isinstance(f, Fernet)

    def test_fernet_can_encrypt_decrypt(self):
        f = self._svc()._get_fernet()
        plaintext = b"test_secret_data"
        token = f.encrypt(plaintext)
        assert f.decrypt(token) == plaintext

    def test_same_key_deterministic(self):
        svc = self._svc()
        f1 = svc._get_fernet()
        f2 = svc._get_fernet()
        token = f1.encrypt(b"hello")
        assert f2.decrypt(token) == b"hello"
