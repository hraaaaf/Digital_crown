"""Four-phase ODF report projection: presentation-only, no clinical inference.

Values in the cephalometric section come ONLY from the verified, typed R17
source chain. Practitioner narrative is accepted ONLY if the *server-created*
PDF projection explicitly exposes an approved, identity-bound clinician
snapshot. The live R15 projection does not supply one yet and deliberately
leaves the three later phases unfilled.
"""
from __future__ import annotations

from typing import Any, Mapping

# Exact canonical IDs and measurement conventions. Do not derive labels from
# unknown IDs or fall back to "Mesure complémentaire N".
# The mapping is for display identification, NOT normative interpretation.
MESURES_OSSEUSES = {
    "M_SNA_DEG_V1": "SNA",
    "M_SNB_DEG_V1": "SNB",
    "M_ANB_DEG_V1": "ANB",
    "M_SND_DEG_V1": "SND",
    "M_A_NPERP_MM_V1": "Position maxillaire A / N-perp.",
    "M_B_NPERP_MM_V1": "Position mandibulaire B / N-perp.",
    "M_POG_NPERP_MM_V1": "Pogonion / N-perp.",
    "M_SN_GOGN_DEG_V1": "SN / Go-Gn",
    "M_FH_GOME_DEG_V1": "Plan de Francfort / Go-Me",
    "M_ANS_ME_MM_V1": "Hauteur faciale antérieure inférieure",
    "M_PALATAL_PLANE_FH_DEG_V1": "Plan palatin / Francfort",
    "M_OCCLUSAL_PLANE_SN_DEG_V1": "Plan occlusal / SN",
    "M_CO_A_MM_V1": "Longueur maxillaire Co-A",
    "M_CO_GN_ANATOMIC_MM_V1": "Longueur mandibulaire Co-Gn (anatomique)",
    "M_CO_GN_MINUS_CO_A_MM_V1": "Différence de longueur Co-Gn / Co-A",
    "M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1": "Angle facial de Downs",
    "M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1": "Profondeur faciale de Ricketts",
    "M_DOWNS_Y_AXIS_SGN_FH_DEG_V1": "Axe Y de Downs",
    "M_FACIAL_AXIS_RICKETTS_DEG_V1": "Axe facial de Ricketts",
    "M_FACIAL_AXIS_MCNAMARA_DEG_V1": "Axe facial de McNamara",
}
MESURES_DENTOALVEOLAIRES = {
    "M_U1_NA_DEG_V1": "Inclinaison incisive supérieure / NA",
    "M_U1_NA_MM_V1": "Position incisive supérieure / NA",
    "M_U1_FH_DEG_V1": "Incisive supérieure / Francfort",
    "M_U1_A_VERTICAL_MM_V1": "Incisive supérieure / verticale A",
    "M_L1_NB_DEG_V1": "Inclinaison incisive inférieure / NB",
    "M_L1_NB_MM_V1": "Position incisive inférieure / NB",
    "M_L1_GOGN_DEG_V1": "Incisive inférieure / Go-Gn",
    "M_IMPA_GOME_DEG_V1": "IMPA (L1 / Go-Me)",
    "M_FMIA_L1_FH_DEG_V1": "FMIA (L1 / Francfort)",
    "M_INTERINCISAL_DEG_V1": "Angle interincisif",
    "M_L1_EDGE_APOG_MM_V1": "Bord incisif inférieur / A-Pog",
    "M_RICKETTS_L1_APOG_INCLINATION_DEG_V1": "Inclinaison incisive inférieure / A-Pog",
    "M_RICKETTS_OVERJET_FOP_MM_V1": "Surplomb horizontal (plan occlusal Ricketts)",
    "M_RICKETTS_OVERBITE_FOP_MM_V1": "Recouvrement vertical (plan occlusal Ricketts)",
    "M_RICKETTS_MOLAR_RELATION_FOP_MM_V1": "Relation molaire (Ricketts)",
    "M_RICKETTS_CANINE_RELATION_FOP_MM_V1": "Relation canine (Ricketts)",
}

# Conservative identity labels for *observed* casts, never inferred classes.
MOULAGE_KEYS = {
    "classe_molaire_droite": "Relation molaire droite",
    "classe_molaire_gauche": "Relation molaire gauche",
    "classe_canine_droite": "Relation canine droite",
    "classe_canine_gauche": "Relation canine gauche",
    "forme_arcade": "Forme des arcades",
    "ddm_maxillaire": "DDM maxillaire",
    "ddm_mandibulaire": "DDM mandibulaire",
    "commentaire": "Observations sur les moulages",
}


def _identity_equal(a: Any, b: Any) -> bool:
    return isinstance(a, int) and isinstance(b, int) and a > 0 and a == b


