from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.repositories.cephalo_repository import CephaloRepository
from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine
from backend.services.vision_service import vision_engine
from backend.services.bilan_ortho_engine import bilan_ortho_engine
from backend.services.cephalo_runtime_evidence import (
    EVIDENCE_GRAPH_KEY,
    build_cephalo_runtime_evidence_payload,
)
from backend.services.cephalo_landmark_correction_evidence import (
    landmark_submission_changed,
    rebuild_evidence_after_landmark_edit,
)
from backend import schemas, models
import datetime as dt
import logging
import math

logger = logging.getLogger(__name__)


def _calculate_age(birth_date) -> Optional[int]:
    if birth_date is None:
        return None
    from datetime import date
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _patient_age_and_sex(patient: Optional["models.Patient"]) -> Tuple[Optional[int], Optional[str]]:
    if patient is None:
        return None, None
    return _calculate_age(patient.date_naissance), patient.sexe


def _remove_autonomous_treatment(payload: Dict[str, Any]) -> Dict[str, Any]:
    narrative = payload.get("ai_narrative")
    if isinstance(narrative, dict):
        narrative.pop("strategie_therapeutique", None)
    return payload


def _same_optional_ratio(left: Optional[float], right: Optional[float]) -> bool:
    if left is None or right is None:
        return left is right
    try:
        left_value = float(left)
        right_value = float(right)
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(left_value)
        and math.isfinite(right_value)
        and math.isclose(left_value, right_value, rel_tol=0.0, abs_tol=1e-12)
    )


