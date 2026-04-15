from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime, date
from typing import Optional, Dict, List, Literal, Any, Tuple, Union
from enum import Enum

# --- 1. SLM & DIAGNOSTIC INTELLIGENT ---

class DiagnosticSLM(BaseModel):
    """Objet structuré généré par le Small Language Model (SLM)."""
    squelettique: str
    dentaire: str
    traitement: str

# --- 2. STRUCTURE DE MESURE CLINIQUE (MÉTHODE COM) ---

class MeasureData(BaseModel):
    """Encapsule une mesure avec ses normes, compensations et son statut clinique."""
    valeur: Optional[float]
    norm_mean: float
    norm_min: float
    norm_max: float
    plage_compensation: Optional[Tuple[float, float]] = None
    status: str
    interpretation: str
    z_score: float

class DentalAnalysis(BaseModel):
    Surplomb: MeasureData
    Recouvrement: MeasureData
    IMPA: MeasureData
    I_Francfort: MeasureData
    Inter_Incisif: MeasureData

class SkeletalAnalysis(BaseModel):
    Angle_de_Tweed: MeasureData
    Decalage_A_B: MeasureData
    Situation_A: MeasureData
    Situation_B: MeasureData
    Profondeur_Faciale: MeasureData

class AnalysisMetrics(BaseModel):
    analyse_dentaire: DentalAnalysis
    analyse_osseuse: SkeletalAnalysis

# --- 3. CONFIGURATION CABINET ---

class CabinetConfigOut(BaseModel):
    nom_complet: str
    specialites: Optional[str] = None
    adresse_complete: Optional[str] = None
    telephone_fixe: Optional[str] = None
    telephone_mobile: Optional[str] = None
    identifiants_legaux: Optional[Dict[str, str]] = None
    model_config = ConfigDict(from_attributes=True)

# --- 4. DOSSIER CLINIQUE ---

class DossierOut(BaseModel):
    id: int
    is_ortho_active: bool
    note_honnetete: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- 5. SCHÉMAS PATIENTS ---

class PatientBase(BaseModel):
    numero_dossier: Optional[str] = None  # Optionnel à la création, auto-généré si vide
    nom: str
    prenom: str
    date_naissance: datetime
    sexe: Literal["M", "F"]
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None
    

    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    numero_dossier: str  # Rendu obligatoire en sortie
    created_at: datetime
    dossier: Optional[DossierOut] = None
    model_config = ConfigDict(from_attributes=True)

# --- 6. SCHÉMA ANALYSE CÉPHALOMÉTRIQUE ---

class CephaloAnalysisOut(BaseModel):
    id: int
    image_original_path: str
    angles_data: Optional[Dict] = None
    landmarks_data: Optional[Dict] = None
    ai_diagnostic: Optional[DiagnosticSLM] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==============================================================================
# --- 7. MODÈLES : DOCUMENT FACTORY ---
# ==============================================================================

class MedicationItem(BaseModel):
    nom: str
    dosage: str
    forme: str = "Sachets"
    posologie: str

class OrdonnanceData(BaseModel):
    medications: List[MedicationItem]
    doc_date: date
    age: Optional[int] = None
    gender: Optional[str] = None

class CertificatData(BaseModel):
    reason: str
    days: int
    start_date: date
    is_work_stop: bool = False
    age: Optional[int] = None
    gender: Optional[str] = None

class ToothTreatmentInfo(BaseModel):
    code: str
    name: str
    price: float

class ToothData(BaseModel):
    """Données d'une dent selon système FDI (11-18, 21-28, 31-38, 41-48)"""
    tooth_number: int  # FDI: 11-18, 21-28, 31-38, 41-48
    treatments: List[ToothTreatmentInfo]
    surfaces: List[str] = []
    notes: Optional[str] = None

class DevisItem(BaseModel):
    acte: str
    dent: str
    dents: List[Union[int, str]] = []  # Liste des numéros de dents concernées
    prix_unitaire: float

