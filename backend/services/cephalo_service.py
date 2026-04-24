from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.repositories.cephalo_repository import CephaloRepository
from backend.services.cephalo_engine import cephalo_engine
from backend.services.vision_service import vision_engine
from backend.services.ai_advisor import ai_advisor
from backend import schemas
import logging

logger = logging.getLogger(__name__)

class CephaloService:
    """
    Orchestrateur de la logique Céphalométrique.
    Centralise Vision, Géométrie, DDM et Diagnostic IA.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = CephaloRepository(db)

    def process_new_radio(self, patient_id: int, file_path: str, db_path: str) -> Dict[str, Any]:
        """
        Exécute la pipeline complète pour une nouvelle radio.
        Vision -> Géométrie -> Initialisation Bilan -> Persistance.
        """
        # 1. Inférence Vision (Points anatomiques)
        vision_result = vision_engine.predict_landmarks(file_path)
        pts = vision_result["landmarks"]
        points_dict = {p['id']: (p['x'], p['y']) for p in pts}

        # 2. Calibration Automatique 2.0 (Phase 4)
        from backend.services.calibration_service import calibration_service
        auto_ratio = calibration_service.detect_mm_per_pixel(file_path)
        mm_ratio = auto_ratio if auto_ratio else 0.1 
        
        # 3. Calcul des métriques Géométriques -> CephaloAnalysisResult
        result = cephalo_engine.calculate_metrics(points_dict, custom_mm_ratio=mm_ratio)
        
        final_data_dict = result.model_dump()
        final_data_dict["vision_metadata"] = {
            "mode_inference": vision_result["mode_inference"],
            "warning": vision_result.get("warning"),
            "processing_time_ms": vision_result["processing_time_ms"]
        }

        # 4. Persistance via Repository
        analysis = self.repo.create(patient_id, file_path, pts, final_data_dict, mm_per_pixel=mm_ratio)
        
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
            "mm_per_pixel": analysis.mm_per_pixel
        }

    def refine_analysis(self, 
                        analysis_id: int, 
                        landmarks: List[Any], 
                        clinical_data: Optional[schemas.ClinicalData] = None, 
                        ai_diagnostic: Optional[Dict] = None, 
                        mm_per_pixel: Optional[float] = None, 
                        mcnamara_projections: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Recalcule et met à jour une analyse existante.
        Recalcul Géométrique -> Calcul DDM -> Diagnostic IA -> Persistance.
        """
        # Conversion des points pour le moteur géométrique
        pts_list = [p.model_dump() if hasattr(p, 'model_dump') else p for p in landmarks]
        points_dict = {p['id']: (p['x'], p['y']) for p in pts_list}
        
        # 1. Recalcul Géométrique -> CephaloAnalysisResult
        result = cephalo_engine.calculate_metrics(
            points_dict, 
            custom_mm_ratio=mm_per_pixel, 
            mcnamara_projections=mcnamara_projections
        )

        # 2. Logique métier DDM Réelle
        if clinical_data:
            result.clinical_data = self._calculate_complex_ddm(result, clinical_data)
        
        # 3. Gestion du Diagnostic IA
        final_data_dict = result.model_dump()
        if ai_diagnostic:
            final_data_dict["ai_diagnostic"] = ai_diagnostic
        else:
            final_data_dict["ai_diagnostic"] = ai_advisor.generate_diagnostic(result)

        # 4. Mise à jour via Repository
        analysis = self.repo.update(analysis_id, pts_list, final_data_dict, mm_per_pixel)
        
        if not analysis:
            raise ValueError(f"Analyse {analysis_id} introuvable lors du raffinement.")

        return {
            "status": "success",
            "analysis_id": analysis.id,
            "results": final_data_dict,
            "ai_diagnostic": final_data_dict["ai_diagnostic"],
            "landmarks": analysis.landmarks_data,
            "is_calibrated": analysis.is_calibrated,
            "mm_per_pixel": analysis.mm_per_pixel
        }

    def _calculate_complex_ddm(self, results: schemas.CephaloAnalysisResult, cd: schemas.ClinicalData) -> schemas.ClinicalData:
        """
        Logique métier DDM Réelle (Master Logic).
        Calcule l'impact de l'inclinaison incisive (IMPA) sur l'encombrement dentaire.
        """
        # Extraction de l'IMPA depuis les nouveaux résultats typés
        impa = results.metrics.analyse_dentaire.IMPA.valeur
        
        # Règle COM : 2.5° d'inclinaison = 1mm de place gagnée/perdue
        ddm_cephalo = (impa - 90) / 2.5 if impa else 0
        
        # On travaille sur une copie du modèle pour éviter les mutations imprévues
        data = cd.model_copy(deep=True)
        
        # Recalcul Maxillaire
        if data.ddm_maxillaire:
            ddm_max_clinique = data.ddm_maxillaire.espace_disponible - data.ddm_maxillaire.espace_necessaire
            data.ddm_maxillaire.calcul_ddm_reelle = round(ddm_max_clinique + ddm_cephalo, 2)
        
        # Recalcul Mandibulaire
        if data.ddm_mandibulaire:
            ddm_mand_clinique = data.ddm_mandibulaire.espace_disponible - data.ddm_mandibulaire.espace_necessaire
            data.ddm_mandibulaire.calcul_ddm_reelle = round(ddm_mand_clinique + ddm_cephalo, 2)
            
        # DDM Réelle Totale
        total_reelle = 0
        if data.ddm_maxillaire and data.ddm_maxillaire.calcul_ddm_reelle:
            total_reelle += data.ddm_maxillaire.calcul_ddm_reelle
        if data.ddm_mandibulaire and data.ddm_mandibulaire.calcul_ddm_reelle:
            total_reelle += data.ddm_mandibulaire.calcul_ddm_reelle
            
        data.ddm_reelle = round(total_reelle, 2)
        return data
