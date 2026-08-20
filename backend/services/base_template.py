"""R5 façade: keep the historical document template implementation intact while
making documentary QR destinations match the mounted FastAPI routes.
"""

import logging

from backend.services.base_template_core import *  # noqa: F401,F403
from backend.services.base_template_core import BaseTemplate as _BaseTemplateCore
from backend.services import base_template_core as _core
from backend.services.qr_document_routes import build_document_qr_url

# Compatibility alias intentionally kept on the façade module: historical tests and
# callers patch backend.services.base_template.ImageReader directly.
ImageReader = _core.ImageReader


class BaseTemplate(_BaseTemplateCore):
    """Base template with truthful document QR destinations."""

    def _draw_qr_code(self, canvas, doc, config, user, p_color):
        qr_enabled = self._get_val(config, 'qr_code_enabled', False)
        if not qr_enabled:
            return

        qr_type = self._get_val(config, 'qr_code_type', 'VCARD')
        qr_value = self._get_val(config, 'qr_code_value', '')
        qr_color_hex = self._get_val(config, 'qr_code_color') or self._get_val(config, 'primary_color', '#003380')
        qr_label = self._get_val(config, 'qr_code_label', '')

        qr_data = qr_value
        if qr_type == 'VCARD' and not qr_value:
            name = self._get_val(config, 'nom_praticien') or self._get_val(user, 'nom_complet') or "Docteur"
            phone = self._get_val(config, 'footer_phones') or self._get_val(user, 'telephone_mobile') or ""
            if "/" in phone:
                phone = phone.split("/")[0].strip()
            email = getattr(user, 'email', '')
            address = self._get_val(config, 'footer_address') or self._get_val(user, 'adresse_complete', '')
            qr_data = _core.QRService.generate_vcard(name, phone, email, address=address)
        elif qr_type == 'INSTAGRAM' and qr_value:
            if not qr_value.startswith('http'):
                qr_data = f"https://instagram.com/{qr_value.replace('@', '')}"
        elif qr_type == 'VALIDATION':
            qr_data = build_document_qr_url(
                _core.os.getenv("BACKEND_URL", "http://localhost:8000"),
                "verify",
                getattr(doc, 'doc_id', 'DOC-TEMP'),
            )
        elif qr_type == 'PAYMENT':
            qr_data = build_document_qr_url(
                _core.os.getenv("BACKEND_URL", "http://localhost:8000"),
                "track",
                getattr(doc, 'doc_id', 'DOC-TEMP'),
            )
        elif qr_type == 'WHATSAPP':
            phone = qr_value
            if not phone:
                c_json = self._get_val(config, 'contacts_json')
                if isinstance(c_json, dict) and c_json.get("whatsapp", {}).get("enabled"):
                    phone = c_json.get("whatsapp", {}).get("value") or ""
            if not phone:
                phone = self._get_val(config, 'footer_phones') or self._get_val(user, 'telephone_mobile') or ""
            if "/" in phone:
                phone = phone.split("/")[0].strip()
            msg = "Bonjour Dr, je souhaite prendre rendez-vous. / السلام عليكم دكتور، أود حجز moعد."
            qr_data = _core.QRService.generate_whatsapp_url(phone, msg)
        elif qr_type == 'LOCATION':
            address = self._get_val(config, 'footer_address') or self._get_val(user, 'adresse_complete', '')
            qr_data = _core.QRService.generate_maps_url(address)
        elif qr_type == 'WEBSITE' and qr_value:
            qr_data = qr_value if qr_value.startswith('http') else f"https://{qr_value}"

        if not qr_data:
            return

        try:
            logo_filename = self._get_val(config, 'logo_path')
            actual_logo_path = None
            if logo_filename:
                actual_logo_path = _core.os.path.join(self.base_path, "static", "uploads", logo_filename)
            if actual_logo_path and not _core.os.path.exists(actual_logo_path):
                actual_logo_path = self.default_logo_path if _core.os.path.exists(self.default_logo_path) else None

            qr_style = self._get_val(config, 'qr_code_style', 'dots')
            qr_bytes = _core.QRService.generate_qr_bytes(
                qr_data,
                color=qr_color_hex,
                box_size=5,
                add_logo=True,
                logo_path=actual_logo_path,
                qr_style=qr_style,
            )
            if qr_bytes:
                p_width, p_height = doc.pagesize
                f_qr_scale = self._get_val(config, 'footer_qr_scale', 1.0)
                qr_size = 1.6 * _core.cm * f_qr_scale
                qr_offset_x = self._get_val(config, 'qr_code_offset_x', 0.0)
                qr_offset_y = self._get_val(config, 'qr_code_offset_y', 0.0)
                x_pos = p_width - 1.5 * _core.cm - qr_size + qr_offset_x * _core.cm
                y_pos = 0.8 * _core.cm + qr_offset_y * _core.cm
                x_pos = max(0.2 * _core.cm, min(x_pos, p_width - qr_size - 0.2 * _core.cm))
                y_pos = max(0.2 * _core.cm, min(y_pos, p_height - qr_size - 0.2 * _core.cm))
                canvas.drawImage(ImageReader(qr_bytes), x_pos, y_pos, width=qr_size, height=qr_size, mask='auto')

                if qr_label:
                    canvas.setFont(self.premium_bold, 6)
                    canvas.setFillColor(_core.colors.HexColor("#334155"))
                    canvas.drawCentredString(
                        x_pos + (qr_size / 2),
                        y_pos - 0.3 * _core.cm,
                        self._prepare_arabic(qr_label),
                    )
        except Exception as e:
            logging.getLogger(__name__).warning(f"QR Code ignoré (erreur rendu): {e}")
