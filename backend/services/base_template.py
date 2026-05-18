import os
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from backend.services.qr_service import QRService
from reportlab.platypus import Flowable
from reportlab.lib.utils import ImageReader

# --- DESIGN SYSTEM : SINGLE SOURCE OF TRUTH ---
NAVY_BLUE = colors.HexColor('#003380')

class PinnedCloture(Flowable):
    """
    Flowable spécialisé pour ancrer la phrase de clôture au bas de la dernière page.
    Utilise drawString direct pour garantir la visibilité (pas de clipping par Paragraph).
    """
    def __init__(self, text, style):
        Flowable.__init__(self)
        self.text = text
        self.style = style

    def wrap(self, availWidth, availHeight):
        # Hauteur minimale pour forcer le passage en fin de flow
        return (availWidth, 0.2 * cm)

    @staticmethod
    def _strip_tags(text: str) -> str:
        """Supprime les balises HTML ReportLab (<b>, <u>, etc.) pour drawString."""
        import re
        return re.sub(r'<[^>]+>', '', text)

    def drawOn(self, canvas, x, y, _debug=0, **kwargs):
        if not self.text:
            return

        canvas.saveState()
        # Annulation de la translation du doc.build → référentiel absolu page
        canvas.translate(-x, -y)

        clean_text = self._strip_tags(self.text)

        # Style depuis self.style
        font_name  = getattr(self.style, 'fontName',  'Helvetica-Bold')
        font_size  = getattr(self.style, 'fontSize',  9)
        text_color = getattr(self.style, 'textColor', NAVY_BLUE)

        canvas.setFont(font_name, font_size)
        canvas.setFillColor(text_color)

        # Largeur utile A5 (148mm − 2×15mm marges) = 118mm ≈ 11.8 cm
        usable_w = 11.8 * cm
        left_x   = 1.5 * cm

        # Découpage manuel si texte trop long (wrap simple par caractères)
        avg_char_w = font_size * 0.55   # estimation largeur moy. caractère
        max_chars  = int(usable_w / avg_char_w)

        lines = []
        remaining = clean_text
        while len(remaining) > max_chars:
            # Coupe au dernier espace avant max_chars
            cut = remaining[:max_chars].rfind(' ')
            if cut == -1:
                cut = max_chars
            lines.append(remaining[:cut])
            remaining = remaining[cut:].strip()
        lines.append(remaining)

        # Y de départ : 4.4 cm du bas = bien au-dessus du trait footer (2.5 cm)
        y_start = 4.4 * cm
        line_h  = font_size * 0.045 * cm + 0.38 * cm   # ~leading

        for i, line in enumerate(lines):
            canvas.drawString(left_x, y_start - i * line_h, line)

        canvas.restoreState()



