"""Only the cabinet's document identity crosses into PDF renderers.

No UI theme, licensing, credentials, patient data or tenant identifiers here.
The canonical layout logic remains BaseTemplate.
"""
from __future__ import annotations

# Keep this explicit; copying CabinetConfig.__table__.columns would also send
# internal and non-documentary cabinet data into the rendering context.
DOCUMENT_BRANDING_FIELDS = (
    "nom_cabinet", "nom_praticien", "nom_praticien_ar",
    "logo_path", "letterhead_path", "use_letterhead",
    "header_lines_fr", "header_lines_ar", "specialty_ids",
    "custom_specialty_fr", "custom_specialty_ar", "header_customized",
    "footer_address", "footer_phones", "contacts_json",
    "primary_color", "secondary_color", "accent_color",
    "selected_template", "font_fr", "font_ar",
    "watermark_enabled", "watermark_opacity",
    "margin_top", "margin_bottom", "content_offset_y",
    "header_scale", "header_font_scale", "header_logo_scale",
    "header_line_height", "footer_font_scale", "footer_qr_scale",
    "footer_line_height", "header_logo_offset_x", "header_logo_offset_y",
    "qr_code_enabled", "qr_code_type", "qr_code_value", "qr_code_color",
    "qr_code_style", "qr_code_label", "qr_code_offset_x",
    "qr_code_offset_y", "hide_header", "hide_footer",
)

def serialize_document_branding(cabinet, user=None) -> dict:
    """Resolve a previously authorized cabinet; never query a tenant here."""
    if cabinet is None:
        return {"selected_template": "swiss", "primary_color": "#003380",
                "secondary_color": "#64748B", "qr_code_enabled": False}
    data = {key: getattr(cabinet, key) for key in DOCUMENT_BRANDING_FIELDS
            if hasattr(cabinet, key)}
    # Enum values are accepted by QR code comparisons and are serializable as strings.
    if hasattr(data.get("qr_code_type"), "value"):
        data["qr_code_type"] = data["qr_code_type"].value
    data["selected_template"] = data.get("selected_template") or "swiss"
    if user is not None:
        data["nom_praticien"] = data.get("nom_praticien") or getattr(user, "nom_complet", "") or ""
        data["footer_address"] = data.get("footer_address") or getattr(user, "adresse_complete", "") or ""
        data["footer_phones"] = data.get("footer_phones") or getattr(user, "telephone_mobile", "") or ""
    return data
