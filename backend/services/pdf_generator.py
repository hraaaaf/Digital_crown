import os
import math
from datetime import datetime
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

class PDFReportGenerator:
    def __init__(self, output_dir="static/reports"):
        self.output_dir = output_dir
        # Recherche intelligente de l'image de fond
        self.bg_image_path = self._find_header_bg()
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.styles = getSampleStyleSheet()
        
        # Style Titre Principal
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.navy,
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10
        ))

        # Style Conclusion
        self.styles.add(ParagraphStyle(
            name='ConclusionText',
            parent=self.styles['Normal'],
            fontName='Helvetica-BoldOblique',
            fontSize=11,
            textColor=colors.darkslategrey,
            leading=14
        ))

    def _find_header_bg(self):
        """Cherche header_bg.jpg partout."""
        candidates = [
            "header_bg.jpg",
            "backend/header_bg.jpg",
            "static/header_bg.jpg",
            "backend/static/header_bg.jpg",
            os.path.join(os.getcwd(), "header_bg.jpg"),
            os.path.join(os.getcwd(), "backend", "header_bg.jpg")
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _add_background(self, canvas, doc):
        """Dessine l'ordonnance et NETTOIE tout le centre."""
        if self.bg_image_path:
            # 1. Dessiner l'ordonnance originale en fond
            canvas.drawImage(self.bg_image_path, 0, 0, width=A4[0], height=A4[1])
            
            # 2. LE GRAND NETTOYAGE (RECTANGLE BLANC UNIQUE)
            canvas.saveState()
            canvas.setFillColor(colors.white)
            canvas.setStrokeColor(colors.white)
            
            # Zone blanche massive pour libérer l'espace central
            canvas.rect(0.5*cm, 4*cm, 20*cm, 18.5*cm, fill=1, stroke=1)
            
            canvas.restoreState()
        else:
            # Fallback ERREUR
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 14)
            canvas.setFillColor(colors.red)
            canvas.drawString(2*cm, 20*cm, "ERREUR : header_bg.jpg MANQUANT")
            canvas.restoreState()

    def _draw_dashed_line(self, draw, pt1, pt2, fill, width=2, dash_length=15):
        """Utilitaire mathématique pour tracer une ligne pointillée sur l'image Pillow"""
        x1, y1 = pt1
        x2, y2 = pt2
        length = math.hypot(x2 - x1, y2 - y1)
        if length == 0: return
        dashes = int(length / dash_length)
        for i in range(dashes):
            if i % 2 == 0:
                start = (x1 + (x2 - x1) * i / dashes, y1 + (y2 - y1) * i / dashes)
                end = (x1 + (x2 - x1) * (i + 1) / dashes, y1 + (y2 - y1) * (i + 1) / dashes)
                draw.line([start, end], fill=fill, width=width)

    def _draw_landmarks_on_image(self, image_path, landmarks, output_path):
        """
        Ouvre la radio, trace les plans géométriques cliniques, puis sauvegarde.
        """
        try:
            with PILImage.open(image_path) as img:
                img = img.convert("RGB")
                draw = ImageDraw.Draw(img)
                
                # Création d'un dictionnaire de points pour un accès facile
                # Supporte le format [{"id": "S", "x": 10, "y": 20}]
                lm_dict = {}
                if isinstance(landmarks, list):
                    for pt in landmarks:
                        if isinstance(pt, dict) and 'id' in pt and 'x' in pt and 'y' in pt:
                            lm_dict[pt['id']] = (pt['x'], pt['y'])
                
                def get_pt(*names):
                    for n in names:
                        if n in lm_dict: return lm_dict[n]
                    return None

                # 1. Plan de Francfort (Po -> Or) : Bleu
                po = get_pt('Po', 'Porion (Po)')
                or_pt = get_pt('Or', 'Orbitale (Or)')
                if po and or_pt:
                    draw.line([po, or_pt], fill="#3b82f6", width=4) # Bleu Tailwind

                # 2. Plan Mandibulaire (Go -> Me) : Bleu
                go = get_pt('Go', 'Gonion (Go)')
                me = get_pt('Me', 'Menton (Me)')
                if go and me:
                    draw.line([go, me], fill="#3b82f6", width=4)

                # 3. Axe Incisif Supérieur (U1a -> U1i) : Rouge
                u1a = get_pt('U1_apex', 'U1a')
                u1i = get_pt('U1_incisal', 'U1_edge', 'U1i')
                if u1a and u1i:
                    draw.line([u1a, u1i], fill="#ef4444", width=4) # Rouge Tailwind

                # 4. Axe Incisif Inférieur (L1a -> L1i) : Vert
                l1a = get_pt('L1_apex', 'L1a')
                l1i = get_pt('L1_incisal', 'L1_edge', 'L1i')
                if l1a and l1i:
                    draw.line([l1a, l1i], fill="#22c55e", width=4) # Vert Tailwind

                # 5. Verticale de Nasion : Jaune pointillé descendant
                n_pt = get_pt('N', 'Nasion (N)')
                if n_pt:
                    self._draw_dashed_line(draw, n_pt, (n_pt[0], img.height), fill="#eab308", width=3, dash_length=20)
                
                img.save(output_path)
                return True
        except Exception as e:
            print(f"Erreur lors du traçage des plans : {e}")
            return False

    def generate(self, analysis_data, patient_data, landmarks=None, archive=False):
        """
        Génère le bilan ortho avec tracé des plans et tableau de mesures COM.
        """
        p_nom = getattr(patient_data, 'nom', 'Inconnu')
        p_prenom = getattr(patient_data, 'prenom', '')
        p_id = getattr(patient_data, 'id', 0)
        
        if landmarks is None:
            landmarks = analysis_data.get('landmarks', [])
        
        now = datetime.now()
        date_str = now.strftime('%d%m%Y')
        filename = f"BILAN_{date_str}_{p_nom.upper()}.pdf"

        if archive:
            p_folder = f"{p_id}_{p_nom.upper()}_{p_prenom.capitalize()}"
            target_dir = os.path.join("static", "patients", p_folder, "Documents")
            os.makedirs(target_dir, exist_ok=True)
            filepath = os.path.join(target_dir, filename)
        else:
            filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2.5*cm, leftMargin=2.5*cm,
            topMargin=7.5*cm, 
            bottomMargin=4*cm
        )

        elements = []
        elements.append(Paragraph("FICHE DE MESURES CLINIQUES", self.styles['ReportTitle']))

        date_display = now.strftime('%d/%m/%Y')
        p_info = f"<b>PATIENT :</b> {p_nom.upper()} {p_prenom} &nbsp;&nbsp;|&nbsp;&nbsp; <b>AGE :</b> -- ans &nbsp;&nbsp;|&nbsp;&nbsp; <b>DATE :</b> {date_display}"
        elements.append(Paragraph(p_info, self.styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

        # --- GESTION DE LA PHOTO RADIO AVEC TRACÉ (Taille Augmentée 10x10 cm) ---
        img_url = analysis_data.get('image_path') or analysis_data.get('image_original_path')
        if img_url:
            local_path = img_url.split("8000/")[-1] if "8000/" in img_url else img_url
            
            if os.path.exists(local_path):
                final_img_path = local_path
                
                if landmarks:
                    marked_filename = f"marked_{os.path.basename(local_path)}"
                    marked_path = os.path.join(self.output_dir, marked_filename)
                    if self._draw_landmarks_on_image(local_path, landmarks, marked_path):
                        final_img_path = marked_path

                im = ReportLabImage(final_img_path, width=10*cm, height=10*cm, kind='proportional')
                im.hAlign = 'CENTER'
                elements.append(im)
                elements.append(Spacer(1, 0.8*cm))

        # --- TABLEAU DES MESURES (Format COM) ---
        data = [["MESURE", "VALEUR NORMALE", "VALEUR DE COMP.", "TRACÉ (Patient)"]]
        
        # Largeur totale = 16cm (A4 = 21cm, Marges = 5cm)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Aligner les noms des mesures à gauche
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]
        
        row_idx = 1
        
        def fill_category(title, cat_key):
            nonlocal row_idx
            # Ligne de Titre de catégorie
            data.append([title, "", "", ""])
            t_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.lightgrey))
            t_style.append(('SPAN', (0, row_idx), (-1, row_idx)))
            t_style.append(('ALIGN', (0, row_idx), (-1, row_idx), 'LEFT'))
            t_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
            row_idx += 1

            results = analysis_data.get('results', {}).get(cat_key, {})
            for k, v in results.items():
                val = v.get('valeur')
                norm = v.get('normale', '-')
                comp = v.get('compensation', '')
                
                is_out = False
                if val is not None:
                    try:
                        val_float = float(val)
                        if val_float < v.get('min', -float('inf')) or val_float > v.get('max', float('inf')):
                            is_out = True
                    except:
                        pass
                
                label = k.replace("_", " ").upper()
                val_str = str(val) if val is not None else "--"
                
                data.append([label, str(norm), str(comp), val_str])
                
                # Coloration de la colonne "TRACÉ" selon le statut
                if is_out:
                    t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.red))
                    t_style.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))
                else:
                    t_style.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.darkgreen))
                    t_style.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))
                
                # Centrer les valeurs
                t_style.append(('ALIGN', (1, row_idx), (-1, row_idx), 'CENTER'))
                row_idx += 1

        # Injection séquentielle COM
        fill_category("ANALYSE DENTAIRE", "analyse_dentaire")
        fill_category("ANALYSE OSSEUSE", "analyse_osseuse")

        # Configuration des largeurs de colonnes
        t = Table(data, colWidths=[5.5*cm, 3.5*cm, 4*cm, 3*cm])
        t.setStyle(TableStyle(t_style))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

        # Diagnostic IA (Gemini)
        ai_diag = analysis_data.get('results', {}).get('ai_diagnostic')
        if ai_diag:
            elements.append(Paragraph("DIAGNOSTIC AUTOMATISÉ (IA) :", 
                ParagraphStyle('H2', parent=self.styles['Normal'], fontName='Helvetica-Bold', textColor=colors.navy)))
            clean_diag = ai_diag.replace("### ", "").replace("**", "")
            elements.append(Paragraph(clean_diag, self.styles['Normal']))

        doc.build(elements, onFirstPage=self._add_background, onLaterPages=self._add_background)
        
        return filepath.replace("\\", "/")