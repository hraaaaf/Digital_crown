import logging
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend import models

logger = logging.getLogger(__name__)


def _extract_panoramic_landmarks(panoramics: list) -> list[str]:
    """Extract FDI tooth-location landmarks only; never propagate pathology labels."""
    landmarks: list[str] = []

    def _fdi(value: Any) -> str | None:
        raw = str(value or "").strip()
        if len(raw) != 2 or not raw.isdigit():
            return None
        quadrant, tooth = int(raw[0]), int(raw[1])
        if quadrant not in {1, 2, 3, 4} or tooth not in range(1, 9):
            return None
        return raw

    for p in panoramics[:2]:
        detections = (p.detections_data or {}).get("detections", [])
        for detection in detections:
            # Prefer the explicit FDI locator. If the detector emits a generic
            # tooth class, its label may carry the FDI number instead.
            tooth = _fdi(detection.get("tooth_fdi"))
            class_name = str(detection.get("class_name") or detection.get("class") or "").strip().lower()
            if tooth is None and class_name in {"tooth", "dent", "dental_tooth"}:
                tooth = _fdi(detection.get("label"))
            if tooth is None:
                continue

            entry = f"Dent {tooth}"
            if entry not in landmarks:
                landmarks.append(entry)
            if len(landmarks) == 5:
                return landmarks

    return landmarks


def _extract_cephalo_trend(cephalos: list) -> str:
    """Expose uniquement la variation IMPA brute entre les deux dernières analyses."""
    if len(cephalos) < 2:
        return "données insuffisantes"
    a1 = (cephalos[0].angles_data or {})
    a2 = (cephalos[1].angles_data or {})
    impa1 = a1.get("IMPA", {}).get("valeur")
    impa2 = a2.get("IMPA", {}).get("valeur")
    if impa1 is None or impa2 is None:
        return "données insuffisantes"
    diff = float(impa1) - float(impa2)
    return f"ΔIMPA {diff:+.1f}° entre les deux dernières analyses"


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