class CephaloService:
    """Runtime orchestrator for cephalometric geometry and persistence."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CephaloRepository(db)

    def process_new_radio(self, patient_id: int, file_path: str, db_path: str) -> Dict[str, Any]:
        logger.info("Analyse Vision pour le patient %s...", patient_id)
        vision_result = vision_engine.predict_landmarks(file_path)
        if not vision_result or "landmarks" not in vision_result:
            logger.error("VisionEngine a retourné un résultat invalide ou vide.")
            raise ValueError("L'IA n'a détecté aucun point sur cette image.")

        pts = vision_result["landmarks"]
        logger.info("%s points détectés par le moteur %s", len(pts), vision_result["mode_inference"])
        points_dict = {p["id"]: (p["x"], p["y"]) for p in pts}

        from backend.services.calibration_service import calibration_service
        logger.info("Recherche d'une réglette candidate non autoritative...")
        calibration_candidate = calibration_service.detect_ruler_candidate(file_path)
        calibration_candidate_record = None
        if calibration_candidate is None:
            calibration_message = (
                "Aucune réglette fiable détectée automatiquement. "
                "Calibration manuelle requise pour les mesures millimétriques."
            )
        else:
            calibration_message = (
                "Réglette candidate détectée. Vérification praticien requise "
                "avant les mesures millimétriques."
            )
            calibration_candidate_record = {
                "schema_version": "CEPHALO_CALIBRATION_CANDIDATE_V1",
                **calibration_candidate,
                "verification_status": "UNVERIFIED",
            }

        mm_ratio = None
        is_calibrated = False

        patient = self.db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        age, sex = _patient_age_and_sex(patient)

        logger.info("Calcul des métriques géométriques sans échelle millimétrique vérifiée...")
        try:
            result = cephalo_engine.calculate_metrics(
                points_dict,
                custom_mm_ratio=mm_ratio,
                age=age,
                sex=sex,
            )
        except Exception as ce_err:
            logger.error("Échec du moteur géométrique: %s", ce_err)
            raise ValueError(f"Erreur lors du calcul des angles : {ce_err}")

        final_data_dict = _remove_autonomous_treatment(result.model_dump())
        final_data_dict["vision_metadata"] = {
            "mode_inference": vision_result["mode_inference"],
            "warning": vision_result.get("warning"),
            "processing_time_ms": vision_result["processing_time_ms"],
        }
        final_data_dict["calibration_status"] = "unverified"

        evidence_payload = build_cephalo_runtime_evidence_payload(
            patient_id=patient_id,
            image_record_id=db_path,
            result=result,
            landmarks=pts,
            inference_mode=vision_result.get("mode_inference"),
            is_calibrated=is_calibrated,
            calibration_data=None,
        )
        persisted_data = {**final_data_dict, EVIDENCE_GRAPH_KEY: evidence_payload}

        analysis = self.repo.create(
            patient_id,
            db_path,
            pts,
            persisted_data,
            mm_per_pixel=None,
            calibration_data=calibration_candidate_record,
        )

        return {
            "status": "success",
            "analysis_id": analysis.id,
            "results": final_data_dict,
            "ai_diagnostic": final_data_dict.get("ai_narrative", {}),
            "landmarks": pts,
            "is_calibrated": False,
            "mm_per_pixel": None,
            "calibration_candidate": calibration_candidate,
            "calibration_message": calibration_message,
        }

    def refine_analysis(
        self,
        analysis_id: int,
        landmarks: List[Any],
        clinical_data: Optional[schemas.ClinicalData] = None,
        ai_diagnostic: Optional[Dict] = None,
        mm_per_pixel: Optional[float] = None,
        mcnamara_projections: Optional[Dict] = None,
        clinician_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        pts_list = [p.model_dump() if hasattr(p, "model_dump") else p for p in landmarks]

        seen_ids: set[str] = set()
        points_dict: Dict[str, tuple[float, float]] = {}
        for point in pts_list:
            if not isinstance(point, dict):
                raise ValueError("Landmark invalide lors du raffinement.")
            landmark_id = point.get("id")
            if not isinstance(landmark_id, str) or not landmark_id.strip():
                raise ValueError("Landmark sans identifiant lors du raffinement.")
            if landmark_id in seen_ids:
                raise ValueError(f"Landmark dupliqué lors du raffinement: {landmark_id}")
            seen_ids.add(landmark_id)
            points_dict[landmark_id] = (point.get("x"), point.get("y"))

        existing = self.repo.get_by_id(analysis_id)
        if not existing:
            raise ValueError(f"Analyse {analysis_id} introuvable lors du raffinement.")

        previous_payload = None
        if isinstance(existing.angles_data, dict):
            candidate = existing.angles_data.get(EVIDENCE_GRAPH_KEY)
            if isinstance(candidate, dict):
                previous_payload = candidate

        if (
            previous_payload is not None
            and mm_per_pixel is not None
            and not _same_optional_ratio(mm_per_pixel, existing.mm_per_pixel)
        ):
            raise ValueError(
                "Le ratio mm/pixel d'une analyse tracée doit être modifié via l'endpoint de calibration."
            )

        effective_mm_per_pixel = mm_per_pixel if mm_per_pixel is not None else existing.mm_per_pixel
        age, sex = _patient_age_and_sex(existing.patient)

        result = cephalo_engine.calculate_metrics(
            points_dict,
            custom_mm_ratio=effective_mm_per_pixel,
            age=age,
            sex=sex,
            mcnamara_projections=mcnamara_projections,
        )

        if clinical_data:
            result.clinical_data = self._calculate_complex_ddm(result, clinical_data)

        final_data_dict = _remove_autonomous_treatment(result.model_dump())
        if ai_diagnostic:
            final_data_dict["ai_diagnostic"] = ai_diagnostic
        else:
            final_data_dict["ai_diagnostic"] = bilan_ortho_engine.generate_bilan(
                result,
                clinical_data if clinical_data else schemas.ClinicalData(),
                age=age,
                sex=sex,
            )

        final_data_dict["calibration_status"] = "verified" if existing.is_calibrated else "unverified"

        persisted_data = dict(final_data_dict)
        if previous_payload is not None:
            changed = landmark_submission_changed(previous_payload, pts_list)
            if changed:
                if clinician_id is None or not str(clinician_id).strip():
                    raise ValueError("Une correction de landmark tracée exige l'identité du praticien.")
                evidence_payload = rebuild_evidence_after_landmark_edit(
                    previous_payload=previous_payload,
                    patient_id=existing.patient_id,
                    image_record_id=existing.image_original_path,
                    result=result,
                    runtime_landmarks=pts_list,
                    clinician_id=str(clinician_id),
                    validated_at=dt.datetime.now(dt.timezone.utc),
                )
            else:
                evidence_payload = previous_payload
            persisted_data[EVIDENCE_GRAPH_KEY] = evidence_payload

        analysis = self.repo.update(
            analysis_id,
            pts_list,
            persisted_data,
            effective_mm_per_pixel,
        )
        if not analysis:
            raise ValueError(f"Analyse {analysis_id} introuvable lors du raffinement.")

        return {
            "status": "success",
            "analysis_id": analysis.id,
            "results": final_data_dict,
            "ai_diagnostic": final_data_dict["ai_diagnostic"],
            "landmarks": analysis.landmarks_data,
            "is_calibrated": analysis.is_calibrated,
            "mm_per_pixel": analysis.mm_per_pixel,
        }

    def _calculate_complex_ddm(
        self,
        _results: schemas.CephaloAnalysisResult,
        cd: schemas.ClinicalData,
    ) -> schemas.ClinicalData:
        data = cd.model_copy(deep=True)
        components = []

        for component in (data.ddm_maxillaire, data.ddm_mandibulaire):
            if component is None:
                continue
            component.calcul_ddm_reelle = None
            components.append(component.calcul_ddm)

        data.ddm_reelle = round(sum(components), 2) if components else None
        return data
