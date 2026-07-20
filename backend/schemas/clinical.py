from pydantic import BaseModel, ConfigDict, Field, field_validator
import datetime
from typing import Optional, Dict, List, Any, Tuple


# --- SLM & DIAGNOSTIC ---

class DiagnosticSLM(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diagnostic_squelettique: str
    analyse_moulages: str
    synthese_diagnostique: str
    strategie_therapeutique: str


# --- STRUCTURE DE MESURE CLINIQUE (MÉTHODE COM) ---

class MeasureData(BaseModel):
    valeur: Optional[float] = None
    norm_mean: float = 0.0
    norm_min: float = 0.0
    norm_max: float = 0.0
    plage_compensation: Optional[Tuple[float, float]] = None
    status: str = "N/A"
    interpretation: str = "Non calculé"
    z_score: float = 0.0


class DentalAnalysis(BaseModel):
    Surplomb: MeasureData = Field(default_factory=MeasureData)
    Recouvrement: MeasureData = Field(default_factory=MeasureData)
    IMPA: MeasureData = Field(default_factory=MeasureData)
    I_Francfort: MeasureData = Field(default_factory=MeasureData)
    Inter_Incisif: MeasureData = Field(default_factory=MeasureData)


class SkeletalAnalysis(BaseModel):
    Angle_de_Tweed: MeasureData = Field(default_factory=MeasureData)
    Decalage_A_B: MeasureData = Field(default_factory=MeasureData)
    Situation_A: MeasureData = Field(default_factory=MeasureData)
    Situation_B: MeasureData = Field(default_factory=MeasureData)
    Profondeur_Faciale: MeasureData = Field(default_factory=MeasureData)
    SNA: MeasureData = Field(default_factory=MeasureData)
    SNB: MeasureData = Field(default_factory=MeasureData)
    ANB: MeasureData = Field(default_factory=MeasureData)


class EstheticAnalysis(BaseModel):
    Ligne_E_Ls: MeasureData = Field(default_factory=MeasureData)
    Ligne_E_Li: MeasureData = Field(default_factory=MeasureData)
    Angle_Nasolabial: MeasureData = Field(default_factory=MeasureData)


class AnalysisMetrics(BaseModel):
    analyse_osseuse: SkeletalAnalysis = Field(default_factory=SkeletalAnalysis)
    analyse_dentaire: DentalAnalysis = Field(default_factory=DentalAnalysis)
    analyse_esthetique: EstheticAnalysis = Field(default_factory=EstheticAnalysis)


# --- ANALYSE CÉPHALOMÉTRIQUE ---

class CephaloAnalysisOut(BaseModel):
    id: int
    image_original_path: str
    angles_data: Optional[Any] = None
    landmarks_data: Optional[Any] = None
    ai_diagnostic: Optional[DiagnosticSLM] = None
    is_calibrated: bool = False
    mm_per_pixel: Optional[float] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --- CONSOLE BILAN PREMIUM (DDM & PLAN TRAITEMENT) ---

class LandmarkItem(BaseModel):
    id: str
    x: float
    y: float


class DDMComponent(BaseModel):
    espace_disponible: float
    espace_necessaire: float
    calcul_ddm: float
    calcul_ddm_reelle: Optional[float] = None


class ClinicalData(BaseModel):
    # DDM
    ddm_maxillaire: Optional[DDMComponent] = None
    ddm_mandibulaire: Optional[DDMComponent] = None
    ddm_reelle: Optional[float] = None
    
    # Moulages / Occlusal
    classe_molaire_droite: Optional[str] = None
    classe_molaire_gauche: Optional[str] = None
    classe_canine_droite: Optional[str] = None
    classe_canine_gauche: Optional[str] = None
    subdivision: Optional[bool] = None
    forme_arcade: Optional[str] = None
    
    # Patient Context
    age: Optional[int] = None
    cvm: Optional[str] = None
    sexe: Optional[str] = None
    denture_type: Optional[str] = None # TEMPORAIRE, MIXTE, PERMANENTE
    preference_technique: Optional[str] = None # DAMON, CLASSIC, ALIGNEURS
    
    # Output Final
    plan_traitement: Optional[str] = ""
    resume_moulages: Optional[str] = ""
    resume_diagnostic: Optional[str] = ""


class McNamaraProjections(BaseModel):
    N_prime: Optional[Tuple[float, float]] = None
    A_prime: Optional[Tuple[float, float]] = None
    B_prime: Optional[Tuple[float, float]] = None


class AnalysisMetadata(BaseModel):
    unit: str = "mm"
    pixel_ratio: Optional[float] = None
    type: str = "COM_Skeletal"
    cohort: str


class CephaloAnalysisResult(BaseModel):
    analysis_metadata: AnalysisMetadata
    metrics: AnalysisMetrics
    visual_debug: Dict[str, Any]
    t1_projection: Dict[str, Tuple[float, float]]
    t2_projection: Dict[str, Tuple[float, float]]
    ai_narrative: Optional[Dict[str, str]] = None
    ai_diagnostic: Optional[DiagnosticSLM] = None
    clinical_data: ClinicalData


class AnalysisUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    landmarks: List[LandmarkItem]
    mm_per_pixel: Optional[float] = None
    ai_diagnostic: Optional[Dict[str, str]] = None
    clinical_data: Optional[ClinicalData] = None
    mcnamara_projections: Optional[McNamaraProjections] = Field(default=None, alias="mcnmara_projections")


class CephaloViewModel(BaseModel):
    patient_nom: str
    patient_prenom: str
    patient_age: str
    patient_id: Optional[int] = None
    analysis: CephaloAnalysisResult
    cabinet_config: Optional[Dict[str, Any]] = None
    doctor_name: Optional[str] = None
    radio_image_path: Optional[str] = None
    date_generation: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%d/%m/%Y"))
    is_pre_bilan: bool = False
    validation_warnings: List[str] = Field(default_factory=list)


class CephaloPDFRequest(BaseModel):
    ai_diagnostic: Optional[Dict[str, str]] = None
    clinical_data: Optional[ClinicalData] = None
    archive: bool = False


# --- CALIBRATION CÉPHALOMÉTRIQUE ---

class CalibrationPoint(BaseModel):
    x: float
    y: float


class CalibrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p1: CalibrationPoint
    p2: CalibrationPoint
    distance_mm: float

    @field_validator('distance_mm')
    @classmethod
    def distance_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("La distance doit etre positive")
        if v > 100:
            raise ValueError("Distance trop grande pour une cephalometrie")
        return v


class CalibrationResponse(BaseModel):
    success: bool
    mm_per_pixel: float
    message: str


class VisionResult(BaseModel):
    analysis_id: int
    date_analyse: datetime.datetime
    points: Dict
    metrics: Dict
    status: str
    message: Optional[str] = None
