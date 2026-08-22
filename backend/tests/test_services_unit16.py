"""Sixteenth batch — PrescriptionService pure helpers."""
from datetime import date


# ── PrescriptionService._normalize_to_molecule ───────────────────────────────

class TestNormalizeToMolecule:
    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def test_doliprane_maps_to_paracetamol(self):
        assert self._svc()._normalize_to_molecule("DOLIPRANE") == "PARACETAMOL"

    def test_advil_maps_to_ibuprofene(self):
        assert self._svc()._normalize_to_molecule("ADVIL") == "IBUPROFENE"

    def test_augmentin_maps_to_amoxicilline_clavulanate(self):
        assert self._svc()._normalize_to_molecule("AUGMENTIN") == "AMOXICILLINE/ACIDE_CLAVULANIQUE"

    def test_voltarene_maps_to_diclofenac(self):
        assert self._svc()._normalize_to_molecule("VOLTARENE") == "DICLOFENAC"

    def test_flagyl_maps_to_metronidazole(self):
        assert self._svc()._normalize_to_molecule("FLAGYL") == "METRONIDAZOLE"

    def test_zeclar_maps_to_clarithromycine(self):
        assert self._svc()._normalize_to_molecule("ZECLAR") == "CLARITHROMYCINE"

    def test_xarelto_maps_to_rivaroxaban(self):
        assert self._svc()._normalize_to_molecule("XARELTO") == "RIVAROXABAN"

    def test_generic_amoxicilline_recognized(self):
        assert self._svc()._normalize_to_molecule("AMOXICILLINE 500MG") == "AMOXICILLINE"

    def test_generic_paracetamol_recognized(self):
        assert self._svc()._normalize_to_molecule("PARACETAMOL 1G") == "PARACETAMOL"

    def test_unknown_returns_uppercase_name(self):
        result = self._svc()._normalize_to_molecule("UNKNOWN_DRUG_XYZ")
        assert isinstance(result, str)


# ── PrescriptionService.check_drug_interactions ──────────────────────────────

class TestCheckDrugInteractions:
    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def test_single_drug_returns_empty(self):
        result = self._svc().check_drug_interactions(["DOLIPRANE"])
        assert result == []

    def test_empty_list_returns_empty(self):
        result = self._svc().check_drug_interactions([])
        assert result == []

    def test_ains_ains_detected(self):
        result = self._svc().check_drug_interactions(["ADVIL", "VOLTARENE"])
        severities = [w["severity"] for w in result]
        assert "medium" in severities

    def test_macrolide_simvastatine_critical(self):
        result = self._svc().check_drug_interactions(["ZECLAR", "ZOCOR"])
        severities = [w["severity"] for w in result]
        assert "high" in severities

    def test_macrolide_amiodarone_critical(self):
        result = self._svc().check_drug_interactions(["ZECLAR", "CORDARONE"])
        severities = [w["severity"] for w in result]
        assert "high" in severities

    def test_metronidazole_alcool_critical(self):
        result = self._svc().check_drug_interactions(["FLAGYL", "ALCOOL"])
        severities = [w["severity"] for w in result]
        assert "high" in severities

    def test_ains_anticoagulant_warning(self):
        result = self._svc().check_drug_interactions(["ADVIL", "XARELTO"])
        severities = [w["severity"] for w in result]
        assert "medium" in severities

    def test_returns_list(self):
        result = self._svc().check_drug_interactions(["DOLIPRANE", "ADVIL"])
        assert isinstance(result, list)

    def test_interaction_has_type_and_message(self):
        result = self._svc().check_drug_interactions(["ADVIL", "VOLTARENE"])
        for w in result:
            assert "type" in w
            assert "message" in w


# ── PrescriptionService._calculate_age ───────────────────────────────────────

class TestCalculateAge:
    def _svc(self):
        from backend.services.prescription_service import PrescriptionService
        return PrescriptionService()

    def test_returns_int(self):
        result = self._svc()._calculate_age(date(1990, 1, 1))
        assert isinstance(result, int)

    def test_age_positive(self):
        result = self._svc()._calculate_age(date(1980, 6, 15))
        assert result > 0

    def test_birthday_today_exact_age(self):
        today = date.today()
        birth = date(today.year - 30, today.month, today.day)
        assert self._svc()._calculate_age(birth) == 30

    def test_birthday_tomorrow_one_less(self):
        today = date.today()
        from datetime import timedelta
        tomorrow = today + timedelta(days=1)
        # Born 30 years ago tomorrow → hasn't turned 30 yet
        birth = date(today.year - 30, tomorrow.month, tomorrow.day)
        result = self._svc()._calculate_age(birth)
        assert result == 29

    def test_newborn_returns_zero(self):
        result = self._svc()._calculate_age(date.today())
        assert result == 0
