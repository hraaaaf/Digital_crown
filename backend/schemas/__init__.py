"""
schemas package — re-exports every public name so that
`from backend import schemas; schemas.X` and
`from backend.schemas import X` both continue to work unchanged.

Import order matters: panoramic re-defines BoundingBox/ToothObject/Finding
(OPG v2 format) after clinical, matching the original schemas.py behaviour
where the last class definition wins.
"""

from .base import (
    QRCodeType,
    StyleKey,
    AppointmentStatus,
    DocumentType,
    DocumentStatus,
    ConflictResolution,
)

from .patient import (
    PraticienProfileOut,
    DossierOut,
    PatientBase,
    PatientUpdate,
    PatientCreate,
    PatientOut,
)

from .appointments import (
    AppointmentBase,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentOut,
    AppointmentImportItem,
    AppointmentBulkCreate,
)

from .clinical import (
    DiagnosticSLM,
    MeasureData,
    DentalAnalysis,
    SkeletalAnalysis,
    EstheticAnalysis,
    AnalysisMetrics,
    CephaloAnalysisOut,
    LandmarkItem,
    DDMComponent,
    ClinicalData,
    McNamaraProjections,
    AnalysisMetadata,
    CephaloAnalysisResult,
    AnalysisUpdate,
    CephaloViewModel,
    CephaloPDFRequest,
    CalibrationPoint,
    CalibrationRequest,
    CalibrationResponse,
    VisionResult,
)

# panoramic re-defines BoundingBox, ToothObject, Finding with OPG fields —
# these override the clinical module's names (v1 panoramic schema unused directly).
from .panoramic import (
    BoundingBox,
    Finding,
    ToothObject,
    FullAnalysis,
    PanoramicAnalysisBase,
    PanoramicAnalysisCreate,
    PanoramicAnalysisOut,
    PanoramicAnalysis,
    PanoramicReportRequest,
)


from .payments import (
    PaymentCreate,
    PaymentOut,
)

from .documents import (
    MedicationItem,
    OrdonnanceData,
    CertificatData,
    ToothTreatmentInfo,
    ToothData,
    InstallmentBase,
    InstallmentCreate,
    InstallmentOut,
    InstallmentPlanBase,
    InstallmentPlanCreate,
    InstallmentPlanOut,
    DevisItem,
    InstallmentItem,
    DevisData,
    PaymentItem,
    HonorairesData,
    LibreData,
    DocumentRequest,
    MedicationOut,
    ClinicalCategoryOut,
    ClinicalProtocolOut,
    PrescriptionLearnRequest,
    ClinicalActCatalogBase,
    ClinicalActCatalogOut,
    ActLearnRequestItem,
    ActLearnRequest,
    AIPrescriptionRequest,
    BIStatsOut,
    DocumentArchiveBase,
    DocumentArchiveCreate,
    DocumentVersionInfo,
    DocumentArchiveOut,
    DocumentConflictCheck,
    DocumentArchiveRequest,
    DocumentArchiveResponse,
    DocumentListParams,
    DocumentListResponse,
    DocumentTrashResponse,
    DocumentRestoreResponse,
    DocumentBatchDeleteRequest,
    DocumentBatchResponse,
    DocumentShareLink,
    DocumentPreviewResponse,
    HonoraireItem,
    HonoraireListResponse,
)

from .cabinet import (
    FontConfig,
    ColorConfig,
    MarginConfig,
    LayoutConfig,
    WatermarkConfig,
    HeaderConfig,
    BorderConfig,
    TypographyConfig,
    SpacingConfig,
    LetterheadConfig,
    DesignConfig,
    CabinetConfigBase,
    CabinetConfigCreate,
    CabinetConfigUpdate,
    CabinetConfigOut,
    CabinetInitStatus,
    DocumentTemplateBase,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentTemplateOut,
    DocumentTemplateList,
    TemplatePreviewRequest,
)

