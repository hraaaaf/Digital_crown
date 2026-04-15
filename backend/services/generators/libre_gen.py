import os
import io
from datetime import datetime, date
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE


class SignatureManager:
    """Gère l'affichage intelligent de la signature sur la dernière page uniquement."""
    
    def __init__(self, base_template):
        self.base_template = base_template
        self.total_pages = 0
        self.current_page = 0
    
    def draw_with_signature(self, canvas, doc):
        """Dessine le template et gère la signature selon la page."""
        self.base_template.draw_static_elements(canvas, doc)
        self.current_page += 1
        
        # Afficher la signature UNIQUEMENT sur la dernière page
        # Si une seule page: c'est aussi la dernière
        # Si plusieurs pages: uniquement sur la dernière
        is_last_page = (self.current_page == self.total_pages)
        
        if is_last_page:
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 11)
            canvas.setFillColor(NAVY_BLUE)
            canvas.drawRightString(14.8*cm - 1.5*cm, 4*cm, "Signature et Cachet :")
            canvas.restoreState()


class LibreGenerator:
    def __init__(self, output_dir="static/documents"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_template = BaseTemplate()
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        self.styles.add(ParagraphStyle(
            name='HeaderInfo', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=NAVY_BLUE, leading=14
        ))
        self.styles.add(ParagraphStyle(
            name='HeaderDate', parent=self.styles['Normal'], fontName='Helvetica', fontSize=10, textColor=NAVY_BLUE, alignment=TA_RIGHT
        ))
        self.styles.add(ParagraphStyle(
            name='LibreTitle', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=NAVY_BLUE, alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='LibreBody', parent=self.styles['Normal'], fontName='Helvetica', fontSize=11, textColor=NAVY_BLUE, alignment=TA_JUSTIFY, leading=16
        ))

    def _calculate_age(self, born):
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _get_save_path(self, patient, data):
        doc_date = getattr(data, 'doc_date', date.today())
        year_str, month_str = doc_date.strftime('%Y'), doc_date.strftime('%m')
        save_dir = os.path.join(self.output_dir, year_str, month_str)
        os.makedirs(save_dir, exist_ok=True)
        
        doc_id = getattr(data, 'id', doc_date.strftime('%Y%m%d'))
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        filename = f"LIBRE_{safe_name}_{doc_id}.pdf"
        return os.path.join(save_dir, filename)

    def _create_header(self, patient, data):
        doc_date = getattr(data, 'doc_date', date.today())
        current_date = doc_date.strftime('%d/%m/%Y')
        age = getattr(data, 'age', self._calculate_age(patient.date_naissance))
        
        info_text = f"Nom : {patient.nom.upper()} {patient.prenom.capitalize()}<br/>Âge : {age} ans"
        header_table = Table([
            [Paragraph(info_text, self.styles['HeaderInfo']), Paragraph(f"Le : ....{current_date}....", self.styles['HeaderDate'])]
        ], colWidths=[6.0*cm, 5.8*cm])
        header_table.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
        return header_table

    def _build_elements(self, patient, data):
        """Construit la liste des éléments du document."""
        # Support both French and English field names
        titre = getattr(data, 'titre', None) or getattr(data, 'title', 'DOCUMENT MÉDICAL')
        
        # Smart Scaling : ajustement en fonction de la longueur du texte
        contenu_brut = getattr(data, 'texte', None) or getattr(data, 'content', None) or getattr(data, 'text', '')
        
        # Convertir les sauts de ligne en HTML <br/> pour préserver la mise en forme
        import html
        contenu_escape = html.escape(contenu_brut)
        contenu_html = contenu_escape.replace('\n', '<br/>')
        
        t_gap = 0.8 if len(contenu_brut) < 400 else 0.4
        
        elements = [
            Spacer(1, 0.5*cm),
            self._create_header(patient, data),
            Spacer(1, t_gap*cm),
            Paragraph(f"<u><b>{titre.upper()}</b></u>", self.styles['LibreTitle']),
            Spacer(1, 0.6*cm)  # Espace fixe après le titre
        ]

        elements.append(Paragraph(contenu_html, self.styles['LibreBody']))
        
        return elements

    def generate(self, patient, data):
        filepath = self._get_save_path(patient, data)
        elements = self._build_elements(patient, data)
        
        # === PASS 1: Compter le nombre de pages ===
        # On génère dans un buffer pour déterminer le nombre de pages
        buffer = io.BytesIO()
        temp_doc = SimpleDocTemplate(
            buffer, 
            pagesize=A5, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=3.6*cm, 
            bottomMargin=5.5*cm
        )
        
        # Fonction simple pour compter les pages
        page_count = [0]
        def count_pages(canvas, doc):
            page_count[0] += 1
            self.base_template.draw_static_elements(canvas, doc)
        
        temp_doc.build(elements, onFirstPage=count_pages, onLaterPages=count_pages)
        total_pages = page_count[0]
        
        # === PASS 2: Générer le vrai PDF avec signature sur la dernière page ===
        sig_manager = SignatureManager(self.base_template)
        sig_manager.total_pages = total_pages
        
        final_doc = SimpleDocTemplate(
            filepath, 
            pagesize=A5, 
            rightMargin=1.5*cm, 
            leftMargin=1.5*cm, 
            topMargin=3.6*cm, 
            bottomMargin=5.5*cm
        )
        final_doc.build(elements, onFirstPage=sig_manager.draw_with_signature, onLaterPages=sig_manager.draw_with_signature)
        
        relative_path = filepath[filepath.find("static"):] if "static" in filepath else filepath
        return relative_path.replace("\\", "/")
