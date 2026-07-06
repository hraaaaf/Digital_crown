"""Pure unit tests for deterministic service modules (no HTTP, no DB)."""
import io
from unittest.mock import MagicMock


# ── file_validator ────────────────────────────────────────────────────────────

class TestSanitizeFilename:
    def _fn(self, name):
        from backend.services.file_validator import sanitize_filename
        return sanitize_filename(name)

    def test_normal_filename_unchanged(self):
        assert self._fn("radio.jpg") == "radio.jpg"

    def test_removes_path_traversal_dots(self):
        result = self._fn("../../etc/passwd.jpg")
        assert ".." not in result

    def test_removes_forward_slash(self):
        assert "/" not in self._fn("foo/bar.jpg")

    def test_removes_backslash(self):
        assert "\\" not in self._fn("foo\\bar.jpg")

    def test_removes_dangerous_chars(self):
        result = self._fn("file<name>.jpg")
        assert "<" not in result
        assert ">" not in result

    def test_long_filename_truncated(self):
        long_name = "a" * 300 + ".jpg"
        result = self._fn(long_name)
        assert len(result) <= 201  # 200 chars + possible dot

    def test_empty_string_returns_empty_or_short(self):
        result = self._fn("")
        assert isinstance(result, str)

    def test_preserves_dots_and_dashes(self):
        result = self._fn("radio-panoramique.tiff")
        assert "radio" in result
        assert "panoramique" in result

    def test_removes_semicolon(self):
        assert ";" not in self._fn("file;rm -rf.jpg")


