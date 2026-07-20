"""
Tests unitaires purs pour le mapping des points tissus mous du moteur céphalométrique
(bug audit fonctionnel 2026-07-12 : les alias *_soft émis par le modèle SOTA n'étaient
pas reconnus par key_mapping, donc Ligne E et angle nasolabial n'étaient jamais calculés
avec les points réels du modèle — la narration retombait sur des valeurs par défaut
présentées comme des mesures). Aucune connexion DB.
Exécuter avec : pytest backend/tests/test_cephalo_engine_soft_tissue.py -v
"""
from backend.services.cephalo_engine import cephalo_engine

# Géométrie synthétique minimale : Prn/Pog_soft définissent la ligne E (verticale),
# Ls_soft à gauche, Li_soft à droite — suffisant pour calculer les deux distances et
# l'angle nasolabial sans dépendre du reste du squelette (guardé par des `if pts[...]`).
SOTA_SOFT_TISSUE_POINTS = {
    "Po": (40.0, 40.0),
    "Or": (80.0, 40.0),
    "Prn": (100.0, 40.0),
    "Pog_soft": (100.0, 200.0),
    "Ls_soft": (92.0, 100.0),
    "Li_soft": (108.0, 120.0),
    "Sn_soft": (100.0, 60.0),
}

LEGACY_SOFT_TISSUE_POINTS = {
    "Po": (40.0, 40.0),
    "Or": (80.0, 40.0),
    "Prn": (100.0, 40.0),
    "Pog_soft": (100.0, 200.0),
    "Ls": (92.0, 100.0),
    "Li": (108.0, 120.0),
}


class TestSotaSoftTissueMapping:
    def test_ligne_e_and_nasolabial_computed_with_sota_aliases(self):
        result = cephalo_engine.calculate_metrics(SOTA_SOFT_TISSUE_POINTS, custom_mm_ratio=0.5)
        esth = result.metrics.analyse_esthetique
        assert esth.Ligne_E_Ls.valeur is not None
        assert esth.Ligne_E_Li.valeur is not None
        assert esth.Angle_Nasolabial.valeur is not None

    def test_narrative_reports_non_evaluable_without_cutaneous_points(self):
        # Aucun point cutané (Prn/Pog_soft/Ls*/Li*/Sn*) : la synthèse esthétique ne doit
        # jamais fabriquer "normal (102.0°)" ou un profil "droit" par défaut.
        skeleton_only = {"S": (50.0, 50.0), "N": (60.0, 40.0)}
        result = cephalo_engine.calculate_metrics(skeleton_only, custom_mm_ratio=0.5)
        esth = result.metrics.analyse_esthetique
        assert esth.Ligne_E_Ls.valeur is None
        assert esth.Angle_Nasolabial.valeur is None

        diagnostic = result.ai_narrative["diagnostic_squelettique"]
        esthetic_section = diagnostic.split("ANALYSE ESTHÉTIQUE :")[-1]
        assert "non évaluable" in esthetic_section
        assert "102" not in esthetic_section
        assert "profil_cutane" not in result.ai_narrative

    def test_legacy_aliases_still_work_non_regression(self):
        result = cephalo_engine.calculate_metrics(LEGACY_SOFT_TISSUE_POINTS, custom_mm_ratio=0.5)
        esth = result.metrics.analyse_esthetique
        assert esth.Ligne_E_Ls.valeur is not None
        assert esth.Ligne_E_Li.valeur is not None
