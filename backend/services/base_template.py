import os
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- DESIGN SYSTEM : SINGLE SOURCE OF TRUTH ---
NAVY_BLUE = colors.HexColor('#003380')

class BaseTemplate:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logo_path = os.path.join(self.base_path, "static", "assets", "logo.png")
        self.font_path = os.path.join(self.base_path, "static", "assets", "fonts", "Amiri-Regular.ttf")
        
        if os.path.exists(self.font_path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', self.font_path))
                self.arabic_font = 'ArabicFont'
            except Exception:
                self.arabic_font = 'Helvetica'
        else:
            self.arabic_font = 'Helvetica'

    def _prepare_arabic(self, text):
        if not text: return ""
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)

    def draw_static_elements(self, canvas, doc):
        """Dessine les éléments statiques (Filigrane, En-tête clinique, Footer)."""
        canvas.saveState()
        
        # --- 1. FILIGRANE (10% OPACITÉ) ---
        if os.path.exists(self.logo_path):
            canvas.saveState()
            canvas.setFillAlpha(0.10)
            canvas.drawImage(self.logo_path, (14.8*cm - 7*cm)/2, (21*cm - 7*cm)/2, width=7*cm, height=7*cm, mask='auto')
            canvas.restoreState()

        # --- 2. EN-TÊTE ---
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(NAVY_BLUE)
        y_pos = 19.5*cm
        canvas.drawString(1.5*cm, y_pos, "Dr. Benmoussa Achraf")
        canvas.setFont('Helvetica', 8)
        canvas.drawString(1.5*cm, y_pos - 0.4*cm, "Chirurgien Dentiste")
        canvas.drawString(1.5*cm, y_pos - 0.8*cm, "Soins - Prothèse")
        canvas.drawString(1.5*cm, y_pos - 1.2*cm, "Chirurgie - Parodontologie")
        canvas.drawString(1.5*cm, y_pos - 1.6*cm, "Blanchiement - Orthodontie")

        if os.path.exists(self.logo_path):
            canvas.drawImage(self.logo_path, (14.8*cm - 2.5*cm)/2, 17.5*cm, width=2.5*cm, height=2.5*cm, mask='auto')

        canvas.setFont(self.arabic_font, 10 if self.arabic_font != 'Helvetica' else 9)
        ar_lines = ["د. أشرف بنموسى", "طبيب جراح للأسنان", "علاج - تعويض الأسنان", "جراحة - أمراض اللثة", "تبييض - تقويم الأسنان"]
        y_ar = y_pos
        for line in ar_lines:
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(13.3*cm, y_ar, prepared_text)
            y_ar -= 0.5*cm

        # --- 3. PIED DE PAGE ---
        # Ligne de séparation unique et nette
        canvas.setStrokeColor(NAVY_BLUE)
        canvas.setLineWidth(0.6)
        canvas.line(1.5*cm, 2.5*cm, 13.3*cm, 2.5*cm)

        # Adresse et Contacts
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(NAVY_BLUE)
        address = "156, 1er étage, Secteur 3, Lotisselement Zerdal Gharbia, Sidi Bouknadel, Salé"
        canvas.drawCentredString(14.8*cm / 2, 2*cm, address)
        contacts = "Tél : 0537822333 / WhatsApp : 0648275852"
        canvas.drawCentredString(14.8*cm / 2, 1.5*cm, contacts)

        canvas.restoreState()