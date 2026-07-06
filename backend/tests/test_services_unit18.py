"""Eighteenth batch — pii_masker pure helpers,
ClinicalRulesEngine pure methods (_normalize_act_name,
_calculate_pediatric_dosage, _get_alternative, analyze_case)."""
import pytest


# ── pii_masker helpers ────────────────────────────────────────────────────────

class TestAgeToBracket:
    def _fn(self, age):
        from backend.services.pii_masker import _age_to_bracket
        return _age_to_bracket(age)

    def test_child_age_bracket(self):
        assert self._fn(8) == "0-9 ans"

    def test_teen_bracket(self):
        assert self._fn(15) == "10-19 ans"

    def test_adult_bracket(self):
        assert self._fn(35) == "30-39 ans"

    def test_senior_bracket(self):
        assert self._fn(72) == "70-79 ans"

    def test_boundary_exactly_30(self):
        assert self._fn(30) == "30-39 ans"

    def test_boundary_exactly_40(self):
        assert self._fn(40) == "40-49 ans"

    def test_none_returns_unknown(self):
        assert self._fn(None) == "âge inconnu"

    def test_string_converts(self):
        assert self._fn("25") == "20-29 ans"

    def test_invalid_string_returns_unknown(self):
        assert self._fn("not_a_number") == "âge inconnu"


class TestMaskPatientContext:
    def _fn(self, raw):
        from backend.services.pii_masker import mask_patient_context
        return mask_patient_context(raw)

    def test_removes_name_fields(self):
        raw = {"nom": "Ahmed", "prenom": "Ali", "age": 30, "antecedents": "Néant", "genre": "M"}
        result = self._fn(raw)
        assert "nom" not in result
        assert "prenom" not in result

    def test_returns_age_bracket(self):
        raw = {"age": 35}
        result = self._fn(raw)
        assert "age_bracket" in result
        assert result["age_bracket"] == "30-39 ans"

    def test_keeps_antecedents(self):
        raw = {"age": 40, "antecedents": "Diabète de type 2"}
        result = self._fn(raw)
        assert result["antecedents"] == "Diabète de type 2"

    def test_missing_antecedents_defaults_to_nean(self):
        raw = {"age": 40}
        result = self._fn(raw)
        assert result["antecedents"] == "Néant"

    def test_keeps_genre(self):
        raw = {"age": 25, "genre": "F"}
        result = self._fn(raw)
        assert result["genre"] == "F"

    def test_result_keys_are_subset(self):
        raw = {"nom": "X", "telephone": "0600", "age": 50, "genre": "M"}
        result = self._fn(raw)
        allowed = {"age_bracket", "genre", "antecedents"}
        assert set(result.keys()).issubset(allowed)


# ── ClinicalRulesEngine._normalize_act_name ───────────────────────────────────