class DevisData(BaseModel):
    items: List[DevisItem]
    doc_date: date
    teeth_data: List[ToothData] = []  # Données détaillées de l'odontogramme
    age: Optional[int] = None
    gender: Optional[str] = None

class PaymentItem(BaseModel):
    date: date
    acte: str
    dent: str = "-"
    dents: List[Union[int, str]] = []  # Liste des numéros de dents concernées
    montant: float
    mode_reglement: str = "Espèces"

class HonorairesData(BaseModel):
    payments: List[PaymentItem]
    doc_date: date
    teeth_data: List[ToothData] = []  # Données détaillées de l'odontogramme
    age: Optional[int] = None
    gender: Optional[str] = None

class LibreData(BaseModel):
    titre: str = Field(default='DOCUMENT MÉDICAL', alias='title')
    texte: str = Field(default='', alias='content')
    doc_date: date
    age: Optional[int] = None
    gender: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)

class DocumentRequest(BaseModel):
    type: Literal["ordonnance", "certificat", "devis", "note", "honoraires", "libre"]
    patient_id: int
    data: Dict


# ==============================================================================
# --- 8. SCHÉMAS : SMART ORDONNANCE (PHASE 2) ---
# ==============================================================================

class MedicationOut(BaseModel):
    id: int
    nom: str
    dosage: Optional[str] = None
    forme: Optional[str] = None
    usage_count: int
    model_config = ConfigDict(from_attributes=True)

class ClinicalCategoryOut(BaseModel):
    id: int
    label: str
    model_config = ConfigDict(from_attributes=True)

class ClinicalProtocolOut(BaseModel):
    id: int
    category_id: int
    variant_name: str
    medications_json: Any
    model_config = ConfigDict(from_attributes=True)

class PrescriptionLearnRequest(BaseModel):
    medications: List[MedicationItem]


# ==============================================================================
# --- 9. SCHÉMAS : CATALOGUE DES ACTES ---
# ==============================================================================

class ClinicalActCatalogBase(BaseModel):
    name: str
    base_price: float

class ClinicalActCatalogOut(ClinicalActCatalogBase):
    id: int
    usage_count: int
    model_config = ConfigDict(from_attributes=True)

class ActLearnRequestItem(BaseModel):
    name: str
    price_applied: float

class ActLearnRequest(BaseModel):
    acts: List[ActLearnRequestItem]

# ==============================================================================
# --- 10. SCHÉMAS : CONSOLE BILAN PREMIUM V4 (DDM & PLAN TRAITEMENT) ---
# ==============================================================================

class LandmarkItem(BaseModel):
    id: str
    x: float
    y: float

class DDMComponent(BaseModel):
    """ED (Espace Disponible) et EN (Espace Nécessaire)."""
    espace_disponible: float
    espace_necessaire: float
    calcul_ddm: float

class ClinicalData(BaseModel):
    """Conteneur unifié pour les mesures de moulages et la synthèse clinique."""
    ddm_maxillaire: Optional[DDMComponent] = None
    ddm_mandibulaire: Optional[DDMComponent] = None
    ddm_reelle: Optional[float] = None
    plan_traitement: Optional[str] = ""

class McNamaraProjections(BaseModel):
    """Projections des points A, B, N sur le plan de Francfort (analyse McNamara)."""
    N_prime: Optional[Tuple[float, float]] = None
    A_prime: Optional[Tuple[float, float]] = None
    B_prime: Optional[Tuple[float, float]] = None

class AnalysisUpdate(BaseModel):
    landmarks: List[LandmarkItem]
    mm_per_pixel: Optional[float] = None
    ai_diagnostic: Optional[Dict[str, str]] = None
    clinical_data: Optional[ClinicalData] = None
    mcnmara_projections: Optional[McNamaraProjections] = None  # Projections A', B', N'

class CephaloPDFRequest(BaseModel):
    """Payload pour forcer l'impression du Bilan Complet avec les modifications Live."""
    ai_diagnostic: Optional[Dict[str, str]] = None
    clinical_data: Optional[ClinicalData] = None
    archive: bool = False


