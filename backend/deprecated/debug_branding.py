
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from backend.services.base_template import BaseTemplate
import os

class MockConfig:
    def __init__(self):
        self.primary_color = "#1e40af"
        self.secondary_color = "#334155"
        self.accent_color = "#1e40af"
        self.logo_path = None
        self.watermark_enabled = True
        self.watermark_opacity = 0.05
        self.header_lines_fr = [
            "Chirurgien Dentiste",
            "Soins - Prothèse",
            "Chirurgie - Parodontologie",
            "Blanchiment - Orthodontie"
        ]
        self.header_lines_ar = [
            "طبيب جراح في جراحة الأسنان",
            "علاجات - تيجان",
            "جراحة - طب اللثة",
            "تبييض - تقويم الأسنان"
        ]
        self.footer_address = "156, 1er étage, Secteur 3, Lotisselement Zerdal Gharbia, Sidi Bouknadel, Salé"
        self.contacts_json = {
            "fixe": {"enabled": True, "value": "0537822333"},
            "whatsapp": {"enabled": True, "value": "0648275852"}
        }
        self.ice = "001819709000006"
        self.if_ = "1449634"
        self.inpe = "104164231"

def generate_test_pdf():
    output_path = "branding_test_elite.pdf"
    c = canvas.Canvas(output_path, pagesize=A5)
    template = BaseTemplate()
    config = MockConfig()
    
    # Dessiner les éléments de branding
    template.draw_static_elements(c, c, config=config, draw_legal_ids=True)
    
    # Contenu fictif
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(A5[0]/2, A5[1]-6*cm, "TEST DE BRANDING ELITE")
    c.setFont("Helvetica", 10)
    c.drawCentredString(A5[0]/2, A5[1]-7*cm, "Validation des en-têtes et du footer v4.2")
    
    c.showPage()
    c.save()
    print(f"PDF généré avec succès : {os.path.abspath(output_path)}")

if __name__ == "__main__":
    generate_test_pdf()
