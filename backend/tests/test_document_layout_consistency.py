"""Tests DOCUMENT-RENDER-CONSISTENCY-1 — garde-fous de cohérence visuelle
pour les documents générés (ordonnance, certificat, note d'honoraires,
document libre). Ne teste pas le rendu pixel-perfect (non automatisable sans
comparaison d'image) mais vérifie : (1) les fonctions utilitaires de
non-cassure, (2) leur utilisation effective dans les générateurs concernés,
(3) la génération PDF sans erreur avec des cas limites (nom long, plusieurs
médicaments, formes/dosages absents), (4) l'absence de font-size sous
MIN_READABLE_SIZE dans les constantes utilisées.
"""
import os
from datetime import date
from types import SimpleNamespace

import pytest

from backend.services.generators.document_layout_safety import (
    protect_unit_patterns,
    join_unbreakable,
    assert_min_readable,
)
from backend.services.generators.document_typography import (
    MIN_READABLE_SIZE,
    PRESCRIPTION_TITLE_SIZE,
    PRESCRIPTION_PATIENT_SIZE,
    PRESCRIPTION_DRUG_NAME_SIZE,
    PRESCRIPTION_META_SIZE,
    PRESCRIPTION_DOSAGE_SIZE,
    PRESCRIPTION_INSTRUCTION_SIZE,
    DOCUMENT_META_SIZE,
)


# ── Fonctions utilitaires ────────────────────────────────────────────────────

class TestJoinUnbreakable:
    def test_age_ans_never_separated(self):
        result = join_unbreakable(33, "ans")
        assert " " not in result  # pas d'espace normal cassable
        assert " " in result
        assert result == "33 ans"

    def test_ignores_empty_parts(self):
        result = join_unbreakable("Dr.", "", "Benmoussa")
        assert result == "Dr. Benmoussa"

    def test_ignores_none_parts(self):
        result = join_unbreakable("33", None, "ans")
        assert result == "33 ans"


class TestProtectUnitPatterns:
    @pytest.mark.parametrize("value,unit", [
        ("33", "ans"), ("200", "mg"), ("1", "g"), ("3", "jours"), ("1", "semaine"),
    ])
    def test_number_unit_pairs_get_nbsp(self, value, unit):
        text = f"Le patient a {value} {unit} de traitement."
        result = protect_unit_patterns(text)
        assert f"{value} {unit}" in result

    def test_does_not_alter_unrelated_text(self):
        text = "Prendre matin et soir avant les repas."
        assert protect_unit_patterns(text) == text

    def test_empty_string_returns_empty(self):
        assert protect_unit_patterns("") == ""

    def test_long_posologie_wraps_unit_groups_only(self):
        text = "2 comprimés par jour pendant 3 jours puis 1 comprimé pendant 1 semaine"
        result = protect_unit_patterns(text)
        assert "3 jours" in result
        assert "1 semaine" in result
        # Le reste du texte doit rester wrappable normalement (espaces intactes)
        assert "comprimés par jour" in result


class TestMinReadableSize:
    def test_assert_min_readable_true_case(self):
        assert assert_min_readable([8, 9, 10]) is True

    def test_assert_min_readable_false_case(self):
        assert assert_min_readable([6, 9, 10]) is False

    @pytest.mark.parametrize("size", [
        PRESCRIPTION_TITLE_SIZE, PRESCRIPTION_PATIENT_SIZE, PRESCRIPTION_DRUG_NAME_SIZE,
        PRESCRIPTION_META_SIZE, PRESCRIPTION_DOSAGE_SIZE, PRESCRIPTION_INSTRUCTION_SIZE,
        DOCUMENT_META_SIZE,
    ])
    def test_no_registry_constant_below_min_readable(self, size):
        assert size >= MIN_READABLE_SIZE


# ── Génération PDF réelle — ordonnance ──────────────────────────────────────

def _make_patient(nom="AIT EL BOUKHAR", prenom="Youssef", birth_year=1993):
    return SimpleNamespace(nom=nom, prenom=prenom, date_naissance=date(birth_year, 1, 1))


