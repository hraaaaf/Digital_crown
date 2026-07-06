"""Tests DOC-LAYOUT-SAFETY-1 — sécurité mise en page PDF."""
from pathlib import Path


# === Registre typographique ===

def test_typography_registry_importable():
    """Registre typographique importable sans erreur."""
    from backend.services.generators.document_typography import (
        TITLE_SIZE, SECTION_TITLE_SIZE, BODY_SIZE, MIN_READABLE_SIZE, LINE_HEIGHT_RATIO
    )
    assert TITLE_SIZE == 20
    assert SECTION_TITLE_SIZE == 14
    assert BODY_SIZE == 11
    assert MIN_READABLE_SIZE == 7.0


def test_min_readable_size_is_at_least_7():
    """Taille minimale lisible >= 7pt."""
    from backend.services.generators.document_typography import MIN_READABLE_SIZE
    assert MIN_READABLE_SIZE >= 7.0


def test_line_height_ratio_is_reasonable():
    """Interligne entre 1.2 et 1.8."""
    from backend.services.generators.document_typography import LINE_HEIGHT_RATIO
    assert 1.2 <= LINE_HEIGHT_RATIO <= 1.8


# === Labels courts pour métriques ===

def test_all_short_labels_under_20_chars():
    """Tous les labels courts < 20 caractères."""
    from backend.services.generators.document_typography import METRIC_SHORT_LABELS
    for key, label in METRIC_SHORT_LABELS.items():
        assert len(label) < 20, f"Label trop long : {key} → {label} ({len(label)} chars)"


def test_short_label_known_metric_returns_short_name():
    """short_label retourne le label court pour une métrique connue."""
    from backend.services.generators.document_typography import short_label
    assert short_label("Angle_Nasolabial") == "Naso-labial"
    assert short_label("Inter_Incisif") == "Inter-incisif"
    assert short_label("I_Francfort") == "Inc./Francfort"


def test_short_label_unknown_metric_replaces_underscore():
    """short_label remplace _ par espace pour métrique inconnue."""
    from backend.services.generators.document_typography import short_label
    assert short_label("Unknown_Metric") == "Unknown Metric"
    assert short_label("SNA") == "SNA"


def test_short_label_never_returns_empty_string():
    """short_label ne retourne jamais une chaîne vide."""
    from backend.services.generators.document_typography import short_label
    assert short_label("") != ""
    assert short_label("Any_Metric") != ""


def test_short_label_does_not_truncate_clinical_value():
    """short_label ne s'applique qu'aux noms, jamais aux valeurs numériques."""
    from backend.services.generators.document_typography import short_label
    # Noms de métriques → labels courts
    assert short_label("SNA") in ("SNA", "SNA".replace("_", " "))
    # Valeurs numériques → inchangées
    assert short_label("82.0") == "82.0"
    assert short_label("5.4") == "5.4"


# === Templates HTML — CSS fixes ===

def test_bilan_ortho_table_has_table_layout_fixed():
    """bilan_ortho_elite.html a table-layout: fixed."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "table-layout: fixed" in content, "table-layout: fixed manquant"


def test_bilan_ortho_table_has_colgroup():
    """bilan_ortho_elite.html a <colgroup> pour la table de l'annexe."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "<colgroup>" in content, "<colgroup> manquant"
    assert "40%" in content, "Largeur colonne métrique (40%) manquante"
    assert "18%" in content, "Largeur colonne valeur (18%) manquante"


def test_bilan_ortho_th_has_ellipsis():
    """th (en-têtes) peuvent avoir text-overflow: ellipsis."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    # Vérifier que text-overflow: ellipsis existe (pour en-têtes, c'est OK)
    assert "text-overflow: ellipsis" in content


def test_bilan_ortho_td_has_overflow_visible():
    """td (cellules données) ont overflow: visible — données jamais cachées."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "overflow: visible" in content, "overflow: visible manquant pour td"


def test_bilan_ortho_text_block_has_word_break():
    """Les blocs narratifs (.text-block) permettent word-break."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    assert "word-break: break-word" in content


def test_bilan_ortho_text_block_no_ellipsis():
    """.text-block jamais text-overflow: ellipsis (les données cliniques ne sont jamais tronquées)."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    # Chercher une règle CSS pour .text-block
    import re
    # Extraire le style de .text-block
    match = re.search(r'\.text-block\s*\{([^}]+)\}', content)
    if match:
        text_block_css = match.group(1)
        assert "text-overflow: ellipsis" not in text_block_css, \
            "ERREUR : .text-block ne doit pas avoir text-overflow: ellipsis"


def test_bilan_ortho_footer_has_page_break_avoid():
    """Footer a page-break-inside: avoid."""
    template_path = Path(__file__).parent.parent / "templates" / "bilan_ortho_elite.html"
    content = template_path.read_text(encoding="utf-8")
    # Vérifier que footer ou signature a page-break-inside: avoid
    assert "page-break-inside: avoid" in content


def test_cephalo_table_has_table_layout_fixed():
    """cephalo_report_elite.html a table-layout: fixed (si existe)."""
    template_path = Path(__file__).parent.parent / "templates" / "cephalo_report_elite.html"
    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        # Si la template a des tables, elle doit utiliser table-layout: fixed
        if "<table>" in content:
            assert "table-layout: fixed" in content


def test_panoramic_table_properties():
    """panoramic_elite.html respecte les règles d'overflow."""
    template_path = Path(__file__).parent.parent / "templates" / "panoramic_elite.html"
    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        if "<table>" in content:
            # Vérifier que table-layout: fixed OU word-break est présent
            assert ("table-layout: fixed" in content or "word-break" in content), \
                "panoramic_elite.html doit avoir table-layout: fixed ou word-break"


# === Intégration registre typographique ===

def test_short_label_used_in_bilan_ortho_gen():
    """bilan_ortho_gen.py importe et utilise short_label."""
    import inspect
    from backend.services.generators import bilan_ortho_gen
    source = inspect.getsource(bilan_ortho_gen.BilanOrthoPDFGenerator._generate_weasyprint)
    assert "short_label" in source, "short_label doit être importé et utilisé dans bilan_ortho_gen.py"
