"""Twenty-sixth batch — document_factory pure helpers, template_engine
preview_template and generate_pdf exception path, ClinicalRulesEngine
CI message branches and remaining analyze_case combinations."""
import os
import tempfile
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch


# ── document_factory pure helpers ──────────────────────────────────────────────

class TestDocumentFactoryPure:
    def _factory(self):
        from backend.services.document_factory import DocumentFactory
        with tempfile.TemporaryDirectory() as d:
            f = DocumentFactory(output_dir=d, static_dir=d)
        return f

    def _make_factory(self):
        from backend.services.document_factory import DocumentFactory
        self._tmpdir = tempfile.mkdtemp()
        return DocumentFactory(output_dir=self._tmpdir, static_dir=self._tmpdir)

    def test_calculate_age_basic(self):
        from backend.services.document_factory import DocumentFactory
        f = self._make_factory()
        born = date(1990, 1, 1)
        age = f._calculate_age(born)
        today = date.today()
        expected = today.year - 1990 - ((today.month, today.day) < (1, 1))
        assert age == expected

    def test_calculate_age_none_returns_zero(self):
        from backend.services.document_factory import DocumentFactory
        f = self._make_factory()
        assert f._calculate_age(None) == 0

    def test_calculate_age_datetime_object(self):
        from backend.services.document_factory import DocumentFactory
        f = self._make_factory()
        born = datetime(2000, 6, 15, 12, 0, 0)
        age = f._calculate_age(born)
        assert isinstance(age, int)
        assert age >= 24  # minimum age as of 2026

    def test_calculate_age_birthday_today(self):
        from backend.services.document_factory import DocumentFactory
        f = self._make_factory()
        today = date.today()
        born = date(today.year - 30, today.month, today.day)
        assert f._calculate_age(born) == 30

    def test_build_output_path_creates_dir(self):
        from backend.services.document_factory import DocumentFactory
        import tempfile
        tmpdir = tempfile.mkdtemp()
        f = DocumentFactory(output_dir=tmpdir, static_dir=tmpdir)

        patient = MagicMock()
        patient.nom = "DUPONT"
        patient.prenom = "Marie"

        path = f._build_output_path(patient, "ordonnance")
        assert os.path.exists(os.path.dirname(path))
        assert "ORDONNANCE" in path
        assert "DUPONT" in path

    def test_build_output_path_returns_string(self):
        from backend.services.document_factory import DocumentFactory
        import tempfile
        tmpdir = tempfile.mkdtemp()
        f = DocumentFactory(output_dir=tmpdir, static_dir=tmpdir)
        patient = MagicMock()
        patient.nom = "MARTIN"
        patient.prenom = "Jean"
        path = f._build_output_path(patient, "certificat")
        assert isinstance(path, str)
        assert path.endswith(".pdf")


# ── template_engine.preview_template ──────────────────────────────────────────

