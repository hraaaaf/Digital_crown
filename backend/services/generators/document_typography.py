"""Registre typographique centralisé — Digital Crown PDF System."""

# === Tailles ReportLab (pts) ===
TITLE_SIZE = 20
SECTION_TITLE_SIZE = 14
BODY_SIZE = 11
SMALL_SIZE = 9
TABLE_HEADER_SIZE = 9
TABLE_CELL_SIZE = 9.5
FOOTER_SIZE = 7.5
MIN_READABLE_SIZE = 7.0
LINE_HEIGHT_RATIO = 1.4

# === Largeurs de colonnes table métriques céphalo (%) ===
COL_METRIC_PCT = "40%"
COL_VALEUR_PCT = "18%"
COL_NORME_PCT = "28%"
COL_STATUT_PCT = "14%"

# === Labels courts pour métriques céphalo ===
# Utilisés dans les tables PDF pour éviter les débordements de cellule
METRIC_SHORT_LABELS = {
    "Angle_Nasolabial": "Naso-labial",
    "Inter_Incisif": "Inter-incisif",
    "I_Francfort": "Inc./Francfort",
    "I_NA_mm": "Inc./NA (mm)",
    "I_NB_mm": "Inc./NB (mm)",
    "Décalage_A_B": "Décalage A-B",
    "Decalage_A_B": "Décalage A-B",
    "Profondeur_Faciale": "Prof. Faciale",
    "Situation_A": "Situ. A",
    "Situation_B": "Situ. B",
}

def short_label(metric_name: str) -> str:
    """Retourne le label court pour une métrique céphalo.

    Utilisé uniquement pour les noms de métriques dans les tables,
    jamais pour les valeurs cliniques (qui restent inchangées).
    """
    return METRIC_SHORT_LABELS.get(metric_name, metric_name.replace("_", " "))
