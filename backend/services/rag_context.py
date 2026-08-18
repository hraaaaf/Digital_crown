import logging
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend import models

logger = logging.getLogger(__name__)


def _extract_panoramic_landmarks(panoramics: list) -> list[str]:
    """Extract tooth-localization landmarks only; this does not infer pathology."""
    landmarks = []
    for p in panoramics[:2]:
        detections = (p.detections_data or {}).get("detections", [])
        for d in detections[:3]:
            label = d.get("class_name") or d.get("label", "")
            tooth = d.get("tooth_fdi", "")
            if label:
                entry = f"{label}" + (f" (dent {tooth})" if tooth else "")
                if entry not in landmarks:
                    landmarks.append(entry)
    return landmarks[:5]


def _extract_cephalo_trend(cephalos: list) -> str:
    """Compare IMPA between last 2 cephalo analyses to detect instability."""
    if len(cephalos) < 2:
        return "données insuffisantes"
    a1 = (cephalos[0].angles_data or {})
    a2 = (cephalos[1].angles_data or {})
    impa1 = a1.get("IMPA", {}).get("valeur")
    impa2 = a2.get("IMPA", {}).get("valeur")
    if impa1 is None or impa2 is None:
        return "données insuffisantes"
    diff = impa1 - impa2
    if abs(diff) <= 2:
        return "stable"
    return "amélioration" if diff < 0 else "dégradation"


def build_patient_rag_context(patient_id: int, db: Session, months: int = 24) -> dict[str, Any]:
    """
    Build a rich deterministic patient-history context.
    Queries the last N months of procedures, panoramic tooth landmarks, and cephalo trend.
    """
    try:
        cutoff = datetime.now() - timedelta(days=months * 30)

        acts = (
            db.query(models.Acte)
            .filter(models.Acte.patient_id == patient_id, models.Acte.date_debut >= cutoff)
            .order_by(desc(models.Acte.date_debut))
            .limit(20)
            .all()
        )

        panoramics = (
            db.query(models.PanoramicAnalysis)
            .filter(models.PanoramicAnalysis.patient_id == patient_id)
            .order_by(desc(models.PanoramicAnalysis.created_at))
            .limit(3)
            .all()
        )

        cephalos = (
            db.query(models.CephaloAnalysis)
            .filter(models.CephaloAnalysis.patient_id == patient_id)
            .order_by(desc(models.CephaloAnalysis.created_at))
            .limit(2)
            .all()
        )

        recent_acts = [
            {
                "libelle": a.libelle,
                "date": a.date_debut.strftime("%Y-%m-%d"),
                "type": a.type_acte.value if a.type_acte else "SOIN",
            }
            for a in acts
        ]

        return {
            "recent_acts": recent_acts,
            "panoramic_landmarks": _extract_panoramic_landmarks(panoramics),
            "cephalo_trend": _extract_cephalo_trend(cephalos),
            "acts_count_24m": len(acts),
        }
    except Exception as e:
        logger.warning("RAGContext: failed to build context for patient %d: %s", patient_id, e)
        return {}
