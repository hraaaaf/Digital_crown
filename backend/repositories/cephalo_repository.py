from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend import models
import logging

logger = logging.getLogger(__name__)

_EVIDENCE_GRAPH_KEY = "_evidence_graph_v1"


def _canonicalize_evidence_projection(results: Dict[str, Any]) -> Dict[str, Any]:
    """Persist one explicit active landmark set whenever it can be proven safely.

    Historical landmarks remain inside the typed graph for audit. The active set is
    explicit so later construction/calibration/read transitions never have to guess
    which evidence object is current. Ambiguous legacy graphs are intentionally left
    without inferred refs and will fail closed on the canonical typed read path.
    """
    projected = dict(results)
    raw_graph = projected.get(_EVIDENCE_GRAPH_KEY)
    if not isinstance(raw_graph, dict):
        return projected

    graph = dict(raw_graph)
    graph.pop("authority_status", None)

    if "current_landmark_refs" not in graph:
        raw_landmarks = graph.get("landmarks", [])
        if isinstance(raw_landmarks, list):
            refs: list[str] = []
            landmark_ids: set[str] = set()
            valid = True
            for item in raw_landmarks:
                if not isinstance(item, dict):
                    valid = False
                    break
                evidence_id = item.get("evidence_id")
                landmark_id = item.get("landmark_id")
                if (
                    not isinstance(evidence_id, str)
                    or not evidence_id.strip()
                    or not isinstance(landmark_id, str)
                    or not landmark_id.strip()
                    or landmark_id in landmark_ids
                ):
                    valid = False
                    break
                refs.append(evidence_id)
                landmark_ids.add(landmark_id)
            if valid:
                graph["current_landmark_refs"] = refs

    projected[_EVIDENCE_GRAPH_KEY] = graph
    return projected


def _merge_calibration_projection(previous: Any, results: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve calibration provenance across ordinary analysis saves.

    Refinement recomputes geometry but is not itself a calibration transition. It
    therefore must not erase a persisted candidate/decision or downgrade the
    specific AUTO_VERIFIED / CLINICIAN_CONFIRMED projection to generic
    ``verified``.
    """
    merged = _canonicalize_evidence_projection(results)
    if not isinstance(previous, dict):
        return merged

    for key in ("calibration_candidate", "calibration_decision"):
        if key in previous and key not in merged:
            merged[key] = previous[key]

    previous_status = previous.get("calibration_status")
    if (
        merged.get("calibration_status") == "verified"
        and previous_status in {"auto_verified", "clinician_confirmed"}
    ):
        merged["calibration_status"] = previous_status

    return merged


class CephaloRepository:
    """
    Gère la persistance des analyses céphalométriques.
    Isole SQLAlchemy de la logique métier.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, analysis_id: int) -> Optional[models.CephaloAnalysis]:
        """Récupère une analyse par son ID."""
        return self.db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.id == analysis_id).first()

    def get_by_patient(self, patient_id: int) -> List[models.CephaloAnalysis]:
        """Récupère toutes les analyses d'un patient."""
        return self.db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).all()

    def create(
        self,
        patient_id: int,
        image_path: str,
        landmarks: List[Dict],
        results: Dict,
        mm_per_pixel: Optional[float] = None,
    ) -> models.CephaloAnalysis:
        """Crée une analyse sans inventer d'échelle physique par défaut."""
        db_analysis = models.CephaloAnalysis(
            patient_id=patient_id,
            image_original_path=image_path,
            landmarks_data=landmarks,
            angles_data=_canonicalize_evidence_projection(results),
            mm_per_pixel=mm_per_pixel,
        )
        self.db.add(db_analysis)
        self.db.commit()
        self.db.refresh(db_analysis)
        return db_analysis

    def update(
        self,
        analysis_id: int,
        landmarks: List[Dict],
        results: Dict,
        mm_per_pixel: Optional[float] = None,
    ) -> Optional[models.CephaloAnalysis]:
        """Met à jour l'analyse sans transformer un save en transition de calibration."""
        db_analysis = self.get_by_id(analysis_id)
        if not db_analysis:
            return None

        db_analysis.landmarks_data = landmarks
        db_analysis.angles_data = _merge_calibration_projection(db_analysis.angles_data, results)
        if mm_per_pixel is not None:
            db_analysis.mm_per_pixel = mm_per_pixel

        self.db.commit()
        self.db.refresh(db_analysis)
        return db_analysis

    def delete(self, analysis_id: int) -> bool:
        """Supprime une analyse."""
        db_analysis = self.get_by_id(analysis_id)
        if db_analysis:
            self.db.delete(db_analysis)
            self.db.commit()
            return True
        return False
