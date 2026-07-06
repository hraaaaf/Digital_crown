"""Twenty-fifth batch — anonymizer (pure), telemetry._telemetry_enabled,
ClinicalRulesEngine helpers (_normalize_act_name, _calculate_pediatric_dosage,
_get_alternative) and remaining analyze_patient_case branches."""
import pytest
from unittest.mock import patch, MagicMock


# ── anonymizer ─────────────────────────────────────────────────────────────────

class TestAnonymizeText:
    def _fn(self, text):
        from backend.services.anonymizer import anonymize_text
        return anonymize_text(text)

    def test_non_string_passthrough(self):
        assert self._fn(42) == 42

    def test_none_passthrough(self):
        assert self._fn(None) is None

    def test_dossier_masked(self):
        assert "[DOSSIER]" in self._fn("Dossier P-123456 créé")

    def test_dossier_case_insensitive(self):
        assert "[DOSSIER]" in self._fn("ref p-99 ok")

    def test_telephone_moroccan_masked(self):
        assert "[TELEPHONE]" in self._fn("Tel: 0661234567")

    def test_email_masked(self):
        assert "[EMAIL]" in self._fn("user@example.com")

    def test_patient_name_masked(self):
        result = self._fn("Patient Dupont Jean")
        assert "[NOM]" in result

    def test_mr_name_masked(self):
        result = self._fn("Mr Dupont Jean")
        assert "[NOM]" in result

    def test_mme_name_masked(self):
        result = self._fn("Mme Durand Marie")
        assert "[NOM]" in result

    def test_no_pii_unchanged(self):
        result = self._fn("Aucune information personnelle ici.")
        assert result == "Aucune information personnelle ici."

    def test_empty_string(self):
        assert self._fn("") == ""

    def test_multiple_pii_all_masked(self):
        text = "Patient Dupont à P-111 email test@x.com tel 0612345678"
        result = self._fn(text)
        assert "[DOSSIER]" in result
        assert "[EMAIL]" in result
        assert "[TELEPHONE]" in result


class TestAnonymizePayload:
    def _fn(self, payload):
        from backend.services.anonymizer import anonymize_payload
        return anonymize_payload(payload)

    def test_dict_recurses(self):
        result = self._fn({"email": "a@b.com", "age": 30})
        assert result["email"] == "[EMAIL]"
        assert result["age"] == 30

    def test_list_recurses(self):
        result = self._fn(["a@b.com", "plain"])
        assert result[0] == "[EMAIL]"
        assert result[1] == "plain"

    def test_string_anonymized(self):
        result = self._fn("Patient Dupont")
        assert "[NOM]" in result

    def test_int_passthrough(self):
        assert self._fn(42) == 42

    def test_nested_dict_and_list(self):
        payload = {"contacts": [{"email": "x@y.com"}]}
        result = self._fn(payload)
        assert result["contacts"][0]["email"] == "[EMAIL]"


# ── telemetry._telemetry_enabled ───────────────────────────────────────────────

class TestTelemetryEnabled:
    def test_disabled_by_default(self):
        from backend.services.telemetry import _telemetry_enabled
        with patch("backend.services.telemetry.settings") as mock_settings:
            mock_settings.TELEMETRY_ENABLED = False
            result = _telemetry_enabled()
        assert result is False

    def test_enabled_when_flag_true(self):
        from backend.services.telemetry import _telemetry_enabled
        with patch("backend.services.telemetry.settings") as mock_settings:
            mock_settings.TELEMETRY_ENABLED = True
            result = _telemetry_enabled()
        assert result is True

    def test_missing_attribute_defaults_to_false(self):
        from backend.services.telemetry import _telemetry_enabled
        with patch("backend.services.telemetry.settings", spec=[]):  # no TELEMETRY_ENABLED attr
            result = _telemetry_enabled()
        assert result is False


# ── ClinicalRulesEngine helpers ────────────────────────────────────────────────

class TestNormalizeActName:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_hydroxyde_calcium_keyword(self):
        assert self._svc()._normalize_act_name("Hydroxyde de calcium inter-séance") == "HYDROXYDE_DE_CALCIUM"

    def test_canalaire_keyword(self):
        assert self._svc()._normalize_act_name("Traitement canalaire") == "MISE_EN_FORME_CANALAIRE"

    def test_endo_keyword(self):
        assert self._svc()._normalize_act_name("Endo monoradiculaire") == "MISE_EN_FORME_CANALAIRE"

    def test_extraction_chirurgicale(self):
        assert self._svc()._normalize_act_name("extraction chirurgicale") == "EXTRACTION_CHIRURGICALE"

    def test_extraction_complexe(self):
        assert self._svc()._normalize_act_name("extraction complexe") == "EXTRACTION_CHIRURGICALE"

    def test_extraction_simple(self):
        assert self._svc()._normalize_act_name("extraction simple") == "EXTRACTION_SIMPLE"

    def test_abces_dentaire(self):
        assert self._svc()._normalize_act_name("abces dentaire") == "ABCES_DENTAIRE"

    def test_abces_parodontal(self):
        assert self._svc()._normalize_act_name("abces paro") == "ABCES_PARODONTAL"

    def test_pulpite_keyword(self):
        assert self._svc()._normalize_act_name("Pulpite aiguë") == "PULPITE"

    def test_douleur_keyword(self):
        assert self._svc()._normalize_act_name("douleur post-op") == "PULPITE"

    def test_implant_keyword(self):
        assert self._svc()._normalize_act_name("pose d'implant") == "IMPLANT"

    def test_unknown_returns_default(self):
        assert self._svc()._normalize_act_name("détartrage") == "DEFAULT"


