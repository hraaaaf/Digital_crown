from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import datetime
from typing import Optional, Dict, List, Literal, Any, Tuple, Union
from enum import Enum

class QRCodeType(str, Enum):
    NONE = "NONE"
    VALIDATION = "VALIDATION"
    VCARD = "VCARD"
    WEBSITE = "WEBSITE"
    INSTAGRAM = "INSTAGRAM"
    PAYMENT = "PAYMENT"
    WHATSAPP = "WHATSAPP"
    LOCATION = "LOCATION"

# --- 1. SLM & DIAGNOSTIC INTELLIGENT ---

class DiagnosticSLM(BaseModel):
    """Objet structuré généré par le Small Language Model (SLM)."""
    squelettique: str
    dentaire: str
    traitement: str

# --- 2. STRUCTURE DE MESURE CLINIQUE (MÉTHODE COM) ---

class MeasureData(BaseModel):
    """Encapsule une mesure avec ses normes, compensations et son statut clinique."""
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

class EstheticAnalysis(BaseModel):
    Ligne_E_Ls: MeasureData = Field(default_factory=MeasureData)
    Ligne_E_Li: MeasureData = Field(default_factory=MeasureData)

class AnalysisMetrics(BaseModel):
    analyse_osseuse: SkeletalAnalysis = Field(default_factory=SkeletalAnalysis)
    analyse_dentaire: DentalAnalysis = Field(default_factory=DentalAnalysis)
    analyse_esthetique: EstheticAnalysis = Field(default_factory=EstheticAnalysis)

# --- 3. CONFIGURATION CABINET ---

class PraticienProfileOut(BaseModel):
    nom_complet: str
    nom: Optional[str] = None # Alias
    specialites: Optional[str] = None
    adresse_complete: Optional[str] = None
    adresse: Optional[str] = None # Alias
    telephone_fixe: Optional[str] = None
    telephone: Optional[str] = None # Alias
    telephone_mobile: Optional[str] = None
    identifiants_legaux: Optional[Dict[str, str]] = None
    inpe: Optional[str] = None # Alias
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
    date_naissance: Union[datetime.datetime, datetime.date, str]
    sexe: str # "M" ou "F", mais tolérant à "Homme"/"Femme"
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    assurance: Optional[str] = "AUCUNE"
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None
    
    @field_validator('sexe', mode='before')
    @classmethod
    def normalize_sexe(cls, v):
        if not v: return "M"
        v_upper = str(v).upper()
        if "HOMME" in v_upper or "MASC" in v_upper or v_upper.startswith("M"):
            return "M"
        if "FEMME" in v_upper or "GARC" in v_upper or v_upper.startswith("F"): # GARC is actually for Garçon but wait...
             # Actually "GARCON" is Male. "FILLE" is Female.
             return "M" if "GARC" in v_upper else "F"
        return "F" if "F" in v_upper else "M"
    

    @field_validator('date_naissance', mode='before')
    @classmethod
    def parse_date_naissance(cls, v):
        if isinstance(v, datetime.datetime):
            return v
        if isinstance(v, datetime.date):
            return datetime.datetime.combine(v, datetime.time.min)
        if isinstance(v, str):
            try:
                # Tentative ISO
                return datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Tentative date simple YYYY-MM-DD
                    d = datetime.date.fromisoformat(v)
                    return datetime.datetime.combine(d, datetime.time.min)
                except ValueError:
                    raise ValueError("Format de date invalide (ISO attendu)")
        return v
    
    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class PatientUpdate(BaseModel):
    numero_dossier: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[Union[datetime.datetime, datetime.date, str]] = None
    sexe: Optional[str] = None
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    assurance: Optional[str] = None
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    numero_dossier: Optional[str] = None  # Changé en optionnel pour éviter les erreurs de validation si NULL en BDD
    created_at: datetime.datetime
    dossier: Optional[DossierOut] = None
    model_config = ConfigDict(from_attributes=True)

# --- 6. SCHÉMAS AGENDA CLINIQUE ---

class AppointmentStatus(str, Enum):
    PREVU = "PRÉVU"
    EN_SALLE_ATTENTE = "EN_S_ATTENTE" 
    EN_FAUTEUIL = "EN_FAUTEUIL"
    TERMINE = "TERMINÉ"
    ANNULE = "ANNULÉ"

