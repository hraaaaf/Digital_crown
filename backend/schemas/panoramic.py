from pydantic import BaseModel, ConfigDict, Field, field_validator
import datetime
from typing import Optional, List, Literal, Dict


# --- SCHÉMA ANALYSE PANORAMIQUE v1 (DENTEX) ---
# Note: BoundingBox/Finding/ToothObject are redefined below by the OPG v2 schema.

class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float


class Finding(BaseModel):
    label: str
    confidence: float
    bbox: Optional[BoundingBox] = None


class ToothObject(BaseModel):
    fdi_number: Optional[int] = Field(None, description="Numérotation FDI (11-48)")
    bbox: BoundingBox
    findings: List[Finding] = Field(default_factory=list)


class FullAnalysis(BaseModel):
    teeth: List[ToothObject] = Field(default_factory=list)
    general_findings: List[Finding] = Field(default_factory=list)


class PanoramicAnalysisBase(BaseModel):
    image_path: str
    detections_data: FullAnalysis = Field(default_factory=FullAnalysis)
    report_narrative: Optional[str] = None


class PanoramicAnalysisCreate(PanoramicAnalysisBase):
    patient_id: int


class PanoramicAnalysisOut(PanoramicAnalysisBase):
    id: int
    patient_id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# --- ANALYSE PANORAMIQUE v2 (OPG / LOKI-SILVRES) ---
# These redefine BoundingBox, ToothObject, Finding with OPG-specific fields.

class BoundingBox(BaseModel):  # noqa: F811
    """Coordonnées de la boîte englobante en pixels [x, y, w, h]."""
    x: float
    y: float
    w: float
    h: float
    confidence: float


class ToothObject(BaseModel):  # noqa: F811
    """Représentation d'une dent individuelle selon la nomenclature FDI."""
    fdi: int
    bbox: BoundingBox
    label: str = "tooth"

    @field_validator('fdi')
    @classmethod
    def validate_fdi(cls, v):
        valid_fdis = [q * 10 + d for q in [1, 2, 3, 4] for d in range(1, 9)]
        valid_fdis += [q * 10 + d for q in [5, 6, 7, 8] for d in range(1, 6)]
        if v not in valid_fdis:
            raise ValueError(f"Numéro FDI invalide : {v}")
        return v


class Finding(BaseModel):  # noqa: F811
    """Pathologie ou objet clinique détecté (Carie, Implant, Lésion, etc.)."""
    label: str
    fdi: Optional[int] = None
    bbox: BoundingBox
    clinical_term: str
    severity: Literal["low", "medium", "high", "none"] = "none"


class PanoramicAnalysis(BaseModel):
    """Résultat complet d'une analyse radiographique panoramique."""
    model_config = ConfigDict(protected_namespaces=())
    image_url: str
    teeth: List[ToothObject]
    findings: List[Finding]
    summary_markdown: Optional[str] = None
    processing_time_ms: float
    model_version: str = "Loki-Silvres-v1.0"


class PanoramicVisualAnnotation(BaseModel):
    id: int
    x: float
    y: float
    text: str


class PanoramicReportRequest(BaseModel):
    """Demande de génération de rapport basé sur les annotations manuelles."""
    analysis_id: int
    manual_anomalies: Dict[int, List[str]]
    rejected_detections: Optional[List[int]] = Field(default_factory=list)
    visual_annotations: Optional[List[PanoramicVisualAnnotation]] = Field(default_factory=list)