# ==============================================================================
# --- SCHÉMAS : CALIBRATION CÉPHALOMÉTRIQUE ---
# ==============================================================================

class CalibrationPoint(BaseModel):
    x: float
    y: float

class CalibrationRequest(BaseModel):
    """Payload pour calibrer l'échelle mm/pixel."""
    p1: CalibrationPoint  # Premier point sur la radio
    p2: CalibrationPoint  # Deuxième point sur la radio
    distance_mm: float    # Distance réelle en mm entre ces deux points
    
    @field_validator('distance_mm')
    @classmethod
    def distance_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("La distance doit être positive")
        if v > 100:  # Max 10cm pour une radio céphalo
            raise ValueError("Distance trop grande pour une céphalométrie")
        return v

class CalibrationResponse(BaseModel):
    """Réponse après calibration."""
    success: bool
    mm_per_pixel: float
    message: str

# ==============================================================================
# --- 11. SCHÉMAS : ERP & IA PHARMACOLOGIQUE ---
# ==============================================================================

class AIPrescriptionRequest(BaseModel):
    acte: str
    age: Optional[int] = None

class BIStatsOut(BaseModel):
    ca_mensuel: float
    ca_annuel: float
    repartition_actes: Dict[str, float]
    evolution_mensuelle: List[Dict[str, Any]]

# ==============================================================================
# --- 12. SCHEMAS : ARCHIVAGE DOCUMENTAIRE VERSIONNE ---
# ==============================================================================

class DocumentType(str, Enum):
    RAPPORT_CEPHALO = "RAPPORT_CEPHALO"
    ORDONNANCE = "ORDONNANCE"
    CERTIFICAT = "CERTIFICAT"
    DEVIS = "DEVIS"
    NOTE_HONORAIRES = "NOTE_HONORAIRES"
    LETTRE_MEDICALE = "LETTRE_MEDICALE"
    DOCUMENT_LIBRE = "DOCUMENT_LIBRE"
    PHOTO_CLINIQUE = "PHOTO_CLINIQUE"
    RADIOGRAPHIE = "RADIOGRAPHIE"
    MOULAGE = "MOULAGE"
    AUTRE = "AUTRE"

class DocumentStatus(str, Enum):
    ACTIF = "ACTIF"
    SUPPRIME = "SUPPRIME"
    ARCHIVE = "ARCHIVE"

class ConflictResolution(str, Enum):
    KEEP_BOTH = "KEEP_BOTH"
    OVERWRITE = "OVERWRITE"
    CANCEL = "CANCEL"
    CREATE_VERSION = "CREATE_VERSION"

class DocumentArchiveBase(BaseModel):
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []

class DocumentArchiveCreate(DocumentArchiveBase):
    patient_id: int
    analysis_id: Optional[int] = None
    clinical_data: Optional[Dict] = None

class DocumentVersionInfo(BaseModel):
    version_number: int
    created_at: datetime
    file_size: int
    is_latest: bool

class DocumentArchiveOut(DocumentArchiveBase):
    id: int
    patient_id: int
    filename: str
    original_filename: str
    file_size: int
    file_hash: str
    document_group_id: str
    version_number: int
    is_latest_version: bool
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    download_url: str
    all_versions: List[DocumentVersionInfo] = []
    
    class Config:
        from_attributes = True

class DocumentConflictCheck(BaseModel):
    has_conflict: bool
    existing_document: Optional[DocumentArchiveOut] = None
    conflict_reason: Optional[str] = None  # "same_hash", "same_name_same_day", "version_exists"
    suggested_action: Optional[ConflictResolution] = None

class DocumentArchiveRequest(BaseModel):
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    check_conflicts: bool = True
    on_conflict: ConflictResolution = ConflictResolution.CREATE_VERSION

class DocumentArchiveResponse(BaseModel):
    success: bool
    message: str
    document: Optional[DocumentArchiveOut] = None
    conflict_info: Optional[DocumentConflictCheck] = None
    requires_action: bool = False