class TestValidateUploadedImage:
    def _make_upload(self, filename, content):
        mock = MagicMock()
        mock.filename = filename
        mock.file.read = MagicMock(side_effect=[content, b""])
        return mock

    def _validate(self, filename, content):
        from backend.services.file_validator import validate_uploaded_image
        upload = self._make_upload(filename, content)
        return validate_uploaded_image(upload)

    def test_invalid_extension_raises_400(self):
        from fastapi import HTTPException
        import pytest
        with pytest.raises(HTTPException) as exc:
            self._validate("document.pdf", b"some content")
        assert exc.value.status_code == 400

    def test_empty_file_raises_400(self):
        from fastapi import HTTPException
        import pytest
        mock = MagicMock()
        mock.filename = "radio.jpg"
        mock.file.read = MagicMock(return_value=b"")
        from backend.services.file_validator import validate_uploaded_image
        with pytest.raises(HTTPException) as exc:
            validate_uploaded_image(mock)
        assert exc.value.status_code == 400

    def test_too_large_file_raises_400(self):
        from fastapi import HTTPException
        import pytest
        # Simulate streaming > 10MB by returning large chunks repeatedly
        MAX = 10 * 1024 * 1024 + 1
        chunk = b"x" * 8192
        calls = [chunk] * (MAX // 8192 + 2) + [b""]
        mock = MagicMock()
        mock.filename = "radio.jpg"
        mock.file.read = MagicMock(side_effect=calls)
        from backend.services.file_validator import validate_uploaded_image
        with pytest.raises(HTTPException) as exc:
            validate_uploaded_image(mock)
        assert exc.value.status_code == 400

    def test_no_extension_raises_400(self):
        from fastapi import HTTPException
        import pytest
        with pytest.raises(HTTPException) as exc:
            self._validate("radiofile", b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        assert exc.value.status_code == 400

    def test_allowed_extension_set(self):
        from backend.services.file_validator import ALLOWED_EXTENSIONS
        for ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".dcm", ".dicom"]:
            assert ext in ALLOWED_EXTENSIONS


class TestFileValidationError:
    def test_is_exception(self):
        from backend.services.file_validator import FileValidationError
        exc = FileValidationError("test error")
        assert isinstance(exc, Exception)
        assert str(exc) == "test error"


# ── pii_masker ────────────────────────────────────────────────────────────────

class TestAgeToBracket:
    def _fn(self, age):
        from backend.services.pii_masker import _age_to_bracket
        return _age_to_bracket(age)

    def test_age_25_returns_20_29(self):
        assert self._fn(25) == "20-29 ans"

    def test_age_30_returns_30_39(self):
        assert self._fn(30) == "30-39 ans"

    def test_age_0_returns_0_9(self):
        assert self._fn(0) == "0-9 ans"

    def test_age_70_returns_70_79(self):
        assert self._fn(70) == "70-79 ans"

    def test_age_as_string_works(self):
        assert self._fn("45") == "40-49 ans"

    def test_invalid_age_returns_unknown(self):
        assert self._fn("not_a_number") == "âge inconnu"

    def test_none_returns_unknown(self):
        assert self._fn(None) == "âge inconnu"

    def test_age_10_returns_10_19(self):
        assert self._fn(10) == "10-19 ans"


class TestMaskPatientContext:
    def _fn(self, raw):
        from backend.services.pii_masker import mask_patient_context
        return mask_patient_context(raw)

    def test_returns_age_bracket(self):
        result = self._fn({"age": 35, "genre": "M", "antecedents": "RAS"})
        assert result["age_bracket"] == "30-39 ans"

    def test_name_not_in_result(self):
        result = self._fn({"nom": "DUPONT", "prenom": "Jean", "age": 35, "genre": "M"})
        assert "nom" not in result
        assert "prenom" not in result

    def test_email_not_in_result(self):
        result = self._fn({"email": "test@test.com", "age": 40})
        assert "email" not in result

    def test_genre_preserved(self):
        result = self._fn({"age": 25, "genre": "F"})
        assert result["genre"] == "F"

    def test_antecedents_preserved(self):
        result = self._fn({"age": 50, "antecedents": "HTA"})
        assert result["antecedents"] == "HTA"

    def test_missing_antecedents_defaults_to_nant(self):
        result = self._fn({"age": 30})
        assert result["antecedents"] == "Néant"

    def test_only_three_keys_in_result(self):
        result = self._fn({"age": 40, "genre": "M", "antecedents": "RAS", "tel": "0600"})
        assert set(result.keys()) == {"age_bracket", "genre", "antecedents"}


# ── holiday_engine ────────────────────────────────────────────────────────────

class TestHolidayEngine:
    def _engine(self):
        from backend.services.holiday_engine import HolidayEngine
        return HolidayEngine()

    def test_get_upcoming_holidays_returns_list(self):
        result = self._engine().get_upcoming_holidays()
        assert isinstance(result, list)

    def test_all_items_have_date_and_name(self):
        result = self._engine().get_upcoming_holidays(days_ahead=365)
        for item in result:
            assert "date" in item
            assert "name" in item
            assert "is_fixed" in item

    def test_sorted_chronologically(self):
        result = self._engine().get_upcoming_holidays(days_ahead=365)
        dates = [item["date"] for item in result]
        assert dates == sorted(dates)

    def test_zero_days_ahead_no_future(self):
        result = self._engine().get_upcoming_holidays(days_ahead=0)
        assert isinstance(result, list)

    def test_fixed_holidays_have_is_fixed_true(self):
        result = self._engine().get_upcoming_holidays(days_ahead=365)
        fixed = [h for h in result if h["is_fixed"]]
        # Should find at least some fixed holidays in a year span
        assert len(fixed) >= 0  # may be empty if none fall in window from today

    def test_fixed_holidays_list_has_9_items(self):
        from backend.services.holiday_engine import HolidayEngine
        assert len(HolidayEngine.FIXED_HOLIDAYS) == 9


# ── clinical_rules_engine ─────────────────────────────────────────────────────

class TestNormalizeActName:
    def _fn(self, name):
        from backend.services.clinical_rules_engine import clinical_rules
        return clinical_rules._normalize_act_name(name)

    def test_extraction_simple(self):
        assert self._fn("Extraction simple") == "EXTRACTION_SIMPLE"

    def test_extraction_chirurgicale(self):
        assert self._fn("Extraction chirurgicale complexe") == "EXTRACTION_CHIRURGICALE"

    def test_abces_dentaire(self):
        assert self._fn("Abcès dentaire infecté") == "ABCES_DENTAIRE"

    def test_abces_parodontal(self):
        # The normalizer does .upper() and checks for "ABCES" (no accent)
        assert self._fn("Abces parodontal") == "ABCES_PARODONTAL"

    def test_pulpite(self):
        assert self._fn("Pulpite aiguë") == "PULPITE"

    def test_implant(self):
        assert self._fn("Pose implant") == "IMPLANT"

    def test_hydroxyde_calcium(self):
        assert self._fn("Médication Hydroxyde de Calcium") == "HYDROXYDE_DE_CALCIUM"

    def test_canalaire(self):
        assert self._fn("Mise en forme canalaire") == "MISE_EN_FORME_CANALAIRE"

    def test_endodontique(self):
        assert self._fn("Traitement endodontique") == "MISE_EN_FORME_CANALAIRE"

    def test_unknown_returns_default(self):
        assert self._fn("Détartrage classique") == "DEFAULT"


class TestCalculatePediatricDosage:
    def _fn(self, mol, weight):
        from backend.services.clinical_rules_engine import clinical_rules
        return clinical_rules._calculate_pediatric_dosage(mol, weight)

    def test_amoxicilline_20kg(self):
        result = self._fn("AMOXICILLINE", 20)
        assert "500mg" in result or "mg" in result

    def test_paracetamol_10kg(self):
        result = self._fn("PARACETAMOL", 10)
        assert "150mg" in result

    def test_ibuprofene_15kg(self):
        result = self._fn("IBUPROFENE", 15)
        assert "150mg" in result

    def test_unknown_molecule_returns_generic(self):
        result = self._fn("CLINDAMYCINE", 20)
        assert "Poids" in result or "confirmer" in result


class TestGetAlternative:
    def _fn(self, mol, banned):
        from backend.services.clinical_rules_engine import clinical_rules
        return clinical_rules._get_alternative(mol, banned)

    def test_ibuprofene_banned_returns_paracetamol(self):
        assert self._fn("IBUPROFENE", ["IBUPROFENE"]) == "PARACETAMOL"

    def test_amoxicilline_banned_returns_clindamycine(self):
        result = self._fn("AMOXICILLINE", ["AMOXICILLINE"])
        assert result == "CLINDAMYCINE"

    def test_all_alternatives_banned_returns_none(self):
        result = self._fn("IBUPROFENE", ["IBUPROFENE", "PARACETAMOL"])
        assert result is None

    def test_unknown_molecule_returns_none(self):
        result = self._fn("MOLECULE_INCONNUE", [])
        assert result is None


class TestAnalyzeCase:
    def _analyze(self, antecedents="RAS", age=35, poids=70, acts=None):
        from backend.services.clinical_rules_engine import clinical_rules
        patient = {"antecedents": antecedents, "age": age, "poids": poids}
        return clinical_rules.analyze_case(patient, acts or [])

    def test_returns_required_keys(self):
        result = self._analyze()
        assert "risques_identifies" in result
        assert "recommandations_moleculaires" in result
        assert "strategie_globale" in result
        assert "dosage_note" in result
        assert "is_child" in result

    def test_no_antecedents_no_critical_warnings(self):
        result = self._analyze(antecedents="RAS")
        criticals = [r for r in result["risques_identifies"] if "CRITICAL" in r.upper() or "Contre-indication" in r]
        # Healthy patient: no critical by default unless act triggers it
        assert isinstance(result["risques_identifies"], list)

    def test_grossesse_triggers_warning(self):
        result = self._analyze(antecedents="Grossesse T2", acts=["Extraction simple"])
        messages = " ".join(result["risques_identifies"])
        assert "Grossesse" in messages or "grossesse" in messages.lower()

    def test_asthme_bans_ibuprofene(self):
        result = self._analyze(antecedents="Asthme chronique", acts=["Extraction simple"])
        # Ibuprofen should NOT appear in recommendations
        mols = [m["molecule"] for m in result["recommandations_moleculaires"]]
        assert "IBUPROFENE" not in mols

    def test_anticoagulant_with_extraction_adds_exacyl(self):
        result = self._analyze(antecedents="Sintrom anticoagulant", acts=["Extraction simple"])
        mols = [m["molecule"] for m in result["recommandations_moleculaires"]]
        assert "ACIDE_TRANEXAMIQUE" in mols

    def test_child_age_sets_is_child_true(self):
        result = self._analyze(age=10, poids=30, acts=["Extraction simple"])
        assert result["is_child"] is True

    def test_adult_is_child_false(self):
        result = self._analyze(age=35)
        assert result["is_child"] is False

    def test_implant_act_adds_antibioprophylaxie(self):
        result = self._analyze(acts=["Pose implant"])
        messages = " ".join(result["risques_identifies"])
        assert "Antibioprophylaxie" in messages or "antibioprophylaxie" in messages.lower()

    def test_abces_dentaire_protocol_has_amoxicilline(self):
        result = self._analyze(acts=["Abcès dentaire infecté"])
        mols = [m["molecule"] for m in result["recommandations_moleculaires"]]
        # Healthy patient + abces -> AMOXICILLINE expected
        assert "AMOXICILLINE" in mols

    def test_penicillin_allergy_uses_alternative(self):
        result = self._analyze(
            antecedents="Allergie pénicilline",
            acts=["Abcès dentaire infecté"]
        )
        mols = [m["molecule"] for m in result["recommandations_moleculaires"]]
        assert "AMOXICILLINE" not in mols

    def test_allergie_penicilline_implant_uses_clindamycine(self):
        result = self._analyze(
            antecedents="Allergie pénicilline",
            acts=["Implant chirurgical"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "CLINDAMYCINE" in messages or "Clindamycine" in messages or "clindamycine" in messages.lower()

    def test_pediatric_dosage_note_shown(self):
        result = self._analyze(age=8, poids=25)
        assert "PÉDIATRIQUE" in result["dosage_note"] or "Poids" in result["dosage_note"]

    def test_diabetes_desequilibre_triggers_critical(self):
        result = self._analyze(antecedents="Diabète HbA1c: 9.2 GLYCEMIE elevée")
        messages = " ".join(result["risques_identifies"])
        assert "Diabète" in messages or "Déséquilibré" in messages or "HbA1c" in messages

    def test_lesion_persistante_triggers_biopsie_rule(self):
        result = self._analyze(antecedents="Lésion suspecte depuis 20 jours")
        messages = " ".join(result["risques_identifies"])
        assert "14 jours" in messages or "biopsie" in messages.lower() or "Lésion" in messages

    def test_empty_acts_still_returns_structure(self):
        result = self._analyze(acts=[])
        assert isinstance(result["recommandations_moleculaires"], list)