class TestCalculatePediatricDosage:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_amoxicilline_formula(self):
        result = self._svc()._calculate_pediatric_dosage("AMOXICILLINE", 20)
        assert "500mg" in result
        assert "50mg/kg/j" in result

    def test_paracetamol_formula(self):
        result = self._svc()._calculate_pediatric_dosage("PARACETAMOL", 20)
        assert "300mg" in result
        assert "60mg/kg/j" in result

    def test_ibuprofene_formula(self):
        result = self._svc()._calculate_pediatric_dosage("IBUPROFENE", 20)
        assert "200mg" in result
        assert "30mg/kg/j" in result

    def test_unknown_molecule(self):
        result = self._svc()._calculate_pediatric_dosage("SPIRAMYCINE", 20)
        assert "confirmer" in result.lower() or "poids" in result.lower()


class TestGetAlternative:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_amoxicilline_returns_clindamycine(self):
        result = self._svc()._get_alternative("AMOXICILLINE", [])
        assert result == "CLINDAMYCINE"

    def test_ibuprofene_returns_paracetamol(self):
        result = self._svc()._get_alternative("IBUPROFENE", [])
        assert result == "PARACETAMOL"

    def test_all_alternatives_banned_returns_none(self):
        result = self._svc()._get_alternative("AMOXICILLINE", ["CLINDAMYCINE", "SPIRAMYCINE_METRONIDAZOLE"])
        assert result is None

    def test_unknown_molecule_returns_none(self):
        result = self._svc()._get_alternative("VANCOMYCINE", [])
        assert result is None


# ── ClinicalRulesEngine remaining analyze_patient_case branches ────────────────

class TestAnalyzeRemainingBranches:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def _run(self, antecedents="", acts=None, age=30, poids=70):
        return self._svc().analyze_case(
            {"antecedents": antecedents, "age": age, "poids": poids},
            acts or []
        )

    def test_antibioprophylaxie_with_penicillin_allergy(self):
        result = self._run(antecedents="PENICILLINE allergie", acts=["IMPLANT"])
        codes = [w for r in result["risques_identifies"] for w in [r] if "DALACINE" in r]
        assert any("DALACINE" in r for r in result["risques_identifies"])

    def test_antibioprophylaxie_without_allergy(self):
        result = self._run(antecedents="", acts=["IMPLANT"])
        assert any("CLAMOXYL" in r or "Amoxicilline" in r for r in result["risques_identifies"])

    def test_anticoagulant_with_extraction_adds_exacyl(self):
        result = self._run(antecedents="ANTICOAGULANT SINTROM", acts=["extraction simple"])
        assert any("Exacyl" in r or "Tranexamique" in r for r in result["risques_identifies"])

    def test_hypertension_precaution_warning(self):
        result = self._run(antecedents="HYPERTENSION HTA")
        assert any("HTA" in r or "Tensionnelle" in r or "hypertendu" in r for r in result["risques_identifies"])

    def test_grossesse_radio_warning(self):
        result = self._run(antecedents="ENCEINTE T2")
        assert any("Radiographie" in r or "TABLIER DE PLOMB" in r for r in result["risques_identifies"])

    def test_pediatric_dosage_note(self):
        result = self._run(antecedents="", acts=["extraction simple"], age=10, poids=30)
        assert result["is_child"] is True
        assert "PÉDIATRIQUE" in result["dosage_note"] or "DIATRIQUE" in result["dosage_note"]

    def test_extraction_chirurgicale_antibioprophylaxie(self):
        result = self._run(antecedents="", acts=["EXTRACTION CHIRURGICALE"])
        assert any("Antibioprophylaxie" in r or "CLAMOXYL" in r or "prophylaxie" in r.lower()
                   for r in result["risques_identifies"])

    def test_ulcere_gastrique_warning_message(self):
        result = self._run(antecedents="ULCERE GASTRIQUE actif")
        assert any("Gastro" in r or "ulcère" in r.lower() or "gastroduodénal" in r
                   for r in result["risques_identifies"])

    def test_ultra_levure_coprescription(self):
        result = self._run(antecedents="", acts=["extraction simple"])
        mols = [m["molecule"] for m in result["recommandations_moleculaires"]]
        if "AMOXICILLINE" in mols:
            assert any("Ultra-Levure" in r or "SACCHAROMYCES" in r or "diarrhée" in r.lower()
                       for r in result["risques_identifies"])