class DocumentListParams(BaseModel):
    patient_id: Optional[int] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = DocumentStatus.ACTIF
    tags: List[str] = []
    search_query: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20

class DocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    documents: List[DocumentArchiveOut]

class DocumentTrashResponse(BaseModel):
    message: str
    document_id: int
    deleted_at: datetime
    permanent_delete_at: datetime

class DocumentRestoreResponse(BaseModel):
    message: str
    document_id: int
    restored_at: datetime

class DocumentBatchDeleteRequest(BaseModel):
    document_ids: List[int]
    permanent: bool = False

class DocumentBatchResponse(BaseModel):
    success: List[int]
    failed: List[Dict[int, str]]  # id -> error message

class DocumentShareLink(BaseModel):
    token: str
    expires_at: datetime
    download_url: str
    max_downloads: int = 5

class DocumentPreviewResponse(BaseModel):
    document_id: int
    preview_url: str
    thumbnail_url: Optional[str] = None
    file_type: str
    can_preview: bool



# ==============================================================================
# SCHÉMAS MULTI-TENANT (Phase SaaS)
# ==============================================================================

class StyleKey(str, Enum):
    CLASSIQUE = "classique"
    MODERNE = "moderne"
    MINIMALISTE = "minimaliste"
    MEDICAL = "medical"
    PREMIUM = "premium"
    SANINOVA = "saninova"


# --- Design Config (Validation Stricte) ---

class FontConfig(BaseModel):
    fr: str = Field(default="Helvetica", max_length=50)
    ar: str = Field(default="Amiri", max_length=50)
    fallback: str = Field(default="Arial", max_length=50)