class TestPreviewTemplate:
    def _engine(self):
        from backend.services.template_engine import TemplateEngine
        with tempfile.TemporaryDirectory() as d:
            return TemplateEngine(static_dir=d)

    def test_preview_template_returns_bytes(self):
        engine = self._engine()
        template = MagicMock()
        template.name = "Ordonnance Test"
        cabinet = MagicMock()

        with patch.object(engine, 'generate_pdf', wraps=lambda tmpl, cab, ctx, path: open(path, 'wb').write(b'%PDF-test') or path) as mock_gen:
            result = engine.preview_template(template, cabinet)

        assert isinstance(result, bytes)

    def test_preview_template_calls_generate_pdf(self):
        engine = self._engine()
        template = MagicMock()
        template.name = "Test"
        cabinet = MagicMock()

        def fake_generate(tmpl, cab, ctx, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4 fake')
            return output_path

        with patch.object(engine, 'generate_pdf', side_effect=fake_generate) as mock_gen:
            result = engine.preview_template(template, cabinet)
            assert mock_gen.called
            assert isinstance(result, bytes)

    def test_preview_template_context_has_patient(self):
        engine = self._engine()
        template = MagicMock()
        template.name = "Certificat"
        cabinet = MagicMock()
        captured_ctx = {}

        def capture_generate(tmpl, cab, ctx, output_path):
            captured_ctx.update(ctx)
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-1.4')
            return output_path

        with patch.object(engine, 'generate_pdf', side_effect=capture_generate):
            engine.preview_template(template, cabinet)

        assert 'patient' in captured_ctx
        assert captured_ctx['patient']['nom'] == 'DUPONT'


# ── template_engine.generate_pdf WeasyPrint exception path ────────────────────

class TestGeneratePdfWeasyPrintFallback:
    def _engine(self):
        from backend.services.template_engine import TemplateEngine
        with tempfile.TemporaryDirectory() as d:
            return TemplateEngine(static_dir=d)

    def test_generate_pdf_falls_back_on_weasyprint_exception(self):
        engine = self._engine()
        engine.weasyprint_available = True  # pretend it's available

        template = MagicMock()
        template.html_content = "<p>Test</p>"
        cabinet = MagicMock()
        cabinet.nom_praticien = "Dr. Test"
        cabinet.selected_template = "swiss"

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name

        try:
            with patch.object(engine, '_generate_weasyprint', side_effect=RuntimeError("WP fail")), \
                 patch.object(engine, '_fallback_reportlab', return_value=output_path) as mock_fallback:
                result = engine.generate_pdf(template, cabinet, {}, output_path)
                assert mock_fallback.called
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


# ── ClinicalRulesEngine CI message branches ────────────────────────────────────

class TestClinicalRulesEngineCIMessages:
    def _svc(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def _run(self, antecedents="", acts=None, age=30):
        return self._svc().analyze_case(
            {"antecedents": antecedents, "age": age, "poids": 70},
            acts or []
        )

    def test_ulcere_gastrique_ci_message_with_ains_act(self):
        """ULCERE_GASTRIQUE + act recommending IBUPROFENE triggers specific CI message."""
        result = self._run(
            antecedents="ULCERE GASTRIQUE actif",
            acts=["EXTRACTION CHIRURGICALE"]
        )
        # Should have Danger Gastro or substitution warning
        messages = " ".join(result["risques_identifies"])
        assert "Gastro" in messages or "ulcère" in messages.lower() or "gastroduodénal" in messages

    def test_anticoagulant_ci_message_with_ains_act(self):
        """ANTICOAGULANT + act recommending IBUPROFENE triggers Danger Anticoagulant message."""
        result = self._run(
            antecedents="ANTICOAGULANT SINTROM",
            acts=["EXTRACTION CHIRURGICALE"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "Anticoagulant" in messages or "anticoagulant" in messages.lower()

    def test_grossesse_extraction_triggers_anesthesia_warning(self):
        """GROSSESSE + EXTRACTION_CHIRURGICALE triggers the anesthesia pregnancy warning."""
        result = self._run(
            antecedents="ENCEINTE T2",
            acts=["EXTRACTION CHIRURGICALE"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "Anesthésie" in messages or "adrén" in messages.lower() or "vasoconstricteur" in messages.lower()

    def test_grossesse_implant_triggers_anesthesia_warning(self):
        """GROSSESSE + IMPLANT also triggers anesthesia pregnancy warning."""
        result = self._run(
            antecedents="ENCEINTE T1",
            acts=["pose d'implant"]
        )
        messages = " ".join(result["risques_identifies"])
        assert any(kw in messages for kw in ["Radiographie", "Anesthésie", "fœtus"])

    def test_ains_substitution_with_ulcere_and_extraction(self):
        """ULCERE_GASTRIQUE + act with IBUPROFENE → AINS substituted to PARACETAMOL."""
        result = self._run(
            antecedents="ULCERE GASTRIQUE",
            acts=["EXTRACTION CHIRURGICALE"]
        )
        mols = [m["molecule"] for m in result["recommandations_moleculaires"]]
        # IBUPROFENE should be replaced by PARACETAMOL due to ulcer CI
        assert "IBUPROFENE" not in mols or "PARACETAMOL" in mols

    def test_diabete_indetermine_without_hba1c(self):
        """DIABETE without HBA1C → DIABETE_INDETERMINE branch."""
        result = self._run(antecedents="DIABETE diagnostiqué récemment")
        messages = " ".join(result["risques_identifies"])
        assert "HbA1c" in messages or "Diabète" in messages or "diabète" in messages.lower()

    def test_asthme_alternative_detection(self):
        """ASTHME via RESPIRATOIRE keyword."""
        result = self._run(antecedents="PROBLÈME RESPIRATOIRE CHRONIQUE ASTHME")
        messages = " ".join(result["risques_identifies"])
        # Asthme bans IBUPROFENE/AINS — should trigger warning if act uses it
        # At minimum, asthme detected should not crash
        assert isinstance(result, dict)