class AppointmentBase(BaseModel):
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    datetime_start: datetime.datetime
    duration_minutes: int = 30
    motif: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.PREVU
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    datetime_start: Optional[datetime.datetime] = None
    duration_minutes: Optional[int] = None
    motif: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentOut(AppointmentBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class AppointmentImportItem(BaseModel):
    patient_name: str
    datetime_start: datetime.datetime
    duration_minutes: int
    notes: Optional[str] = None
    patient_id: Optional[int] = None
    status: AppointmentStatus = AppointmentStatus.PREVU

class AppointmentBulkCreate(BaseModel):
    appointments: List[AppointmentImportItem]

# --- 7. SCHÉMA ANALYSE CÉPHALOMÉTRIQUE ---

class CephaloAnalysisOut(BaseModel):
    id: int
    image_original_path: str
    angles_data: Optional[Dict] = None
    landmarks_data: Optional[Dict] = None
    ai_diagnostic: Optional[DiagnosticSLM] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- 7bis. SCHÉMA ANALYSE PANORAMIQUE (DENTEX / LOKI) ---

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


# ==============================================================================
# --- 7. MODÈLES : DOCUMENT FACTORY ---
# ==============================================================================

class MedicationItem(BaseModel):
    nom: str
    dosage: Optional[str] = ""
    forme: Optional[str] = "Sachets"
    posologie: Optional[str] = ""
    type: Optional[str] = "MEDICAMENT" # MEDICAMENT ou EXAMEN

class OrdonnanceData(BaseModel):
    medications: List[MedicationItem] = []
    doc_date: Optional[datetime.date] = None # Utilise date d'en-tête, si absent utilise today
    age: Optional[int] = None
    gender: Optional[str] = None

class CertificatData(BaseModel):
    reason: Optional[str] = "Certificat Médical"
    days: Optional[int] = 1
    start_date: Optional[datetime.date] = None # Sera remplacé par today si None dans le générateur
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

# --- PHASE 5 : PAYMENT TRACKING ---

class InstallmentBase(BaseModel):
    label: str
    amount: float
    due_date: datetime.date
    paid_date: Optional[datetime.date] = None
    status: str = "EN_ATTENTE"
    notes: Optional[str] = None

class InstallmentCreate(InstallmentBase):
    pass

class InstallmentOut(InstallmentBase):
    id: int
    plan_id: int
    model_config = ConfigDict(from_attributes=True)

class InstallmentPlanBase(BaseModel):
    title: str
    total_amount: float

class InstallmentPlanCreate(InstallmentPlanBase):
    patient_id: int
    installments: List[InstallmentCreate]

class InstallmentPlanOut(InstallmentPlanBase):
    id: int
    patient_id: int
    created_at: datetime.datetime
    installments: List[InstallmentOut]
    model_config = ConfigDict(from_attributes=True)

class DevisItem(BaseModel):
    acte: str = ""
    dent: str = ""
    dents: List[Union[int, str]] = []  # Liste des numéros de dents concernées
    prix_unitaire: float = 0.0

class InstallmentItem(BaseModel):
    date: Optional[datetime.date] = None
    amount: float = 0.0
    label: str = "Versement"

class DevisData(BaseModel):
    items: List[DevisItem] = []
    doc_date: Optional[datetime.date] = None
    teeth_data: List[ToothData] = []  # Données détaillées de l'odontogramme
    age: Optional[int] = None
    gender: Optional[str] = None
    installments: List[InstallmentItem] = []

class PaymentItem(BaseModel):
    date: Optional[datetime.date] = None
    acte: str = ""
    dent: str = "-"
    dents: List[Union[int, str]] = []  # Liste des numéros de dents concernées
    montant: float = 0.0
    mode_reglement: str = "Espèces"

class HonorairesData(BaseModel):
    payments: List[PaymentItem] = []
    doc_date: Optional[datetime.date] = None
    teeth_data: List[ToothData] = []  # Données détaillées de l'odontogramme
    age: Optional[int] = None
    gender: Optional[str] = None
    installments: List[InstallmentItem] = []

class LibreData(BaseModel):
    titre: str = Field(default='DOCUMENT MÉDICAL', alias='title')
    contenu: str = Field(default='', alias='content')
    doc_date: Optional[datetime.date] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    custom_patient: Optional[str] = None
    custom_date: Optional[str] = None
    hide_patient_header: bool = False
    page_size: str = "A5"
    alignment: str = "justify"
    
    model_config = ConfigDict(populate_by_name=True)

class DocumentRequest(BaseModel):
    type: Literal["ordonnance", "certificat", "devis", "note", "honoraires", "libre"]
    patient_id: int
    data: Dict


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
    calcul_ddm_reelle: Optional[float] = None

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

class AnalysisMetadata(BaseModel):
    unit: str = "mm"
    pixel_ratio: float
    type: str = "COM_Skeletal"
    cohort: str

class CephaloAnalysisResult(BaseModel):
    """Schéma de sortie unifié du moteur CephaloEngine."""
    analysis_metadata: AnalysisMetadata
    metrics: AnalysisMetrics
    visual_debug: Dict[str, Any]
    t1_projection: Dict[str, Tuple[float, float]]
    ai_narrative: Optional[Dict[str, str]] = None
    ai_diagnostic: Optional[DiagnosticSLM] = None # Version structurée
    clinical_data: ClinicalData

class AnalysisUpdate(BaseModel):
    landmarks: List[LandmarkItem]
    mm_per_pixel: Optional[float] = None
    ai_diagnostic: Optional[Dict[str, str]] = None
    clinical_data: Optional[ClinicalData] = None
    mcnmara_projections: Optional[McNamaraProjections] = None  # Projections A', B', N'

class CephaloViewModel(BaseModel):
    """ViewModel unifié pour le générateur PDF (découplage total)."""
    patient_nom: str
    patient_prenom: str
    patient_age: str
    patient_id: Optional[int] = None
    
    analysis: CephaloAnalysisResult
    
    cabinet_config: Optional[Dict[str, Any]] = None # p_color, logos, etc.
    doctor_name: Optional[str] = None
    
    radio_image_path: Optional[str] = None
    date_generation: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%d/%m/%Y"))

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
    created_at: datetime.datetime
    file_size: int
    is_latest: bool

class DocumentArchiveOut(DocumentArchiveBase):
    id: Union[int, str]
    patient_id: int
    filename: str
    original_filename: str
    file_size: int
    file_hash: str
    document_group_id: str
    version_number: int
    is_latest_version: bool
    status: DocumentStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None
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
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    page: int = 1
    page_size: int = 20

class DocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    documents: List[DocumentArchiveOut]

class DocumentTrashResponse(BaseModel):
    message: str
    document_id: Union[int, str]
    deleted_at: datetime.datetime
    permanent_delete_at: datetime.datetime

class DocumentRestoreResponse(BaseModel):
    message: str
    document_id: Union[int, str]
    restored_at: datetime.datetime

class DocumentBatchDeleteRequest(BaseModel):
    document_ids: List[Union[int, str]]
    permanent: bool = False

class DocumentBatchResponse(BaseModel):
    success: List[int]
    failed: List[Dict[int, str]]  # id -> error message

class DocumentShareLink(BaseModel):
    token: str
    expires_at: datetime.datetime
    download_url: str
    max_downloads: int = 5

class DocumentPreviewResponse(BaseModel):
    document_id: Union[int, str]
    preview_url: str
    thumbnail_url: Optional[str] = None
    file_type: str
    can_preview: bool
 
class HonoraireItem(BaseModel):
    id: Union[int, str]
    patient_id: int
    patient_name: str
    assurance: Optional[str] = "AUCUNE"
    date: datetime.datetime
    title: str
    amount: float
    file_url: str
    
class HonoraireListResponse(BaseModel):
    total: int
    total_amount: float
    items: List[HonoraireItem]



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
    nom_cabinet: str = Field(default="", max_length=255)
    nom_praticien: str = Field(default="", max_length=255)
    nom_praticien_ar: str = Field(default="", max_length=255)
    cabinet_type: str = Field(default="PRIVE") # "PRIVE" ou "CLINIQUE"
    header_lines_fr: List[str] = Field(default_factory=list, max_length=6)
    header_lines_ar: List[str] = Field(default_factory=list, max_length=6)
    footer_address: Optional[str] = Field(default="", max_length=500)
    footer_phones: Optional[str] = Field(default="", max_length=255)
    adresse: Optional[str] = Field(default="", max_length=500, alias="adresse") # Alias pour compatibilité frontend
    telephone: Optional[str] = Field(default="", max_length=255, alias="telephone") 
    nom: Optional[str] = Field(default=None, max_length=255) # Alias pour nom_praticien
    
    # Identifiants légaux
    ice: Optional[str] = Field(default="", max_length=50)
    if_: Optional[str] = Field(default="", max_length=50, alias="if")
    inpe: Optional[str] = Field(default="", max_length=50)
    
    letterhead_path: Optional[str] = None
    primary_color: str = Field(default="#003380", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#1e40af", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(default="#60a5fa", pattern=r"^#[0-9A-Fa-f]{6}$")
    font_fr: str = Field(default="Helvetica", max_length=50)
    font_ar: str = Field(default="Amiri", max_length=50)
    watermark_enabled: bool = Field(default=True)
    watermark_opacity: float = Field(default=0.10, ge=0.0, le=1.0)
    selected_theme: str = Field(default="elite", max_length=20)
    selected_template: str = Field(default="classic", max_length=20)
    margin_top: float = Field(default=3.6, ge=0.0, le=15.0)
    margin_bottom: float = Field(default=3.2, ge=0.0, le=15.0)
    contacts_json: Optional[Dict] = Field(default_factory=dict)
    
    # QR Code Strategy (Elite v4.0)
    qr_code_enabled: bool = Field(default=False)
    qr_code_type: QRCodeType = Field(default=QRCodeType.VCARD)
    qr_code_value: Optional[str] = Field(default=None, max_length=500)
    qr_code_color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    qr_code_label: Optional[str] = Field(default=None, max_length=100)
    
    # Templates de clôture (Accounting)
    cloture_note_template: str = Field(default="Arrêtée la présente note à la somme de {total_words} TTC.")
    cloture_devis_template: str = Field(default="Arrêté le présent devis à la somme de {total_words} TTC.")


class CabinetConfigCreate(CabinetConfigBase):
    pass


class CabinetConfigUpdate(CabinetConfigBase):
    pass


class CabinetConfigOut(CabinetConfigBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str
    public_id: str
    owner_id: int
    logo_path: Optional[str] = None
    is_initialized: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


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
    created_at: datetime.datetime
    updated_at: datetime.datetime


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

class VisionResult(BaseModel):
    analysis_id: int
    date_analyse: datetime.datetime
    points: Dict
    metrics: Dict
    status: str
    message: Optional[str] = None

# --- 13. SCHÉMAS AUTHENTIFICATION ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    nom_complet: Optional[str] = None
    is_active: bool = True
    employer_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# --- 14. GESTION D'ÉQUIPE (SOUS-COMPTES ASSISTANTES) ---

class TeamMemberCreate(BaseModel):
    """Création d'un sous-compte assistante rattaché au praticien connecté."""
    email: EmailStr
    password: str = Field(min_length=4, description="Mot de passe provisoire (4 caractères minimum)")
    nom_complet: str = Field(min_length=2, description="Nom complet de l'assistante")
    telephone_mobile: Optional[str] = None

class TeamMemberUpdate(BaseModel):
    """Mise à jour d'un sous-compte existant."""
    nom_complet: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone_mobile: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = Field(None, min_length=4)

class TeamMemberOut(BaseModel):
    """Représentation d'un membre de l'équipe (lecture)."""
    id: int
    email: str
    role: str
    nom_complet: Optional[str] = None
    telephone_mobile: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- 11. ANALYSE PANORAMIQUE (OPG) ---

class BoundingBox(BaseModel):
    """Coordonnées de la boîte englobante en pixels [x, y, w, h]."""
    x: float
    y: float
    w: float
    h: float
    confidence: float

class ToothObject(BaseModel):
    """Représentation d'une dent individuelle selon la nomenclature FDI."""
    fdi: int  # 11-48
    bbox: BoundingBox
    label: str = "tooth"
    
    @field_validator('fdi')
    @classmethod
    def validate_fdi(cls, v):
        # Quadrants 1-4, Dents 1-8
        valid_fdis = [q*10 + d for q in [1, 2, 3, 4] for d in range(1, 9)]
        # Dents de lait (optionnel mais bon pour la complétude)
        valid_fdis += [q*10 + d for q in [5, 6, 7, 8] for d in range(1, 6)]
        
        if v not in valid_fdis:
            raise ValueError(f"Numéro FDI invalide : {v}")
        return v

class Finding(BaseModel):
    """Pathologie ou objet clinique détecté (Carie, Implant, Lésion, etc.)."""
    label: str
    fdi: Optional[int] = None
    bbox: BoundingBox
    clinical_term: str  # Traduction française (ex: "Carie profonde")
    severity: Literal["low", "medium", "high", "none"] = "none"

class PanoramicAnalysis(BaseModel):
    """Résultat complet d'une analyse radiographique panoramique."""
    image_url: str
    teeth: List[ToothObject]
    findings: List[Finding]
    summary_markdown: Optional[str] = None
    processing_time_ms: float
    model_version: str = "Loki-Silvres-v1.0"