class BaseTemplate:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Assets par défaut
        self.default_logo_path = os.path.join(self.base_path, "static", "assets", "logo.png")
        self.font_path = os.path.join(self.base_path, "static", "assets", "fonts", "Amiri-Regular.ttf")
        self.montserrat_reg = os.path.join(self.base_path, "static", "assets", "fonts", "Montserrat-Regular.ttf")
        self.montserrat_bold = os.path.join(self.base_path, "static", "assets", "fonts", "Montserrat-Bold.ttf")
        
        # Enregistrement des polices
        self._register_fonts()

    def _register_fonts(self):
        # 1. Arabe (Amiri)
        if os.path.exists(self.font_path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', self.font_path))
                self.arabic_font = 'ArabicFont'
            except Exception:
                self.arabic_font = 'Helvetica'
        else:
            self.arabic_font = 'Helvetica'

        # 2. Latin Premium (Montserrat)
        self.premium_font = "Helvetica" # Fallback
        self.premium_bold = "Helvetica-Bold"
        self.header_font = "Helvetica"
        self.header_bold = "Helvetica-Bold"
        
        if os.path.exists(self.montserrat_reg) and os.path.exists(self.montserrat_bold):
            try:
                pdfmetrics.registerFont(TTFont('Montserrat', self.montserrat_reg))
                pdfmetrics.registerFont(TTFont('Montserrat-Bold', self.montserrat_bold))
                self.premium_font = 'Montserrat'
                self.premium_bold = 'Montserrat-Bold'
                
                # Outfit (Elite Header Premium)
                font_dir = os.path.dirname(self.montserrat_reg)
                pdfmetrics.registerFont(TTFont('Outfit', os.path.join(font_dir, 'Outfit-Regular.ttf')))
                pdfmetrics.registerFont(TTFont('Outfit-Bold', os.path.join(font_dir, 'Outfit-Bold.ttf')))
                self.header_font = 'Outfit'
                self.header_bold = 'Outfit-Bold'

                # Inter Tight
                inter_reg = os.path.join(font_dir, 'InterTight-Regular.ttf')
                inter_bold = os.path.join(font_dir, 'InterTight-Bold.ttf')
                if os.path.exists(inter_reg) and os.path.exists(inter_bold):
                    pdfmetrics.registerFont(TTFont('InterTight', inter_reg))
                    pdfmetrics.registerFont(TTFont('InterTight-Bold', inter_bold))
                    
                # Playfair Display
                playfair_reg = os.path.join(font_dir, 'PlayfairDisplay-Regular.ttf')
                playfair_bold = os.path.join(font_dir, 'PlayfairDisplay-Bold.ttf')
                if os.path.exists(playfair_reg) and os.path.exists(playfair_bold):
                    pdfmetrics.registerFont(TTFont('PlayfairDisplay', playfair_reg))
                    pdfmetrics.registerFont(TTFont('PlayfairDisplay-Bold', playfair_bold))

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur enregistrement Montserrat/Premium Fonts: {e}")
                self.header_font = self.premium_font
                self.header_bold = self.premium_bold

    def update_active_fonts(self, config):
        """
        Met à jour dynamiquement les polices actives du template en fonction de la configuration de l'utilisateur.
        """
        font_fr = self._get_val(config, 'font_fr', 'inter')
        
        # Mappings des polices pré-enregistrées
        if font_fr == 'outfit':
            self.premium_font = 'Outfit'
            self.premium_bold = 'Outfit-Bold'
            self.header_font = 'Outfit'
            self.header_bold = 'Outfit-Bold'
        elif font_fr == 'inter':
            # Fallback à Helvetica ou Montserrat si InterTight n'est pas présent
            try:
                pdfmetrics.getFont('InterTight')
                self.premium_font = 'InterTight'
                self.premium_bold = 'InterTight-Bold'
                self.header_font = 'InterTight'
                self.header_bold = 'InterTight-Bold'
            except Exception:
                self.premium_font = 'Montserrat'
                self.premium_bold = 'Montserrat-Bold'
                self.header_font = 'Outfit'
                self.header_bold = 'Outfit-Bold'
        elif font_fr == 'playfair':
            try:
                pdfmetrics.getFont('PlayfairDisplay')
                self.premium_font = 'PlayfairDisplay'
                self.premium_bold = 'PlayfairDisplay-Bold'
                self.header_font = 'PlayfairDisplay'
                self.header_bold = 'PlayfairDisplay-Bold'
            except Exception:
                self.premium_font = 'Montserrat'
                self.premium_bold = 'Montserrat-Bold'
                self.header_font = 'Outfit'
                self.header_bold = 'Outfit-Bold'
        else:
            self.premium_font = 'Montserrat'
            self.premium_bold = 'Montserrat-Bold'
            self.header_font = 'Outfit'
            self.header_bold = 'Outfit-Bold'

    def _prepare_arabic(self, text):
        if not text: return ""
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)

    def _get_val(self, obj, key, default=None):
        """Récupère une valeur que l'objet soit un dict ou un modèle SQLAlchemy."""
        if obj is None: return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def get_adaptive_font_size(text, font_name, base_fs, max_width, min_fs=6.5):
        """
        Calcule la taille de police optimale pour faire tenir un texte sur une seule ligne.
        Utilise pdfmetrics.stringWidth pour une précision absolue.
        """
        from reportlab.pdfbase.pdfmetrics import stringWidth
        import re
        
        # Nettoyage des balises HTML pour le calcul de largeur
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        fs = base_fs
        while stringWidth(clean_text, font_name, fs) > max_width and fs > min_fs:
            fs -= 0.5
        return fs

    def get_adaptive_style(self, base_style, text, max_width, min_fs=6.5):
        """Retourne un nouveau ParagraphStyle avec une fontSize adaptée."""
        from reportlab.lib.styles import ParagraphStyle
        
        new_fs = self.get_adaptive_font_size(
            text, 
            base_style.fontName, 
            base_style.fontSize, 
            max_width,
            min_fs=min_fs
        )
        
        return ParagraphStyle(
            name=f"{base_style.name}_adaptive",
            parent=base_style,
            fontSize=new_fs,
            leading=new_fs * 1.2
        )

    def draw_static_elements(self, canvas, doc, config=None, draw_legal_ids=False, user=None):
        """
        Dessine les éléments statiques du Template Mère.
        Supporte : Filigrane, et Header/Footer Premium dynamique.
        Le mode Letterhead ne masque plus le header/footer : il s'intègre en-dessous.
        """
        canvas.saveState()
        
        # 1. Récupération des paramètres
        p_color_hex = self._get_val(config, 'primary_color', '#003380')
        s_color_hex = self._get_val(config, 'secondary_color', '#666666')
        a_color_hex = self._get_val(config, 'accent_color', '#0055AA')

        primary_color = colors.HexColor(p_color_hex)
        secondary_color = colors.HexColor(s_color_hex)
        accent_color = colors.HexColor(a_color_hex)
        
        logo_filename = self._get_val(config, 'logo_path')
        logo_path = None
        if logo_filename:
            logo_path = os.path.join(self.base_path, "static", "uploads", logo_filename)
        if not logo_path or not os.path.exists(logo_path):
            logo_path = self.default_logo_path if os.path.exists(self.default_logo_path) else None

        p_width, p_height = doc.pagesize
        
        # 1. Fond de page / Letterhead (Supprimé pour privilégier le rendu natif "Ghost Elite")
        # Le système n'utilise plus d'image de fond statique pour éviter les flous d'impression.
        
        # Récupération de la mise en page choisie
        selected_template = self._get_val(config, 'selected_template', 'classic')
        
        # Dessin du sidebar s'il est sélectionné
        if selected_template == 'sidebar':
            canvas.saveState()
            canvas.setFillColor(colors.HexColor('#f8fafc'))
            canvas.rect(0, 0, 0.8*cm, p_height, fill=True, stroke=False)
            canvas.setStrokeColor(primary_color)
            canvas.setLineWidth(2)
            canvas.line(0.8*cm, 0, 0.8*cm, p_height)
            canvas.restoreState()

        # 2. Watermark Central (Opalescent)
        # Transparent et majestueux
        watermark_enabled = self._get_val(config, 'watermark_enabled', False)
        if watermark_enabled and logo_path:
            canvas.saveState()
            opacity = self._get_val(config, 'watermark_opacity', 0.10)
            canvas.setFillAlpha(opacity)
            w_size = 9*cm # Légèrement plus grand comme demandé
            canvas.drawImage(logo_path, (p_width - w_size)/2, (p_height - w_size)/2, width=w_size, height=w_size, mask='auto')
            canvas.restoreState()

        # 4. RENDU DU MASTER TEMPLATE (LE SEUL, L'UNIQUE)
        # Appelé inconditionnellement pour normaliser le rendu.
        self._draw_auto_header(canvas, config, logo_path, primary_color, secondary_color, accent_color, p_width, p_height)
        self._draw_qr_code(canvas, doc, config, user, primary_color)
        self._draw_footer(canvas, doc, config, draw_legal_ids, user)

        canvas.restoreState()

    def _draw_auto_header(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height):
        """
        En-tête Elite : Répartit et applique le design selon selected_template.
        """
        selected_template = self._get_val(config, 'selected_template', 'classic')
        
        fr_lines = self._get_val(config, 'header_lines_fr')
        if not fr_lines: fr_lines = ["Dr. Nom Prénom", "Chirurgien Dentiste"]
        
        ar_lines = self._get_val(config, 'header_lines_ar')
        if not ar_lines: ar_lines = ["د. الإسم الكامل", "طبيب جراح للأسنان"]

        # Échelle globale de l'en-tête (Elite Scaler L180)
        h_scale = self._get_val(config, 'header_scale', 1.0)

        if selected_template == 'elite':
            self._draw_header_elite(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)
        elif selected_template == 'sidebar':
            self._draw_header_sidebar(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)
        elif selected_template == 'royal':
            self._draw_header_royal(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)
        elif selected_template == 'prestige':
            self._draw_header_prestige(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)
        elif selected_template == 'minimal':
            self._draw_header_minimal(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)
        else: # classic
            self._draw_header_classic(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)

    def _draw_header_classic(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Haute Couture (Classique) : Elegance, double lines, serif-like structure
        margin = 1.5*cm
        y_top = p_height - 1.8*cm
        
        # Double top border
        canvas.saveState()
        canvas.setStrokeColor(p_color)
        canvas.setLineWidth(1.5)
        canvas.line(margin, p_height - 0.8*cm, p_width - margin, p_height - 0.8*cm)
        canvas.setLineWidth(0.5)
        canvas.line(margin, p_height - 0.95*cm, p_width - margin, p_height - 0.95*cm)
        canvas.restoreState()

        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        column_w = (p_width - 2*margin) / 3.0
        line_height = 0.45*cm * lh_scale

        # French Text (Left)
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 26 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 26 * hf_scale

        curr_y = y_top
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(p_color)
            canvas.setFont(font, common_fs)
            canvas.drawString(margin, curr_y, line)
            curr_y -= line_height

        # Centered Logo
        if logo_path:
            logo_size = 2.2*cm * hl_scale
            text_center_y = y_top - ((len(fr_lines) - 1) * line_height) / 2.0 + 0.08*cm
            logo_y = text_center_y - (logo_size / 2.0)
            canvas.drawImage(logo_path, (p_width - logo_size)/2, logo_y, width=logo_size, height=logo_size, mask='auto')

        # Arabic Text (Right)
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (28 if font_ar != 'Helvetica' else 20) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (28 if font_ar != 'Helvetica' else 20) * hf_scale

        curr_y = y_top
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - margin, curr_y, prepared_text)
            curr_y -= line_height

        # Elegant bottom divider (Double line with diamond)
        bottom_y = p_height - 3.8*cm
        canvas.saveState()
        canvas.setStrokeColor(p_color)
        canvas.setLineWidth(0.5)
        # Left line
        canvas.line(margin, bottom_y, p_width/2 - 0.4*cm, bottom_y)
        # Right line
        canvas.line(p_width/2 + 0.4*cm, bottom_y, p_width - margin, bottom_y)
        
        # Diamond
        canvas.setFillColor(a_color)
        canvas.setFont(self.header_bold, 6)
        canvas.drawCentredString(p_width/2, bottom_y - 0.08*cm, "◆")
        canvas.restoreState()

    def _draw_header_elite(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Ghost Elite (Signature): Modern floating card effect with tech accent
        margin = 1.5*cm
        
        # Floating card background
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#F8FAFC')) # Very light slate
        canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
        canvas.setLineWidth(0.5)
        # Card from left to right margin
        card_h = 2.8*cm
        card_y = p_height - margin - card_h + 0.3*cm
        canvas.roundRect(margin, card_y, p_width - 2*margin, card_h, radius=0.3*cm, fill=True, stroke=True)
        
        # Tech accent line on the left of the card
        canvas.setFillColor(a_color)
        canvas.roundRect(margin, card_y, 0.15*cm, card_h, radius=0.15*cm, fill=True, stroke=False)
        canvas.restoreState()

        # Content inside the card
        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        inner_margin = margin + 0.6*cm
        column_w = (p_width - 2*inner_margin) / 3.0
        line_height = 0.42*cm * lh_scale
        
        y_top = card_y + card_h - 0.6*cm

        # French Text
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 24 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 24 * hf_scale

        curr_y = y_top
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(p_color)
            canvas.setFont(font, common_fs)
            canvas.drawString(inner_margin, curr_y, line)
            curr_y -= line_height

        # Centered Logo
        if logo_path:
            logo_size = 2.0*cm * hl_scale
            text_center_y = card_y + card_h/2.0
            logo_y = text_center_y - (logo_size / 2.0)
            canvas.drawImage(logo_path, (p_width - logo_size)/2, logo_y, width=logo_size, height=logo_size, mask='auto')

        # Arabic Text
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (26 if font_ar != 'Helvetica' else 18) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (26 if font_ar != 'Helvetica' else 18) * hf_scale

        curr_y = y_top
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - inner_margin, curr_y, prepared_text)
            curr_y -= line_height

    def _draw_header_sidebar(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Clinique Technique (Latéral): Left solid column, strict grid
        margin = 1.5*cm
        sidebar_w = 0.8*cm

        canvas.saveState()
        # Solid sidebar
        canvas.setFillColor(p_color)
        canvas.rect(0, 0, sidebar_w, p_height, fill=True, stroke=False)
        # Accent thin line next to it
        canvas.setFillColor(a_color)
        canvas.rect(sidebar_w, 0, 0.1*cm, p_height, fill=True, stroke=False)
        
        # Top right "Barcode" element for a clinical/tech feel
        canvas.setFillColor(colors.HexColor('#CBD5E1'))
        bx = p_width - margin - 2*cm
        by = p_height - 1.2*cm
        widths = [2, 1, 3, 1, 2, 4, 1, 2]
        for w in widths:
            canvas.rect(bx, by, w, 0.5*cm, fill=True, stroke=False)
            bx += w + 2
        
        canvas.restoreState()

        y_top = p_height - 1.8*cm
        content_x = sidebar_w + 1.2*cm
        column_w = (p_width - content_x - margin) / 2.0 - 0.5*cm

        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        line_height = 0.42*cm * lh_scale

        logo_size = 2.0*cm * hl_scale
        if logo_path:
            fr_x = content_x + logo_size + 0.6*cm
        else:
            fr_x = content_x

        # French Text
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 24 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 24 * hf_scale

        text_center_y = y_top - ((len(fr_lines) - 1) * line_height) / 2.0 + 0.08*cm
        if logo_path:
            logo_y = text_center_y - (logo_size / 2.0)
            canvas.drawImage(logo_path, content_x, logo_y, width=logo_size, height=logo_size, mask='auto')

        curr_y = y_top
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(p_color)
            canvas.setFont(font, common_fs)
            canvas.drawString(fr_x, curr_y, line)
            curr_y -= line_height

        # Arabic Text
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (26 if font_ar != 'Helvetica' else 18) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (26 if font_ar != 'Helvetica' else 18) * hf_scale

        curr_y = y_top
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - margin, curr_y, prepared_text)
            curr_y -= line_height
            
        # Horizontal delimiter
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
        canvas.setLineWidth(0.5)
        canvas.line(content_x, p_height - 3.8*cm, p_width - margin, p_height - 3.8*cm)
        canvas.restoreState()

    def _draw_header_royal(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Royal Prestige (Centré): Centered, elegant, regal
        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        # Background very subtle pattern or lines (faint top border)
        canvas.saveState()
        canvas.setStrokeColor(a_color)
        canvas.setLineWidth(2)
        canvas.line(0, p_height, p_width, p_height)
        canvas.restoreState()

        # Logo at top center
        logo_size = 2.2*cm * hl_scale
        y_start = p_height - 1.0*cm
        if logo_path:
            logo_y = y_start - logo_size
            canvas.drawImage(logo_path, (p_width - logo_size)/2, logo_y, width=logo_size, height=logo_size, mask='auto')
            y_start = logo_y - 0.5*cm
        
        line_height = 0.45*cm * lh_scale
        column_w = p_width - 4.0*cm

        # French
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 26 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 26 * hf_scale

        curr_y = y_start
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(p_color)
            canvas.setFont(font, common_fs)
            canvas.drawCentredString(p_width/2, curr_y, line)
            curr_y -= line_height

        # Royal Divider
        curr_y -= 0.1*cm
        canvas.saveState()
        canvas.setStrokeColor(p_color)
        canvas.setLineWidth(0.5)
        # Line - dot - diamond - dot - Line
        canvas.line(p_width/2 - 3.0*cm, curr_y, p_width/2 - 0.8*cm, curr_y)
        canvas.line(p_width/2 + 0.8*cm, curr_y, p_width/2 + 3.0*cm, curr_y)
        
        canvas.setFillColor(a_color)
        canvas.circle(p_width/2 - 0.5*cm, curr_y, 0.05*cm, fill=True, stroke=False)
        canvas.circle(p_width/2 + 0.5*cm, curr_y, 0.05*cm, fill=True, stroke=False)
        
        canvas.setFont(self.header_bold, 8)
        canvas.drawCentredString(p_width/2, curr_y - 0.1*cm, "✦")
        canvas.restoreState()
        
        curr_y -= 0.5*cm

        # Arabic
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (28 if font_ar != 'Helvetica' else 20) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (28 if font_ar != 'Helvetica' else 20) * hf_scale

        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawCentredString(p_width/2, curr_y, prepared_text)
            curr_y -= line_height

    def _draw_header_prestige(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Nuit Noire (Luxe Sombre): Dark luxury block at the top
        block_h = 4.2*cm
        canvas.saveState()
        canvas.setFillColor(p_color)
        canvas.rect(0, p_height - block_h, p_width, block_h, fill=True, stroke=False)
        
        # Accent thin line at the bottom of the dark block
        canvas.setFillColor(a_color)
        canvas.rect(0, p_height - block_h - 0.1*cm, p_width, 0.1*cm, fill=True, stroke=False)
        
        # Inner thin gold frame
        canvas.setStrokeColor(a_color)
        canvas.setLineWidth(0.5)
        canvas.rect(0.3*cm, p_height - block_h + 0.3*cm, p_width - 0.6*cm, block_h - 0.6*cm, fill=False, stroke=True)
        canvas.restoreState()

        margin = 1.5*cm
        y_top = p_height - 1.5*cm
        column_w = (p_width - 2*margin) / 3.0

        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        line_height = 0.45*cm * lh_scale

        # French
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 26 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w - 0.2*cm))
        common_fs = min(fs_list) if fs_list else 26 * hf_scale

        curr_y = y_top
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            # First line is Accent color, others are white
            canvas.setFillColor(a_color if i == 0 else colors.white)
            canvas.setFont(font, common_fs)
            canvas.drawString(margin, curr_y, line)
            curr_y -= line_height

        # Centered Logo inside a white circle shield
        if logo_path:
            logo_size = 2.0*cm * hl_scale
            text_center_y = y_top - ((len(fr_lines) - 1) * line_height) / 2.0 + 0.08*cm
            logo_y = text_center_y - (logo_size / 2.0)
            
            canvas.saveState()
            canvas.setFillColor(colors.white)
            canvas.setStrokeColor(a_color)
            canvas.setLineWidth(1)
            canvas.circle(p_width/2, text_center_y, logo_size/2 + 0.2*cm, fill=True, stroke=True)
            canvas.restoreState()
            
            canvas.drawImage(logo_path, (p_width - logo_size)/2, logo_y, width=logo_size, height=logo_size, mask='auto')

        # Arabic
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (28 if font_ar != 'Helvetica' else 20) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w - 0.2*cm))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (28 if font_ar != 'Helvetica' else 20) * hf_scale

        curr_y = y_top
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(a_color if i == 0 else colors.white)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - margin, curr_y, prepared_text)
            curr_y -= line_height

    def _draw_header_minimal(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Épure Zen (Minimaliste): Lots of whitespace, muted tones, simple layout
        margin = 2.0*cm
        y_top = p_height - 1.8*cm

        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        line_height = 0.40*cm * lh_scale

        logo_size = 1.4*cm * hl_scale
        if logo_path:
            fr_x = margin + logo_size + 0.6*cm
        else:
            fr_x = margin

        column_w = (p_width - fr_x - margin) / 2.0 - 0.5*cm

        # French
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 20 * hf_scale # Smaller fonts for minimalism
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 20 * hf_scale

        if logo_path:
            text_center_y = y_top - ((len(fr_lines) - 1) * line_height) / 2.0 + 0.08*cm
            logo_y = text_center_y - (logo_size / 2.0)
            canvas.drawImage(logo_path, margin, logo_y, width=logo_size, height=logo_size, mask='auto')

        curr_y = y_top
        text_color = colors.HexColor('#334155') # Slate 700
        
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(text_color)
            canvas.setFont(font, common_fs)
            canvas.drawString(fr_x, curr_y, line)
            curr_y -= line_height

        # Arabic
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (22 if font_ar != 'Helvetica' else 16) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (22 if font_ar != 'Helvetica' else 16) * hf_scale

        curr_y = y_top
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(text_color)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - margin, curr_y, prepared_text)
            curr_y -= line_height

        # Single minimal accent line at the bottom, centered and very short
        canvas.saveState()
        canvas.setStrokeColor(a_color)
        canvas.setLineWidth(1)
        canvas.line(p_width/2 - 1.5*cm, p_height - 3.2*cm, p_width/2 + 1.5*cm, p_height - 3.2*cm)
        canvas.restoreState()

    def _draw_footer(self, canvas, doc, config, draw_legal_ids=False, user=None):
        """Pied de page Elite Dynamique (v6.4)."""
        p_width, _ = doc.pagesize
        margin = 1.5 * cm
        
        f_font_scale = self._get_val(config, 'footer_font_scale', 1.0)
        f_qr_scale = self._get_val(config, 'footer_qr_scale', 1.0)
        f_lh_scale = self._get_val(config, 'footer_line_height', 1.0)

        qr_size = 1.6 * cm * f_qr_scale
        
        # Calcul de la zone de texte : de la marge gauche au début du QR
        # Cela garantit un centrage parfait dans l'espace restant
        qr_x_start = p_width - margin - qr_size
        text_zone_w = qr_x_start - margin
        text_center_x = margin + (text_zone_w / 2.0)
        
        p_color = self._get_val(config, 'primary_color', '#003380')
        s_color = self._get_val(config, 'secondary_color', '#666666')
        
        # Trait de séparation épuré
        canvas.setStrokeColor(colors.HexColor(p_color))
        canvas.setLineWidth(0.5)
        canvas.line(margin, 2.5*cm, p_width - margin, 2.5*cm)
        
        # 1. Adresse
        address = self._get_val(config, 'footer_address')
        if not address:
            address = self._get_val(user, "adresse_complete") or "Votre adresse de cabinet"
            
        fs_addr = self.get_adaptive_font_size(address, self.premium_font, 9 * f_font_scale, text_zone_w - 0.4*cm)
        canvas.setFont(self.premium_font, fs_addr)
        canvas.setFillColor(colors.HexColor(p_color))
        
        # Centrage vertical avec interligne adaptatif
        addr_y = (1.45 + 0.40 * f_lh_scale) * cm
        canvas.drawCentredString(text_center_x, addr_y, self._prepare_arabic(address))
        
        # 2. Contacts (Interligne serré v6.6)
        contacts_to_show = []
        c_json = self._get_val(config, 'contacts_json')
        if c_json:
            labels = {"fixe": "Tél", "mobile": "Mob", "whatsapp": "WhatsApp", "instagram": "Insta"}
            for key in ["fixe", "mobile", "whatsapp", "instagram"]:
                info = c_json.get(key)
                if isinstance(info, dict) and info.get("enabled") and info.get("value"):
                    contacts_to_show.append(f"{labels[key]} : {info['value'].strip()}")
        
        if not contacts_to_show:
            phones = self._get_val(config, 'footer_phones') or self._get_val(user, "telephone_mobile") or "Contact"
            contacts_to_show = [phones]
            
        contact_str = " / ".join(contacts_to_show)
        fs_contact = self.get_adaptive_font_size(contact_str, self.premium_font, 8 * f_font_scale, text_zone_w - 0.4*cm)
        canvas.setFont(self.premium_font, fs_contact)
        canvas.setFillColor(colors.HexColor(s_color))
        
        # Centrage vertical
        canvas.drawCentredString(text_center_x, 1.45*cm, self._prepare_arabic(contact_str))
        
        # 3. Identifiants Légaux
        if draw_legal_ids:
            identifiants = []
            if config:
                c_ice = str(self._get_val(config, 'ice', "")).strip()
                c_if = str(self._get_val(config, 'if_', "")).strip()
                c_inpe = str(self._get_val(config, 'inpe', "")).strip()
                if c_ice: identifiants.append(f"ICE : {c_ice}")
                if c_inpe: identifiants.append(f"INP : {c_inpe}")
                if c_if: identifiants.append(f"IF : {c_if}")
            
            if not identifiants and getattr(user, "identifiants_legaux", None):
                ids = user.identifiants_legaux
                if ids.get("ice"): identifiants.append(f"ICE : {str(ids['ice']).strip()}")
                if ids.get("inpe"): identifiants.append(f"INP : {str(ids['inpe']).strip()}")
                if ids.get("if"): identifiants.append(f"IF : {str(ids['if']).strip()}")
                
            if identifiants:
                legal_str = "  |  ".join(identifiants)
                fs_legal = self.get_adaptive_font_size(legal_str, self.premium_font, 7.5 * f_font_scale, text_zone_w - 0.4*cm)
                canvas.setFont(self.premium_font, fs_legal)
                canvas.setFillColor(colors.HexColor("#777777"))
                
                # Centrage vertical
                legal_y = (1.45 - 0.35 * f_lh_scale) * cm
                canvas.drawCentredString(text_center_x, legal_y, legal_str)

    def _draw_qr_code(self, canvas, doc, config, user, p_color):
        """Dessine le QR Code stratégique configuré par le docteur."""
        qr_enabled = self._get_val(config, 'qr_code_enabled', False)
        if not qr_enabled: return

        qr_type = self._get_val(config, 'qr_code_type', 'VCARD')
        qr_value = self._get_val(config, 'qr_code_value', '')
        qr_color_hex = self._get_val(config, 'qr_code_color') or self._get_val(config, 'primary_color', '#003380')
        qr_label = self._get_val(config, 'qr_code_label', '')

        # Détermination du contenu du QR
        qr_data = qr_value
        if qr_type == 'VCARD' and not qr_value:
            # Génération automatique de la vCard à partir du profil
            name = self._get_val(config, 'nom_praticien') or self._get_val(user, 'nom_complet') or "Docteur"
            phone = self._get_val(config, 'footer_phones') or self._get_val(user, 'telephone_mobile') or ""
            if "/" in phone:
                phone = phone.split("/")[0].strip()
            email = getattr(user, 'email', '')
            address = self._get_val(config, 'footer_address') or self._get_val(user, 'adresse_complete', '')
            qr_data = QRService.generate_vcard(name, phone, email, address=address)
        elif qr_type == 'INSTAGRAM' and qr_value:
            if not qr_value.startswith('http'):
                qr_data = f"https://instagram.com/{qr_value.replace('@', '')}"
        elif qr_type == 'VALIDATION':
            # Mode validation : pointe vers le portail de vérification (URL de base + ID document)
            b_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            qr_data = f"{b_url}/verify/{getattr(doc, 'doc_id', 'DOC-TEMP')}"
        elif qr_type == 'PAYMENT':
            # Suivi de paiement / Progression (nouveau mode Elite v4.2)
            b_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            qr_data = f"{b_url}/track/{getattr(doc, 'doc_id', 'DOC-TEMP')}"
        elif qr_type == 'WHATSAPP':
            # Contact direct WhatsApp (v4.2) - Priorité absolue à qr_value
            # car c'est là que le docteur saisit le numéro spécifique au QR
            phone = qr_value
            
            if not phone:
                c_json = self._get_val(config, 'contacts_json')
                if isinstance(c_json, dict) and c_json.get("whatsapp", {}).get("enabled"):
                    phone = c_json.get("whatsapp", {}).get("value") or ""
            
            if not phone:
                phone = self._get_val(config, 'footer_phones') or self._get_val(user, 'telephone_mobile') or ""
            
            # Si on a plusieurs numéros (ex: "06.. / 05.."), on prend le premier
            if "/" in phone:
                phone = phone.split("/")[0].strip()
                
            # Message bilingue pour une expérience patient optimale (Prise de RDV)
            msg = "Bonjour Dr, je souhaite prendre rendez-vous. / السلام عليكم دكتور، أود حجز moعد."
            qr_data = QRService.generate_whatsapp_url(phone, msg)
        elif qr_type == 'LOCATION':
            # Localisation Google Maps (v4.2)
            address = self._get_val(config, 'footer_address') or self._get_val(user, 'adresse_complete', '')
            qr_data = QRService.generate_maps_url(address)
        elif qr_type == 'WEBSITE' and qr_value:
            qr_data = qr_value if qr_value.startswith('http') else f"https://{qr_value}"

        if not qr_data: return

        # Génération du QR avec sceau "Elite" ou Logo réel au centre
        try:
            logo_filename = self._get_val(config, 'logo_path')
            actual_logo_path = None
            if logo_filename:
                actual_logo_path = os.path.join(self.base_path, "static", "uploads", logo_filename)
            
            # Fallback sur logo par défaut si configuré mais inexistant
            if actual_logo_path and not os.path.exists(actual_logo_path):
                actual_logo_path = self.default_logo_path if os.path.exists(self.default_logo_path) else None

            qr_style = self._get_val(config, 'qr_code_style', 'dots')
            qr_bytes = QRService.generate_qr_bytes(qr_data, color=qr_color_hex, box_size=5, add_logo=True, logo_path=actual_logo_path, qr_style=qr_style)
            if qr_bytes:
                p_width, _ = doc.pagesize
                f_qr_scale = self._get_val(config, 'footer_qr_scale', 1.0)
                qr_size = 1.6 * cm * f_qr_scale
                
                # Colonne Droite (Action/Interaction) : Ancré en bas à droite
                x_pos = p_width - 1.5 * cm - qr_size
                y_pos = 0.8 * cm

                # ImageReader est obligatoire pour que ReportLab accepte un BytesIO
                canvas.drawImage(ImageReader(qr_bytes), x_pos, y_pos, width=qr_size, height=qr_size, mask='auto')

                # Label "Scannez pour nous écrire" : placé proprement sous ou à gauche du QR
                if qr_label:
                    canvas.setFont(self.premium_bold, 6)
                    canvas.setFillColor(colors.HexColor("#334155"))  # Slate-700
                    # On centre le label exactement au milieu du QR Code, en dessous
                    canvas.drawCentredString(x_pos + (qr_size / 2), y_pos - 0.3 * cm, self._prepare_arabic(qr_label))
        except Exception as e:
            # Ne jamais bloquer la génération du PDF pour un QR défaillant
            import logging
            logging.getLogger(__name__).warning(f"QR Code ignoré (erreur rendu): {e}")