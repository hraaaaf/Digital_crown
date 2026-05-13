from pydantic import BaseModel, ConfigDict, Field
import datetime
from typing import Optional, Dict, List, Literal, Any

from .base import QRCodeType, StyleKey, DocumentType


# --- DESIGN CONFIG ---

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
    enabled: bool = Field(default=False)
    image_url: Optional[str] = Field(default=None)
    hide_default_header: bool = Field(default=True)
    hide_default_footer: bool = Field(default=True)


class DesignConfig(BaseModel):
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


# --- CABINET CONFIG ---

class CabinetConfigBase(BaseModel):
    nom_cabinet: str = Field(default="", max_length=255)
    nom_praticien: str = Field(default="", max_length=255)
    nom_praticien_ar: str = Field(default="", max_length=255)
    cabinet_type: str = Field(default="PRIVE")
    header_lines_fr: List[str] = Field(default_factory=list, max_length=6)
    header_lines_ar: List[str] = Field(default_factory=list, max_length=6)
    specialty_ids: List[str] = Field(default_factory=list)
    footer_address: Optional[str] = Field(default="", max_length=500)
    footer_phones: Optional[str] = Field(default="", max_length=255)
    adresse: Optional[str] = Field(default="", max_length=500, alias="adresse")
    telephone: Optional[str] = Field(default="", max_length=255, alias="telephone")
    nom: Optional[str] = Field(default=None, max_length=255)
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
    app_accent_color: Optional[str] = Field(default=None, pattern=r"^(?:#[0-9A-Fa-f]{6})?$")
    selected_template: str = Field(default="classic", max_length=20)
    margin_top: float = Field(default=3.6, ge=0.0, le=15.0)
    margin_bottom: float = Field(default=3.2, ge=0.0, le=15.0)
    contacts_json: Optional[Dict] = Field(default_factory=dict)
    qr_code_enabled: bool = Field(default=False)
    qr_code_type: QRCodeType = Field(default=QRCodeType.VCARD)
    qr_code_value: Optional[str] = Field(default=None, max_length=500)
    qr_code_color: Optional[str] = Field(default=None, pattern=r"^(?:#[0-9A-Fa-f]{6})?$")
    qr_code_label: Optional[str] = Field(default=None, max_length=100)
    cloture_note_template: str = Field(default="Arrêtée la présente note à la somme de {total_words} TTC.")
    cloture_devis_template: str = Field(default="Arrêté le présent devis à la somme de {total_words} TTC.")
    show_patient_badges: bool = Field(default=True)


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


# --- DOCUMENT TEMPLATES ---

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