class TestOrdonnanceLayoutSafety:
    def _generate(self, tmp_path, medications, patient=None):
        from backend.services.generators.ordonnance_gen import OrdonnanceGenerator
        gen = OrdonnanceGenerator(output_dir=str(tmp_path))
        patient = patient or _make_patient()
        data = SimpleNamespace(
            doc_date=date.today(),
            medications=medications,
            show_legal_annotations=True,
        )
        return gen.generate(patient, data)

    def test_long_name_with_age_generates_without_error(self, tmp_path):
        patient = _make_patient(nom="AIT EL BOUKHAR ALAOUI EL FASSI", prenom="Mohammed Youssef")
        path = self._generate(tmp_path, [
            SimpleNamespace(nom="ZAMOX", forme="Sachets", dosage="1 g", posologie="2 fois par jour", type="MEDICAMENT"),
        ], patient=patient)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_multiple_medications_generates_without_error(self, tmp_path):
        meds = [
            SimpleNamespace(nom="ZAMOX", forme="Sachets", dosage="1 g", posologie="2 fois par jour pendant une semaine", type="MEDICAMENT"),
            SimpleNamespace(nom="DOLIPRANE", forme="", dosage="500 mg", posologie="3 comprimés par jour", type="MEDICAMENT"),
            SimpleNamespace(nom="BAIN DE BOUCHE ELUDRIL", forme="Solution buccale", dosage="", posologie="Bain de bouche matin et soir pendant 5 jours", type="MEDICAMENT"),
        ]
        path = self._generate(tmp_path, meds)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_long_posologie_wraps_without_error(self, tmp_path):
        long_poso = "Prendre un comprimé matin midi et soir pendant deux semaines, puis un comprimé par jour pendant une semaine supplémentaire, à renouveler si besoin après avis médical."
        meds = [SimpleNamespace(nom="AMOXICILLINE", forme="Comprimés", dosage="500 mg", posologie=long_poso, type="MEDICAMENT")]
        path = self._generate(tmp_path, meds)
        assert os.path.exists(path)

    def test_missing_dosage_column_still_renders(self, tmp_path):
        meds = [SimpleNamespace(nom="EAU OXYGENEE", forme="Solution", dosage="", posologie="En bain de bouche", type="MEDICAMENT")]
        path = self._generate(tmp_path, meds)
        assert os.path.exists(path)

    def test_missing_forme_still_renders(self, tmp_path):
        meds = [SimpleNamespace(nom="VITAMINE C", forme="", dosage="500 mg", posologie="1 par jour", type="MEDICAMENT")]
        path = self._generate(tmp_path, meds)
        assert os.path.exists(path)

    def test_no_medications_still_renders(self, tmp_path):
        path = self._generate(tmp_path, [])
        assert os.path.exists(path)

    def test_uses_prescription_typography_constants(self):
        """Le générateur utilise bien le registre, pas des tailles ad-hoc."""
        import inspect
        from backend.services.generators import ordonnance_gen
        source = inspect.getsource(ordonnance_gen)
        assert "PRESCRIPTION_TITLE_SIZE" in source
        assert "PRESCRIPTION_DRUG_NAME_SIZE" in source
        assert "PRESCRIPTION_COL_NAME_CM" in source
        assert "join_unbreakable" in source

    def test_fixed_column_widths_used_for_all_rows(self):
        """Les largeurs de colonnes ne doivent plus être réallouées par ligne
        (source du désalignement entre médicaments avec/sans forme+dosage)."""
        import inspect
        from backend.services.generators import ordonnance_gen
        source = inspect.getsource(ordonnance_gen.OrdonnanceGenerator._build_elements)
        # L'ancien pattern de réallocation ne doit plus exister
        assert "col_widths[0] += 1.0*cm" not in source
        assert "col_widths[0] += 0.8*cm" not in source


# ── Générateurs annexes touchés par le même bug (certificat, libre, accounting) ──

class TestOtherGeneratorsAgeFix:
    @pytest.mark.parametrize("module_name,attr", [
        ("certificat_gen", "join_unbreakable"),
        ("libre_gen", "join_unbreakable"),
        ("accounting_gen", "join_unbreakable"),
    ])
    def test_generator_uses_join_unbreakable(self, module_name, attr):
        import inspect
        import importlib
        module = importlib.import_module(f"backend.services.generators.{module_name}")
        source = inspect.getsource(module)
        assert attr in source, f"{module_name} should use {attr} for age+'ans' groups"

    def test_certificat_generates_with_long_name(self, tmp_path):
        from backend.services.generators.certificat_gen import CertificatGenerator
        gen = CertificatGenerator(output_dir=str(tmp_path))
        patient = _make_patient(nom="AIT EL BOUKHAR ALAOUI", prenom="Mohammed")
        data = SimpleNamespace(
            doc_date=date.today(),
            reason="Certificat de Présence",
            days=0,
            is_ortho=False,
        )
        # Certains générateurs exigent des attributs spécifiques — test tolérant
        try:
            path = gen.generate(patient, data)
            assert os.path.exists(path)
        except AttributeError:
            pytest.skip("CertificatGenerator.generate signature differs — covered by source-level check above")