class ColorConfig(BaseModel):
    primary: str = Field(default="#003380", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: str = Field(default="#666666", pattern=r"^#[0-9A-Fa-f]{6}$")
    background: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: str = Field(default="#0055AA", pattern=r"^#[0-9A-Fa-f]{6}$")


class MarginConfig(BaseModel):
    top: float = Field(default=3.6, ge=1.0, le=5.0)
    right: float = Field(default=1.5, ge=0.5, le=3.0)
    bottom: float = Field(default=3.2, ge=1.0, le=5.0)
    left: float = Field(default=1.5, ge=0.5, le=3.0)


class LayoutConfig(BaseModel):
    page_size: Literal["A4", "A5"] = Field(default="A5")
    margins: MarginConfig = Field(default_factory=MarginConfig)
    header_height: float = Field(default=4.0, ge=2.0, le=6.0)
    footer_height: float = Field(default=2.5, ge=1.0, le=4.0)


class WatermarkConfig(BaseModel):
    enabled: bool = Field(default=True)
    size_cm: float = Field(default=7.0, ge=3.0, le=10.0)
    opacity: float = Field(default=0.10, ge=0.0, le=1.0)
    position: Literal["center", "top-left", "top-right", "bottom-left", "bottom-right"] = Field(default="center")


class HeaderConfig(BaseModel):
    bilingual: bool = Field(default=True)
    logo_in_header: bool = Field(default=True)
    logo_header_size_cm: float = Field(default=2.5, ge=1.0, le=5.0)
    show_lines: bool = Field(default=True)


class BorderConfig(BaseModel):
    header_line: bool = Field(default=True)
    header_line_style: Literal["single", "double", "none"] = Field(default="single")
    header_line_color: str = Field(default="#003380", pattern=r"^#[0-9A-Fa-f]{6}$")
    content_border: bool = Field(default=False)
    content_border_radius: int = Field(default=0, ge=0, le=20)


class TypographyConfig(BaseModel):
    title_size: int = Field(default=18, ge=12, le=32)
    title_bold: bool = Field(default=True)
    title_underline: bool = Field(default=True)
    title_align: Literal["left", "center", "right"] = Field(default="center")
    body_size: int = Field(default=11, ge=8, le=16)
    body_line_height: float = Field(default=1.6, ge=1.0, le=2.5)


class SpacingConfig(BaseModel):
    paragraph_gap_cm: float = Field(default=1.0, ge=0.0, le=2.0)
    section_gap_cm: float = Field(default=0.8, ge=0.0, le=2.0)


class LetterheadConfig(BaseModel):
    """Configuration du papier en-tête (Letterhead Mode)."""
    enabled: bool = Field(default=False)
    image_url: Optional[str] = Field(default=None, description="URL de l'image A4 uploadée")
    hide_default_header: bool = Field(default=True, description="Masquer le HTML du header")
    hide_default_footer: bool = Field(default=True, description="Masquer le HTML du footer")


class DesignConfig(BaseModel):
    """Configuration stylistique complète. Validation stricte."""
    model_config = ConfigDict(extra="forbid")
    
    fonts: FontConfig = Field(default_factory=FontConfig)
    colors: ColorConfig = Field(default_factory=ColorConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    watermark: WatermarkConfig = Field(default_factory=WatermarkConfig)
    header: HeaderConfig = Field(default_factory=HeaderConfig)
    borders: BorderConfig = Field(default_factory=BorderConfig)
    typography: TypographyConfig = Field(default_factory=TypographyConfig)
    spacing: SpacingConfig = Field(default_factory=SpacingConfig)
    letterhead: LetterheadConfig = Field(default_factory=LetterheadConfig)


# --- Cabinet Config ---

class CabinetConfigBase(BaseModel):
    header_lines_fr: List[str] = Field(default_factory=list, max_length=6)
    header_lines_ar: List[str] = Field(default_factory=list, max_length=6)
    footer_address: str = Field(default="", max_length=500)
    footer_phones: str = Field(default="", max_length=255)
    primary_color: str = Field(default="#003380", pattern=r"^#[0-9A-Fa-f]{6}$")
    font_fr: str = Field(default="Helvetica", max_length=50)
    font_ar: str = Field(default="Amiri", max_length=50)
    watermark_enabled: bool = Field(default=True)
    watermark_opacity: float = Field(default=0.10, ge=0.0, le=1.0)


class CabinetConfigCreate(CabinetConfigBase):
    pass


class CabinetConfigUpdate(CabinetConfigBase):
    pass


class CabinetConfigOut(CabinetConfigBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    public_id: str
    owner_id: int
    logo_path: Optional[str] = None
    letterhead_path: Optional[str] = None
    is_initialized: bool
    created_at: datetime
    updated_at: datetime


class CabinetInitStatus(BaseModel):
    is_initialized: bool
    needs_setup: bool


# --- Document Templates ---

class DocumentTemplateBase(BaseModel):
    type: DocumentType
    style_key: StyleKey
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class DocumentTemplateCreate(DocumentTemplateBase):
    body_html: str = Field(min_length=10)
    design_config: DesignConfig = Field(default_factory=DesignConfig)
    is_system: bool = Field(default=False)
    is_default: bool = Field(default=False)


class DocumentTemplateUpdate(BaseModel):
    """Mise à jour utilisateur - body_html EXCLU (sécurité SSTI)."""
    model_config = ConfigDict(extra="forbid")
    
    name: Optional[str] = Field(default=None, max_length=100)
    design_config: Optional[DesignConfig] = None
    is_default: Optional[bool] = None


class DocumentTemplateOut(DocumentTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: Optional[int]
    is_system: bool
    is_default: bool
    design_config: DesignConfig
    body_html: Optional[str] = Field(default=None)
    created_at: datetime
    updated_at: datetime


class DocumentTemplateList(BaseModel):
    id: str
    type: DocumentType
    style_key: StyleKey
    name: str
    is_default: bool
    description: Optional[str]


class TemplatePreviewRequest(BaseModel):
    template_id: str
    sample_data: Dict[str, Any] = Field(default_factory=lambda: {
        "patient": {"nom": "DUPONT", "prenom": "Marie", "age": 35},
        "date": "02/03/2026",
        "titre": "ORDONNANCE"
    })