from .auth import (
    Token,
    RefreshRequest,
    TokenData,
    UserLogin,
    UserOut,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberOut,
    SupabaseSyncRequest,
)

from .branding import (
    BrandingPreviewPayload,
)

__all__ = [
    # base
    "QRCodeType", "StyleKey", "AppointmentStatus",
    "DocumentType", "DocumentStatus", "ConflictResolution",
    # patient
    "PraticienProfileOut", "DossierOut",
    "PatientBase", "PatientUpdate", "PatientCreate", "PatientOut",
    # appointments
    "AppointmentBase", "AppointmentCreate", "AppointmentUpdate",
    "AppointmentOut", "AppointmentImportItem", "AppointmentBulkCreate",
    # clinical
    "DiagnosticSLM", "MeasureData", "DentalAnalysis", "SkeletalAnalysis",
    "EstheticAnalysis", "AnalysisMetrics", "CephaloAnalysisOut",
    "LandmarkItem", "DDMComponent", "ClinicalData", "McNamaraProjections",
    "AnalysisMetadata", "CephaloAnalysisResult", "AnalysisUpdate",
    "CephaloViewModel", "CephaloPDFRequest",
    "CalibrationPoint", "CalibrationRequest", "CalibrationResponse",
    "VisionResult",
    # panoramic (OPG v2 — overrides v1 BoundingBox/ToothObject/Finding)
    "BoundingBox", "Finding", "ToothObject",
    "FullAnalysis", "PanoramicAnalysisBase", "PanoramicAnalysisCreate",
    "PanoramicAnalysisOut", "PanoramicAnalysis", "PanoramicReportRequest",

    # documents
    "MedicationItem", "OrdonnanceData", "CertificatData",
    "ToothTreatmentInfo", "ToothData",
    "InstallmentBase", "InstallmentCreate", "InstallmentOut",
    "InstallmentPlanBase", "InstallmentPlanCreate", "InstallmentPlanOut",
    "DevisItem", "InstallmentItem", "DevisData",
    "PaymentItem", "HonorairesData", "LibreData", "DocumentRequest",
    "MedicationOut", "ClinicalCategoryOut", "ClinicalProtocolOut",
    "PrescriptionLearnRequest",
    "ClinicalActCatalogBase", "ClinicalActCatalogOut",
    "ActLearnRequestItem", "ActLearnRequest",
    "AIPrescriptionRequest", "BIStatsOut",
    "DocumentArchiveBase", "DocumentArchiveCreate", "DocumentVersionInfo",
    "DocumentArchiveOut", "DocumentConflictCheck",
    "DocumentArchiveRequest", "DocumentArchiveResponse",
    "DocumentListParams", "DocumentListResponse",
    "DocumentTrashResponse", "DocumentRestoreResponse",
    "DocumentBatchDeleteRequest", "DocumentBatchResponse",
    "DocumentShareLink", "DocumentPreviewResponse",
    "HonoraireItem", "HonoraireListResponse",
    # cabinet
    "FontConfig", "ColorConfig", "MarginConfig", "LayoutConfig",
    "WatermarkConfig", "HeaderConfig", "BorderConfig",
    "TypographyConfig", "SpacingConfig", "LetterheadConfig", "DesignConfig",
    "CabinetConfigBase", "CabinetConfigCreate", "CabinetConfigUpdate",
    "CabinetConfigOut", "CabinetInitStatus",
    "DocumentTemplateBase", "DocumentTemplateCreate", "DocumentTemplateUpdate",
    "DocumentTemplateOut", "DocumentTemplateList", "TemplatePreviewRequest",
    # auth
    "Token", "RefreshRequest", "TokenData", "UserLogin", "UserOut",
    "TeamMemberCreate", "TeamMemberUpdate", "TeamMemberOut",
    "SupabaseSyncRequest",
    # branding
    "BrandingPreviewPayload",
]
