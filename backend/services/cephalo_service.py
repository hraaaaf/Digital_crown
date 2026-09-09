from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.repositories.cephalo_repository import CephaloRepository
from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine
from backend.services.vision_service import vision_engine
from backend.services.bilan_ortho_engine import bilan_ortho_engine
from backend import schemas, models
import logging

logger = logging.getLogger(__name__)


def _calculate_age(birth_date) -> Optional[int]:
    if birth_date is None:
        return None
    from datetime import date
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _patient_age_and_sex(patient: Optional["models.Patient"]) -> Tuple[Optional[int], Optional[str]]:
    """Read patient context exactly as stored; never substitute age or sex."""
    if patient is None:
        return None, None
    return _calculate_age(patient.date_naissance), patient.sexe


def _remove_autonomous_treatment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Defense-in-depth treatment boundary for serialized cephalo output."""
    narrative = payload.get("ai_narrative")
    if isinstance(narrative, dict):
        narrative.pop("strategie_therapeutique", None)
    return payload


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
        logger.info("Tentative de calibration automatique...")
        auto_ratio = calibration_service.detect_mm_per_pixel(file_path)
        if auto_ratio is None:
            logger.warning("Auto-calibration unavailable; linear millimeter metrics will not be calculated.")
        mm_ratio = auto_ratio
        logger.info("Ratio retenu : %s mm/px (Auto: %s)", mm_ratio, auto_ratio is not None)

        patient = self.db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        age, sex = _patient_age_and_sex(patient)

        logger.info("Calcul des métriques géométriques...")
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
        final_data_dict["calibration_status"] = "verified" if auto_ratio else "unverified"

        analysis = self.repo.create(
            patient_id,
            db_path,
            pts,
            final_data_dict,
            mm_per_pixel=mm_ratio,
        )
        if auto_ratio:
            analysis.is_calibrated = True
            self.db.commit()

        return {
            "status": "success",
            "analysis_id": analysis.id,
            "results": final_data_dict,
            "ai_diagnostic": final_data_dict.get("ai_narrative", {}),
            "landmarks": pts,
            "is_calibrated": analysis.is_calibrated,
            "mm_per_pixel": analysis.mm_per_pixel,
        }

    def refine_analysis(
        self,
        analysis_id: int,
        landmarks: List[Any],
        clinical_data: Optional[schemas.ClinicalData] = None,
        ai_diagnostic: Optional[Dict] = None,
        mm_per_pixel: Optional[float] = None,
        mcnamara_projections: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        pts_list = [p.model_dump() if hasattr(p, "model_dump") else p for p in landmarks]
        points_dict = {p["id"]: (p["x"], p["y"]) for p in pts_list}

        existing = self.repo.get_by_id(analysis_id)
        if not existing:
            raise ValueError(f"Analyse {analysis_id} introuvable lors du raffinement.")

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
            # Explicit practitioner-authored content is preserved unchanged.
            final_data_dict["ai_diagnostic"] = ai_diagnostic
        else:
            final_data_dict["ai_diagnostic"] = bilan_ortho_engine.generate_bilan(
                result,
                clinical_data if clinical_data else schemas.ClinicalData(),
                age=age,
                sex=sex,
            )

        final_data_dict["calibration_status"] = "verified" if existing.is_calibrated else "unverified"

        analysis = self.repo.update(
            analysis_id,
            pts_list,
            final_data_dict,
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
        """Preserve practitioner-supplied clinical space discrepancy fail-closed.

        The former implementation converted IMPA deviation with a fixed universal
        angular-to-space factor and called the result "DDM réelle". That
        patient-specific correction is not validated by the Scientific Core and
        is therefore retired. No cephalometric angle changes clinical space here.
        """
        data = cd.model_copy(deep=True)
        components = []

        for component in (data.ddm_maxillaire, data.ddm_mandibulaire):
            if component is None:
                continue
            # calcul_ddm is the explicit clinical value received from the caller.
            # Do not reconstruct it from placeholder espace_* fields and do not
            # manufacture a cephalometric correction.
            component.calcul_ddm_reelle = None
            components.append(component.calcul_ddm)

        data.ddm_reelle = round(sum(components), 2) if components else None
        return data
