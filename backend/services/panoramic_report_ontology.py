from typing import Dict, Tuple

# Canonical reporting domains derived from the dental panoramic structured-report
# literature. These are report/checklist domains, not automated diagnostic targets.
PANORAMIC_REPORT_DOMAINS: Tuple[str, ...] = (
    "dental_anomalies",
    "restorations",
    "caries",
    "apical",
    "periodontium",
    "jawbone",
    "tmj",
    "sinuses",
)

PANORAMIC_DOMAIN_TITLES: Dict[str, str] = {
    "dental_anomalies": "Dentition et anomalies dentaires",
    "restorations": "Restaurations / prothèses / implants",
    "caries": "Lésions carieuses",
    "apical": "Régions périapicales / endodontie",
    "periodontium": "Parodonte et support osseux",
    "jawbone": "Maxillaire et mandibule",
    "tmj": "Articulations temporo-mandibulaires",
    "sinuses": "Sinus maxillaires",
}

# Negative statements are emitted only after an explicit practitioner
# confirmation of status="normal". Missing status is always non-assessed.
PANORAMIC_EXPLICIT_NORMAL_TEXT: Dict[str, str] = {
    "dental_anomalies": "Pas d'anomalie dentaire supplémentaire documentée.",
    "restorations": "Pas d'autre restauration, prothèse ou implant remarquable documenté.",
    "caries": "Pas d'autre image carieuse documentée.",
    "apical": "Pas d'autre anomalie périapicale documentée.",
    "periodontium": "Pas d'autre anomalie parodontale ou du support osseux documentée.",
    "jawbone": "Pas d'anomalie osseuse maxillo-mandibulaire documentée.",
    "tmj": "Pas d'anomalie osseuse condylienne documentée sur cette panoramique.",
    "sinuses": "Pas d'anomalie sinusienne documentée sur les territoires visibles.",
}

PANORAMIC_STATUS_VALUES = ("not_assessed", "normal", "abnormal")
PANORAMIC_IMAGE_QUALITY_VALUES = ("not_assessed", "diagnostic", "limited", "non_diagnostic")
