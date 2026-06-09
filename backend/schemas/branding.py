from pydantic import BaseModel, field_validator
from typing import Optional
from typing import Any


class BrandingPreviewPayload(BaseModel):
    """Schéma de payload pour la génération d'un aperçu de branding de document."""
    selected_template: Optional[str] = None
    font_fr: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None
    header_scale: Optional[float] = None
    header_font_scale: Optional[float] = None
    header_logo_scale: Optional[float] = None
    header_line_height: Optional[float] = None
    footer_font_scale: Optional[float] = None
    footer_qr_scale: Optional[float] = None
    footer_line_height: Optional[float] = None
    qr_code_enabled: Optional[bool] = None
    qr_code_type: Optional[str] = None
    qr_code_style: Optional[str] = None
    qr_code_value: Optional[str] = None
    qr_code_label: Optional[str] = None

    @field_validator('*', mode='before')
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v
