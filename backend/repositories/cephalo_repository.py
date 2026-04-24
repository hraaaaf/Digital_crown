from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend import models
import logging

logger = logging.getLogger(__name__)

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

    def create(self, patient_id: int, image_path: str, landmarks: List[Dict], results: Dict) -> models.CephaloAnalysis:
        """Crée une nouvelle analyse en base de données."""
        db_analysis = models.CephaloAnalysis(
            patient_id=patient_id,
            image_original_path=image_path,
            landmarks_data=landmarks,
            angles_data=results
        )
        self.db.add(db_analysis)
        self.db.commit()
        self.db.refresh(db_analysis)
        return db_analysis

    def update(self, analysis_id: int, landmarks: List[Dict], results: Dict, mm_per_pixel: Optional[float] = None) -> Optional[models.CephaloAnalysis]:
        """Met à jour les données d'une analyse existante."""
        db_analysis = self.get_by_id(analysis_id)
        if not db_analysis:
            return None
            
        db_analysis.landmarks_data = landmarks
        db_analysis.angles_data = results
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