def _verified_clinician_snapshot(projection: Mapping[str, Any]) -> dict[str, Any] | None:
    """Only a server-supplied approved source bound to the exact study.

    IMPORTANT: the current R15 real backend always reports clinical validation
    unavailable. This gate is intentionally unreachable via client-submitted
    legacy ai_diagnostic/clinical_data; no new API exposes this snapshot.
    """
    snap = projection.get("practitioner_approved_sections")
    if not isinstance(snap, dict):
        return None
    if not (
        projection.get("clinical_validation_available") is True
        and projection.get("document_state") == "COMPLETE"
        and not projection.get("blocking_gates")
        and snap.get("contract_version") == "ORTHO_PRACTITIONER_APPROVED_V1"
        and snap.get("validation_state") == "APPROVED"
        and isinstance(snap.get("practitioner_id"), int)
        and snap.get("practitioner_id") > 0
        and isinstance(snap.get("validated_at"), str)
        and snap["validated_at"].strip()
        and _identity_equal(snap.get("patient_id"), projection.get("patient_id"))
        and _identity_equal(snap.get("analysis_id"), projection.get("analysis_id"))
        and _identity_equal(snap.get("analysis_revision"), projection.get("analysis_revision"))
    ):
        return None
    return snap


def _ceph_rows(projection: Mapping[str, Any]) -> tuple[list[dict], list[dict]]:
    if projection.get("active_runtime_chain_verified") is not True:
        return [], []
    osseuses, dentaires = [], []
    seen: set[str] = set()
    available_ids = {**MESURES_OSSEUSES, **MESURES_DENTOALVEOLAIRES}
    for m in projection.get("measurements") or []:
        if not isinstance(m, dict):
            continue
        key = m.get("measurement_id")
        if not isinstance(key, str) or key not in available_ids or key in seen:
            continue
        if m.get("scientific_source") != "EVIDENCE_GRAPH_V1":
            continue
        seen.add(key)
        status = m.get("availability_status")
        value = m.get("value")
        from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS
        registry = CANONICAL_MEASUREMENTS.get(key)
        # Unit and source status are NOT freely derived from payload.
        if registry is None or registry.unit is None:
            continue
        # A missing or intentionally blocked value is never shown as valid.
        if status == "AVAILABLE" and isinstance(value, (int, float)) and not isinstance(value, bool):
            from math import isfinite
            if isfinite(value):
                displayed = f"{value:g} {registry.unit}"
            else:
                displayed = "Non calculable"
        else:
            displayed = "Non calculable"
        row = {"label": available_ids[key], "value": displayed}
        (osseuses if key in MESURES_OSSEUSES else dentaires).append((key, row))
    # Registry order = display order, not unpredictable evidence graph order.
    osseuses.sort(key=lambda x: list(MESURES_OSSEUSES).index(x[0]))
    dentaires.sort(key=lambda x: list(MESURES_DENTOALVEOLAIRES).index(x[0]))
    return [row for _, row in osseuses], [row for _, row in dentaires]


def build_ortho_bilan_document(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Build immutable-to-caller four-phase PDF context from backend evidence."""
    osseuse, dentoalveolaire = _ceph_rows(projection)
    approved = _verified_clinician_snapshot(projection)
    moulages: list[dict[str, str]] = []
    diagnostic = ""
    traitement = ""
    if approved:
        section = approved.get("moulages") or {}
        if isinstance(section, dict):
            for key, label in MOULAGE_KEYS.items():
                value = section.get(key)
                if isinstance(value, str) and value.strip():
                    moulages.append({"label": label, "value": value.strip()[:1500]})
                elif key.startswith("ddm_") and isinstance(value, (int, float)) and not isinstance(value, bool):
                    from math import isfinite
                    if isfinite(value):
                        moulages.append({"label": label, "value": f"{value:g} mm"})
        diagnostic = approved.get("resume_diagnostique") or ""
        traitement = approved.get("plan_traitement") or ""
        if not isinstance(diagnostic, str):
            diagnostic = ""
        if not isinstance(traitement, str):
            traitement = ""
    clinical_alerts: list[str] = []
    for stage in projection.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        for key in ("contraindications", "contradictions"):
            for raw in (stage.get(key) or []):
                if not isinstance(raw, str):
                    continue
                # Omit machine IDs here, not clinical findings.
                from backend.services.cephalo_pdf_presentation import clinical_term
                value = clinical_term(raw, "")
                if value and value not in clinical_alerts:
                    clinical_alerts.append(value)
    return {
        "osseuse": osseuse,
        "dentoalveolaire": dentoalveolaire,
        "moulages": moulages,
        "resume_diagnostique": diagnostic.strip()[:10000],
        "plan_traitement": traitement.strip()[:10000],
        "clinical_alerts": clinical_alerts,
        "practitioner_sections_authorized": approved is not None,
    }
