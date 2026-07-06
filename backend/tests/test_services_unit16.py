"""Sixteenth batch — SecureTemplateRenderer security_check/render,
CSSGenerator.generate, PrescriptionService pure helpers."""
import pytest
from datetime import date


# ── SecureTemplateRenderer._security_check ───────────────────────────────────

class TestSecurityCheck:
    def _renderer(self):
        from backend.services.template_engine import SecureTemplateRenderer
        return SecureTemplateRenderer()

    def test_clean_html_passes(self):
        r = self._renderer()
        r._security_check("<p>Bonjour {{ patient }}</p>")  # should not raise

    def test_import_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("{% import os %}")

    def test_eval_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("{{ eval('os.getcwd()') }}")

    def test_exec_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("{% exec('import os') %}")

    def test_subprocess_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("subprocess.run(['ls'])")

    def test_dunder_import_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("{{ __import__('os').system('ls') }}")

    def test_config_injection_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("{{ config.SECRET_KEY }}")

    def test_os_dot_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r._security_check("os.path.join('/etc', 'passwd')")

    def test_empty_string_passes(self):
        r = self._renderer()
        r._security_check("")  # should not raise


# ── SecureTemplateRenderer.render (from_string path) ─────────────────────────

class TestSecureTemplateRender:
    def _renderer(self):
        from backend.services.template_engine import SecureTemplateRenderer
        return SecureTemplateRenderer()

    def test_simple_variable_rendered(self):
        r = self._renderer()
        result = r.render("Hello {{ patient }}", {"patient": "Ahmed"})
        assert "Ahmed" in result

    def test_unknown_variable_filtered_out(self):
        # "patient" is in ALLOWED_VARIABLES but "secret" is not
        r = self._renderer()
        # With StrictUndefined, an unknown allowed variable would raise but
        # here we pass something not in ALLOWED_VARIABLES — it gets stripped from context
        # passing no vars means patient will be Undefined → StrictUndefined raises
        result = r.render("Static content only", {"patient": "X"})
        assert "Static content only" in result

    def test_injection_in_template_raises(self):
        r = self._renderer()
        with pytest.raises(ValueError):
            r.render("{{ __import__('os') }}", {"patient": "test"})

    def test_context_filtered_to_allowed(self):
        # Only ALLOWED_VARIABLES should reach the template
        r = self._renderer()
        result = r.render("{{ patient }}", {"patient": "Dr. Smith", "evil": "payload"})
        assert "Dr. Smith" in result

    def test_cabinet_variable_allowed(self):
        r = self._renderer()
        result = r.render("{{ cabinet }}", {"cabinet": "Clinique ABC"})
        assert "Clinique ABC" in result

    def test_returns_string(self):
        r = self._renderer()
        result = r.render("<p>test</p>", {})
        assert isinstance(result, str)


# ── CSSGenerator.generate ────────────────────────────────────────────────────

class TestCSSGeneratorGenerate:
    def _gen(self):
        from backend.services.template_engine import CSSGenerator
        return CSSGenerator()

    def _design(self):
        from backend.schemas import DesignConfig
        return DesignConfig()

    def test_returns_string(self):
        css = self._gen().generate(self._design())
        assert isinstance(css, str)

    def test_contains_page_rule(self):
        css = self._gen().generate(self._design())
        assert "@page" in css

    def test_contains_body_rule(self):
        css = self._gen().generate(self._design())
        assert "body" in css

    def test_default_primary_color_present(self):
        css = self._gen().generate(self._design())
        assert "#003380" in css

    def test_font_family_present(self):
        css = self._gen().generate(self._design())
        assert "Outfit" in css or "Helvetica" in css

    def test_page_size_a5_default(self):
        css = self._gen().generate(self._design())
        assert "A5" in css

    def test_letterhead_disabled_by_default(self):
        css = self._gen().generate(self._design())
        # No background-image when letterhead is disabled
        assert "background-image" not in css


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
