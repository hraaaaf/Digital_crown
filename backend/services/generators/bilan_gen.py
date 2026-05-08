import os
import math
import logging
from datetime import date, datetime
from PIL import Image as PILImage, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from backend.services.base_template import BaseTemplate, NAVY_BLUE

logger = logging.getLogger(__name__)

class BilanPDFGenerator(BaseTemplate):
    """
    Générateur du Bilan Orthodontique Complet (Multi-pages).
    Page 1 : Synthèse Clinique & Plan de traitement.
    Page 2 : Céphalométrie (Image tracée + Mesures déviantes).
    Page 3 : Analyse des Moulages (DDM).
    """
    
    def __init__(self, output_dir="static/reports"):
        super().__init__()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._init_styles()

    def _init_styles(self):
        """Initialisation du Design System pour le Bilan V4."""
        self.styles.add(ParagraphStyle(name='ReportTitle', parent=self.styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=NAVY_BLUE, alignment=TA_CENTER, spaceAfter=20))
        self.styles.add(ParagraphStyle(name='PageTitle', parent=self.styles['Heading2'], fontName='Helvetica-Bold', fontSize=15, textColor=NAVY_BLUE, alignment=TA_CENTER, spaceAfter=25, spaceBefore=10))
        self.styles.add(ParagraphStyle(name='SectionTitle', parent=self.styles['Heading3'], fontName='Helvetica-Bold', fontSize=13, textColor=NAVY_BLUE, spaceBefore=15, spaceAfter=10))
        self.styles.add(ParagraphStyle(name='PatientInfo', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=NAVY_BLUE, leading=16))
        self.styles.add(ParagraphStyle(name='Narrative', parent=self.styles['Normal'], fontName='Helvetica', fontSize=10, leading=15, alignment=TA_JUSTIFY, spaceAfter=6))
        self.styles.add(ParagraphStyle(name='TreatmentPlan', parent=self.styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=11, leading=16, alignment=TA_JUSTIFY, textColor=colors.darkslategrey))

    def _calculate_age(self, born):
        if not born: return "N/A"
        today = date.today()
        birth = born.date() if isinstance(born, datetime) else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    def _draw_dashed_line(self, draw, pt1, pt2, fill, width=2, dash_length=15):
        x1, y1 = pt1; x2, y2 = pt2
        length = math.hypot(x2 - x1, y2 - y1)
        if length == 0: return
        dashes = int(length / dash_length)
        for i in range(dashes):
            if i % 2 == 0:
                start = (x1 + (x2 - x1) * i / dashes, y1 + (y2 - y1) * i / dashes)
                end = (x1 + (x2 - x1) * (i + 1) / dashes, y1 + (y2 - y1) * (i + 1) / dashes)
                draw.line([start, end], fill=fill, width=width)

    def _burn_in_tracings(self, image_path, landmarks, output_path):
        """Incruste les lignes céphalométriques professionnelles sur l'image."""
        try:
            with PILImage.open(image_path) as img:
                img = img.convert("RGB")
                draw = ImageDraw.Draw(img)
                lm_dict = {p['id']: (p['x'], p['y']) for p in landmarks if 'id' in p}
                def get_pt(*names):
                    for n in names:
                        if n in lm_dict: return lm_dict[n]
                    return None
                
                # Tracés Plan de Francfort & Mandibulaire (Bleu)
                po, or_pt = get_pt('Po', 'Porion (Po)'), get_pt('Or', 'Orbitale (Or)')
                if po and or_pt: draw.line([po, or_pt], fill="#3b82f6", width=4)
                go, me = get_pt('Go', 'Gonion (Go)'), get_pt('Me', 'Menton (Me)')
                if go and me: draw.line([go, me], fill="#3b82f6", width=4)
                
                # Axes Incisifs (Rouge/Vert)
                u1a, u1i = get_pt('U1_apex', 'U1a'), get_pt('U1_incisal', 'U1i')
                if u1a and u1i: draw.line([u1a, u1i], fill="#ef4444", width=4)
                l1a, l1i = get_pt('L1_apex', 'L1a'), get_pt('L1_incisal', 'L1i')
                if l1a and l1i: draw.line([l1a, l1i], fill="#22c55e", width=4)

                # Verticale de Nasion (Jaune pointillé)
                n_pt = get_pt('N', 'Nasion (N)')
                if n_pt: self._draw_dashed_line(draw, n_pt, (n_pt[0], img.height), fill="#eab308", width=3, dash_length=20)
                
                img.save(output_path)
                return True
        except Exception as e:
            logger.error(f"Erreur Burn-in: {e}")
            return False

    def _draw_canvas(self, canvas, doc):
        """Applique l'en-tête et le footer hérités."""
        self.draw_static_elements(canvas, doc)

    def generate(self, patient_data, analysis_payload, image_path=None, filename=None):
        """Génère le rapport multi-pages V4."""
        p_nom = getattr(patient_data, 'nom', 'Inconnu')
        p_prenom = getattr(patient_data, 'prenom', '')
        p_age = self._calculate_age(getattr(patient_data, 'date_naissance', None))
        
        results = analysis_payload.get("results", analysis_payload)
        clinical_data = results.get("clinical_data", {})
        ai_diag = results.get("ai_diagnostic", results.get("ai_narrative", {}))

        if not filename:
            filename = f"BILAN_COMPLET_{p_nom.upper()}_{datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
        file_path = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=4.5*cm, bottomMargin=3.5*cm)
        doc.qr_type = 'VALIDATION'
        doc.doc_id = f"BILAN-{p_nom[:3].upper()}-{datetime.now().strftime('%m%H%M')}"
        elements = []

        # ==============================================================================
        # PAGE 1 : SYNTHÈSE CLINIQUE & PLAN DE TRAITEMENT
        # ==============================================================================
        elements.append(Paragraph("BILAN ORTHODONTIQUE COMPLET", self.styles['ReportTitle']))
        date_display = datetime.now().strftime('%d/%m/%Y')
        info_text = f"<b>Patient(e) :</b> {p_nom.upper()} {p_prenom.capitalize()}<br/>"
        info_text += f"<b>Âge :</b> {p_age} ans &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date du Bilan :</b> {date_display}"
        elements.append(Paragraph(info_text, self.styles['PatientInfo']))
        elements.append(Spacer(1, 1.0*cm))

        elements.append(Paragraph("1. SYNTHÈSE DIAGNOSTIQUE (IA)", self.styles['SectionTitle']))
        if isinstance(ai_diag, dict) and ai_diag:
            if ai_diag.get("diagnostic_squelettique"):
                elements.append(Paragraph(f"<b>• Squelettique :</b> {ai_diag.get('diagnostic_squelettique')}", self.styles['Narrative']))
            if ai_diag.get("analyse_dentaire"):
                elements.append(Paragraph(f"<b>• Dentaire :</b> {ai_diag.get('analyse_dentaire')}", self.styles['Narrative']))
        else:
            elements.append(Paragraph("Synthèse automatique en attente de validation.", self.styles['Narrative']))
        
        elements.append(Spacer(1, 1.0*cm))
        elements.append(Paragraph("2. PLAN DE TRAITEMENT THERAPEUTIQUE", self.styles['SectionTitle']))
        plan_texte = clinical_data.get("plan_traitement")
        if plan_texte and plan_texte.strip():
            elements.append(Paragraph(plan_texte.replace('\n', '<br/>'), self.styles['TreatmentPlan']))
        else:
            elements.append(Paragraph("Aucun plan de traitement saisi par le praticien.", self.styles['Narrative']))

        elements.append(PageBreak())

        # ==============================================================================
        # PAGE 2 : IMAGERIE ET CÉPHALOMÉTRIE
        # ==============================================================================
        elements.append(Paragraph("IMAGERIE & CÉPHALOMÉTRIE TRACÉE", self.styles['PageTitle']))
        used_image_path = image_path or analysis_payload.get('image_path') or analysis_payload.get('image_original_path')
        if used_image_path:
            local_path = used_image_path.split("8000/")[-1] if "8000/" in used_image_path else used_image_path
            if os.path.exists(local_path):
                marked_path = os.path.join(self.output_dir, f"marked_bilan_{os.path.basename(local_path)}")
                if self._burn_in_tracings(local_path, analysis_payload.get('landmarks', []), marked_path):
                    img = Image(marked_path, width=14*cm, height=10*cm, kind='proportional')
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("Mesures Céphalométriques Déviantes", self.styles['SectionTitle']))
        table_data = [["Métrique", "Valeur", "Norme", "Statut"]]
        metrics = results.get("metrics", {})
        has_deviants = False
        for cat, measures in metrics.items():
            for name, data in measures.items():
                if data.get('status') in ["High", "Low", "Compensated"]:
                    has_deviants = True
                    norm_str = f"{data.get('norm_mean')} ({data.get('norm_min')} - {data.get('norm_max')})"
                    table_data.append([name.replace("_", " "), str(data.get('value')), norm_str, data.get('status')])

        if not has_deviants: table_data.append(["Aucune déviation détectée.", "-", "-", "Normal"])
        
        t_ceph = Table(table_data, colWidths=[6.5*cm, 3*cm, 4.5*cm, 3*cm])
        t_style = [('BACKGROUND',(0,0),(-1,0),NAVY_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.5,colors.grey)]
        for row_idx, row in enumerate(table_data[1:], start=1):
            if row[3] == "High": t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.red))
            elif row[3] == "Low": t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.darkorange))
            elif row[3] == "Compensated": t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.orange))
        t_ceph.setStyle(TableStyle(t_style))
        elements.append(t_ceph)
        
        elements.append(PageBreak())

        # ==============================================================================
        # PAGE 3 : ANALYSE DES MOULAGES (DDM)
        # ==============================================================================
        elements.append(Paragraph("ANALYSE DES MOULAGES (DDM)", self.styles['PageTitle']))
        ddm_max = clinical_data.get('ddm_maxillaire') or {}
        ddm_mand = clinical_data.get('ddm_mandibulaire') or {}
        
        ddm_table_data = [
            ["Arcade", "Espace Disponible (ED)", "Espace Nécessaire (EN)", "DDM Clinique"],
            ["Maxillaire", f"{ddm_max.get('espace_disponible', 0)} mm", f"{ddm_max.get('espace_necessaire', 0)} mm", f"{ddm_max.get('calcul_ddm', 0)} mm"],
            ["Mandibulaire", f"{ddm_mand.get('espace_disponible', 0)} mm", f"{ddm_mand.get('espace_necessaire', 0)} mm", f"{ddm_mand.get('calcul_ddm', 0)} mm"],
            ["VERDICT DDM RÉELLE", "", "", f"<b>{clinical_data.get('ddm_reelle', 0)} mm</b>"]
        ]
        
        t_ddm = Table(ddm_table_data, colWidths=[4.5*cm, 4*cm, 4*cm, 4.5*cm])
        t_ddm.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.grey),('SPAN',(0,3),(2,3))]))
        elements.append(t_ddm)
        elements.append(Spacer(1, 1*cm))
        
        elements.append(Paragraph("<i>Note : La DDM Réelle intègre l'encombrement prévisionnel lié au redressement incisif calculé en céphalométrie (0.5mm par degré de correction).</i>", self.styles['Narrative']))

        doc.build(elements, onFirstPage=self._draw_canvas, onLaterPages=self._draw_canvas)
        return file_path.replace("\\", "/")