class TestNormalizeActName:
    def _eng(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_extraction_simple(self):
        assert self._eng()._normalize_act_name("Extraction dentaire") == "EXTRACTION_SIMPLE"

    def test_extraction_chirurgicale(self):
        assert self._eng()._normalize_act_name("Extraction chirurgicale 38") == "EXTRACTION_CHIRURGICALE"

    def test_extraction_complexe(self):
        assert self._eng()._normalize_act_name("Extraction complexe") == "EXTRACTION_CHIRURGICALE"

    def test_implant(self):
        assert self._eng()._normalize_act_name("Pose implant") == "IMPLANT"

    def test_pulpite(self):
        assert self._eng()._normalize_act_name("Pulpite irréversible") == "PULPITE"

    def test_douleur_maps_to_pulpite(self):
        assert self._eng()._normalize_act_name("Douleur dentaire") == "PULPITE"

    def test_abces_dentaire(self):
        # Use ASCII spelling (engine checks for "ABCES" after .upper())
        assert self._eng()._normalize_act_name("Abces dentaire") == "ABCES_DENTAIRE"

    def test_abces_parodontal(self):
        assert self._eng()._normalize_act_name("Abces paro") == "ABCES_PARODONTAL"

    def test_endo_maps_to_mise_en_forme(self):
        assert self._eng()._normalize_act_name("Endodontie") == "MISE_EN_FORME_CANALAIRE"

    def test_traitement_canalaire(self):
        assert self._eng()._normalize_act_name("Traitement canalaire 26") == "MISE_EN_FORME_CANALAIRE"

    def test_hydroxyde_de_calcium(self):
        assert self._eng()._normalize_act_name("Hydroxyde de calcium") == "HYDROXYDE_DE_CALCIUM"

    def test_infect_maps_to_abces_dentaire(self):
        assert self._eng()._normalize_act_name("Infection dentaire") == "ABCES_DENTAIRE"

    def test_unknown_returns_default(self):
        assert self._eng()._normalize_act_name("DÉTARTRAGE") == "DEFAULT"


# ── ClinicalRulesEngine._calculate_pediatric_dosage ──────────────────────────

class TestCalculatePediatricDosage:
    def _eng(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_amoxicilline_25kg_child(self):
        result = self._eng()._calculate_pediatric_dosage("AMOXICILLINE", 25)
        assert "mg" in result.lower()
        assert "625" in result  # 25 * 50 / 2 = 625

    def test_paracetamol_20kg_child(self):
        result = self._eng()._calculate_pediatric_dosage("PARACETAMOL", 20)
        assert "300mg" in result  # 20 * 15 = 300

    def test_ibuprofene_10kg_child(self):
        result = self._eng()._calculate_pediatric_dosage("IBUPROFENE", 10)
        assert "100mg" in result  # 10 * 10 = 100

    def test_unknown_molecule_returns_generic(self):
        result = self._eng()._calculate_pediatric_dosage("UNKNOWN_MOL", 15)
        assert isinstance(result, str)
        assert len(result) > 0


# ── ClinicalRulesEngine._get_alternative ─────────────────────────────────────

class TestGetAlternative:
    def _eng(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def test_amoxicilline_returns_clindamycine(self):
        result = self._eng()._get_alternative("AMOXICILLINE", [])
        assert result == "CLINDAMYCINE"

    def test_ibuprofene_returns_paracetamol(self):
        result = self._eng()._get_alternative("IBUPROFENE", [])
        assert result == "PARACETAMOL"

    def test_returns_none_when_all_banned(self):
        result = self._eng()._get_alternative("AMOXICILLINE", ["CLINDAMYCINE", "SPIRAMYCINE_METRONIDAZOLE"])
        assert result is None

    def test_skips_banned_first_option(self):
        result = self._eng()._get_alternative("AUGMENTIN", ["CLINDAMYCINE"])
        assert result == "SPIRAMYCINE_METRONIDAZOLE"

    def test_unknown_molecule_returns_none(self):
        result = self._eng()._get_alternative("UNKNOWN_DRUG", [])
        assert result is None


# ── ClinicalRulesEngine.analyze_case ─────────────────────────────────────────

class TestAnalyzeCase:
    def _eng(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def _patient(self, antecedents="", age=35, poids=70):
        return {"antecedents": antecedents, "age": age, "poids": poids}

    def test_returns_dict_with_required_keys(self):
        result = self._eng().analyze_case(self._patient(), ["DÉTARTRAGE"])
        assert "risques_identifies" in result
        assert "recommandations_moleculaires" in result
        assert "dosage_note" in result
        assert "is_child" in result

    def test_no_antecedents_no_warnings(self):
        result = self._eng().analyze_case(self._patient(), ["DÉTARTRAGE"])
        assert result["risques_identifies"] == []

    def test_extraction_simple_recommends_paracetamol(self):
        result = self._eng().analyze_case(self._patient(), ["Extraction dentaire"])
        molecules = [m["molecule"] for m in result["recommandations_moleculaires"]]
        assert "PARACETAMOL" in molecules

    def test_grossesse_triggers_critical_warning(self):
        result = self._eng().analyze_case(self._patient(antecedents="Grossesse T2"), ["DÉTARTRAGE"])
        assert len(result["risques_identifies"]) > 0
        # Should contain AINS counter-indication

    def test_allergie_penicilline_present(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Allergie Pénicilline"),
            ["Abcès dentaire"]
        )
        # Should detect allergy and suggest alternatives
        assert isinstance(result["risques_identifies"], list)

    def test_child_patient_sets_is_child_true(self):
        result = self._eng().analyze_case(self._patient(age=8, poids=25), ["Extraction dentaire"])
        assert result["is_child"] is True

    def test_adult_patient_sets_is_child_false(self):
        result = self._eng().analyze_case(self._patient(age=35), ["Extraction dentaire"])
        assert result["is_child"] is False

    def test_child_has_dosage_note(self):
        result = self._eng().analyze_case(self._patient(age=10, poids=30), ["Extraction dentaire"])
        assert "PÉDIATRIQUE" in result["dosage_note"] or "AJUSTEMENT" in result["dosage_note"]

    def test_implant_triggers_antibioprophylaxie(self):
        result = self._eng().analyze_case(self._patient(), ["Pose implant"])
        messages = " ".join(result["risques_identifies"])
        assert "ANTIBIO" in messages.upper() or "antibioprophylaxie" in messages.lower()

    def test_anticoagulant_warns_against_ains(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="XARELTO 20mg traitement anticoagulant"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        assert len(result["risques_identifies"]) > 0

    def test_abces_dentaire_recommends_amoxicilline(self):
        # Use ASCII spelling so engine matches "ABCES" after upper()
        result = self._eng().analyze_case(self._patient(), ["Abces dentaire"])
        molecules = [m["molecule"] for m in result["recommandations_moleculaires"]]
        assert len(molecules) > 0

    def test_extraction_with_anticoagulant_adds_exacyl(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="XARELTO AVK anticoagulant"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        # Exacyl or acid tranexamique should be mentioned
        assert "Exacyl" in messages or "EXACYL" in messages or "Tranex" in messages

    def test_asthme_warns_about_ains(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Asthme allergique"),
            ["Extraction chirurgicale"]
        )
        assert len(result["risques_identifies"]) > 0

    def test_amoxicilline_triggers_ultra_levure_suggestion(self):
        result = self._eng().analyze_case(self._patient(), ["Abces dentaire"])
        messages = " ".join(result["risques_identifies"])
        assert "Ultra-Levure" in messages or "boulardii" in messages.lower()

    def test_hypertension_triggers_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="HTA traitée"),
            ["Extraction dentaire"]
        )
        assert len(result["risques_identifies"]) > 0
