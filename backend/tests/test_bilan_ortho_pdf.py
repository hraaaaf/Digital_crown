"""Tests CEPHALO-PDF-SAFETY-1 — validateur branché + modes pré-bilan/archive."""
import pytest
from pathlib import Path


# --- Tests : template statique ---

def test_signature_electronique_absente_template():
    """'Signature électronique certifiée' absent du template."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "Signature électronique certifiée" not in content


def test_diagnostic_clinique_absent_qr_template():
    """'diagnostic clinique' absent du texte QR du template."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "authenticité de ce diagnostic clinique" not in content


def test_donnees_severes_absent_template():
    """'Données Céphalométriques Sévères' absent du template."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "Données Céphalométriques Sévères" not in content


def test_praticien_responsable_present_template():
    """'Praticien responsable' présent dans le template (remplace signature électronique)."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "Praticien responsable" in content


def test_authenticite_du_rapport_present_template():
    """'authenticité du rapport' présent dans le texte QR (remplace 'diagnostic clinique')."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "authenticité" in content.lower()
    assert "du rapport" in content.lower()


# --- Tests : mesures unitaires (cephalo_measure_registry) ---

def test_recouvrement_unit_is_mm():
    """Recouvrement → unité mm selon measure_registry."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("Recouvrement") == "mm"


def test_surplomb_unit_is_mm():
    """Surplomb → unité mm."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("Surplomb") == "mm"


def test_situation_a_unit_is_mm():
    """Situation A → unité mm."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("Situation_A") == "mm"


def test_situation_b_unit_is_mm():
    """Situation B → unité mm."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("Situation_B") == "mm"


def test_sna_unit_is_degrees():
    """SNA → unité °."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("SNA") == "°"


def test_snb_unit_is_degrees():
    """SNB → unité °."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("SNB") == "°"


def test_anb_unit_is_degrees():
    """ANB → unité °."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("ANB") == "°"


def test_impa_unit_is_degrees():
    """IMPA → unité °."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("IMPA") == "°"


def test_inter_incisif_unit_is_degrees():
    """Inter_Incisif → unité °."""
    from backend.services.cephalo_measure_registry import cephalo_unit
    assert cephalo_unit("Inter_Incisif") == "°"


# --- Tests : CephaloViewModel schéma ---

def test_cephaleo_viewmodel_has_is_pre_bilan():
    """CephaloViewModel a le champ is_pre_bilan."""
    from backend import schemas
    assert hasattr(schemas.CephaloViewModel, '__annotations__')
    assert 'is_pre_bilan' in schemas.CephaloViewModel.__annotations__


def test_cephaleo_viewmodel_has_validation_warnings():
    """CephaloViewModel a le champ validation_warnings."""
    from backend import schemas
    assert hasattr(schemas.CephaloViewModel, '__annotations__')
    assert 'validation_warnings' in schemas.CephaloViewModel.__annotations__


def test_profondeur_faciale_excluded_from_pdf_metrics():
    """Profondeur_Faciale est exclus des métriques du PDF."""
    from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator
    gen = BilanOrthoPDFGenerator()
    # Vérifier que LINEAR_MEASURES_EXCLUDED contient Profondeur_Faciale
    # (inspection statique du code source)
    import inspect
    source = inspect.getsource(gen._generate_weasyprint)
    assert "Profondeur_Faciale" in source
    assert "LINEAR_MEASURES_EXCLUDED" in source


# --- Tests : validateur intégré ---

def test_cephalo_consistency_validator_exists():
    """Le validateur de cohérence céphalo existe et est importable."""
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    assert cephalo_consistency_validator is not None


def test_cephalo_consistency_validator_has_validate_method():
    """Le validateur a la méthode validate()."""
    from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
    assert hasattr(CephaloConsistencyValidator, 'validate')


def test_validation_result_has_is_valid():
    """ValidationResult a la propriété is_valid."""
    from backend.services.cephalo_consistency_validator import ValidationResult
    result = ValidationResult()
    assert hasattr(result, 'is_valid')
    assert result.is_valid is True  # Pas d'erreurs → valide


def test_validation_result_has_fatals_and_warnings():
    """ValidationResult a les listes fatals et warnings."""
    from backend.services.cephalo_consistency_validator import ValidationResult
    result = ValidationResult(fatals=["error"], warnings=["warning"])
    assert result.fatals == ["error"]
    assert result.warnings == ["warning"]


def test_validation_sna_hard_bounds():
    """SNA entre 60 et 105° est acceptable (bornes physiologiques)."""
    from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
    validator = CephaloConsistencyValidator()
    # SNA = 82 est normal
    angles_data = {
        "analyse_osseuse": {
            "SNA": {"valeur": 82.0, "unite": "°"},
            "SNB": {"valeur": 80.0, "unite": "°"},
            "ANB": {"valeur": 2.0, "unite": "°"},
        }
    }
    result = validator.validate(angles_data)
    # SNA=82 ne doit pas générer d'erreur fatale
    assert not any("SNA" in f and "fatal" in f.lower() for f in result.fatals)


def test_validation_sna_out_of_bounds_fatal():
    """SNA > 105° ou < 60° génère erreur FATALE."""
    from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
    validator = CephaloConsistencyValidator()
    angles_data = {
        "analyse_osseuse": {
            "SNA": {"valeur": 110.0, "unite": "°"},  # Hors limites
            "SNB": {"valeur": 80.0, "unite": "°"},
            "ANB": {"valeur": 30.0, "unite": "°"},
        }
    }
    result = validator.validate(angles_data)
    # Doit avoir au moins une erreur fatale
    assert not result.is_valid
    assert len(result.fatals) > 0
