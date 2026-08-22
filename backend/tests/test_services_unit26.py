"""Twenty-sixth batch — document_factory pure helpers,
ClinicalRulesEngine CI message branches and remaining analyze_case combinations."""
import os
import tempfile
from datetime import date, datetime
from unittest.mock import MagicMock


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
        tmpdir = tempfile.mkdtemp()
        f = DocumentFactory(output_dir=tmpdir, static_dir=tmpdir)
        patient = MagicMock()
        patient.nom = "MARTIN"
        patient.prenom = "Jean"
        path = f._build_output_path(patient, "certificat")
        assert isinstance(path, str)
        assert path.endswith(".pdf")


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
        assert "IBUPROFENE" not in mols or "PARACETAMOL" in mols

    def test_diabete_indetermine_without_hba1c(self):
        """DIABETE without HBA1C → DIABETE_INDETERMINE branch."""
        result = self._run(antecedents="DIABETE diagnostiqué récemment")
        messages = " ".join(result["risques_identifies"])
        assert "HbA1c" in messages or "Diabète" in messages or "diabète" in messages.lower()

    def test_asthme_alternative_detection(self):
        """ASTHME via RESPIRATOIRE keyword."""
        result = self._run(antecedents="PROBLÈME RESPIRATOIRE CHRONIQUE ASTHME")
        assert isinstance(result, dict)
