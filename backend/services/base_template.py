"""R5 façade: keep the historical document template implementation intact while
making documentary QR destinations match the mounted FastAPI routes.
"""

import logging

from reportlab.platypus import Paragraph

from backend.services.base_template_core import *  # noqa: F401,F403
from backend.services.base_template_core import BaseTemplate as _BaseTemplateCore
from backend.services import base_template_core as _core
from backend.services.qr_document_routes import build_document_qr_url

# Compatibility alias intentionally kept on the façade module: historical tests and
# callers patch backend.services.base_template.ImageReader directly.
ImageReader = _core.ImageReader


class PinnedCloture(_core.PinnedCloture):
    """Pinned closing sentence that also reserves its physical footer-adjacent space."""

    def wrap(self, availWidth, availHeight):
        paragraph = Paragraph(self.text, self.style)
        _, paragraph_height = paragraph.wrap(11.8 * _core.cm, 10 * _core.cm)
        # drawOn() in the historical implementation paints the sentence around
        # 4.4 cm from the page bottom while the content frame stops at ~2.8 cm.
        # Reserve that band so the accounting table can never run underneath it.
        reserved = max(1.6 * _core.cm, paragraph_height + 0.2 * _core.cm)
        return availWidth, reserved


class BaseTemplate(_BaseTemplateCore):
    """Base template with truthful document QR destinations."""

    @staticmethod
    def scale_elements(elements, factor):
        """Scale a disposable list so ReportLab retries never consume the source list."""
        return _BaseTemplateCore.scale_elements(list(elements), factor)

    def get_document_margins(self, config, p_width):
        """Reserve the premium header and expose a real body-only Y travel range.

        ``margin_top`` remains structural. ``content_offset_y`` is the visual body
        control in centimetres. The neutral position deliberately keeps 8 mm of
        safe headroom above the body so the supported -8 mm value always produces
        real upward movement without crossing the calculated premium-header guard.
        Positive offsets move the title/patient/table down without moving the header.
        """
        if self.has_active_letterhead(config):
            return _BaseTemplateCore.get_document_margins(self, config, p_width)

        selected = self._get_val(config, "selected_template", "swiss")
        line_scale = float(self._get_val(config, "header_line_height", 1.0))
        font_scale = float(self._get_val(config, "header_font_scale", 1.0)) * float(
            self._get_val(config, "header_scale", 1.0)
        )
        fr_lines = [line for line in (self._get_val(config, "header_lines_fr", []) or []) if str(line).strip()]
        ar_lines = [line for line in (self._get_val(config, "header_lines_ar", []) or []) if str(line).strip()]
        n_fr = max(len(fr_lines), 1)
        n_ar = max(len(ar_lines), 1)
        n_lines = max(n_fr, n_ar)

        baseline_cm = {
            "swiss": 1.20,
            "royal": 2.05,
            "clinical": 1.17,
            "modern": 1.14,
        }
        safety_cm = 0.28 + max(0.0, font_scale - 1.0) * 0.40

        if selected == "heritage":
            dense = n_lines > 4
            if dense:
                first = 1.76
                gap = 0.34 * 0.76 * line_scale
                separator = max(3.22, first + (n_lines - 1) * gap + 0.34)
            else:
                fr_gap = 0.34 * 0.82 * line_scale
                fr_bottom = 1.76 + (n_fr - 1) * fr_gap
                ar_start = max(2.64, fr_bottom + 0.42)
                ar_bottom = ar_start + (n_ar - 1) * fr_gap
                separator = max(3.22, fr_bottom + 0.40, ar_bottom + 0.40)
            required_top = (separator + safety_cm) * _core.cm
        else:
            first = baseline_cm.get(selected, 1.20)
            gap = 0.34 * line_scale
            separator = first + (n_lines - 1) * gap + 0.36
            required_top = (separator + safety_cm) * _core.cm

        configured_top = self._get_val(config, "margin_top")
        default_top = 2.8 if selected in {"swiss", "modern"} else 3.1
        structural_top = float(configured_top if configured_top is not None else default_top) * _core.cm

        min_offset_cm = -0.8
        max_offset_cm = 1.5
        upward_travel = abs(min_offset_cm) * _core.cm
        neutral_top = max(structural_top, required_top + upward_travel)

        raw_offset = float(self._get_val(config, "content_offset_y", 0.0) or 0.0)
        offset_cm = max(min_offset_cm, min(max_offset_cm, raw_offset))
        requested_body_top = neutral_top + offset_cm * _core.cm
        m_top = max(required_top, requested_body_top)

        configured_bottom = self._get_val(config, "margin_bottom")
        user_bottom = float(configured_bottom if configured_bottom is not None else 2.5) * _core.cm
        m_bottom = max(user_bottom, 2.8 * _core.cm)

        if selected == "royal":
            m_left = m_right = 2.0 * _core.cm
        else:
            m_left = m_right = 1.5 * _core.cm
        return m_top, m_bottom, m_left, m_right

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
            msg = "Bonjour Dr, je souhaite prendre rendez-vous. / السلام عليكم دكتور، أود حجز موعد."
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
