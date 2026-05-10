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
        
        # Enregistrement des polices
        self._register_fonts()

    def _register_fonts(self):
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

    def _get_val(self, obj, key, default=None):
        """Récupère une valeur que l'objet soit un dict ou un modèle SQLAlchemy."""
        if obj is None: return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

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
        En-tête Premium en 3 colonnes:
        Gauche (Français), Centre (Logo), Droite (Arabe).
        """
        y_pos = p_height - 1.5*cm
        
        fr_lines = self._get_val(config, 'header_lines_fr')
        if not fr_lines: fr_lines = ["Dr. Nom Prénom", "Chirurgien Dentiste"]
        
        ar_lines = self._get_val(config, 'header_lines_ar')
        if not ar_lines: ar_lines = ["د. الإسم الكامل", "طبيب جراح للأسنان"]

        # Centre : Logo
        if logo_path:
            logo_size = 2.8*cm
            canvas.drawImage(logo_path, (p_width - logo_size)/2, p_height - 3.5*cm, width=logo_size, height=logo_size, mask='auto')

        # Police dynamique
        font_name = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        
        # Gauche : FR
        curr_y = y_pos
        for i, line in enumerate(fr_lines):
            canvas.setFillColor(p_color)
            canvas.setFont('Helvetica-Bold' if i == 0 else 'Helvetica', 12 if i == 0 else 10)
            canvas.drawString(1.5*cm, curr_y, line)
            curr_y -= 0.55*cm

        # Droite : AR
        canvas.setFont(font_name, 13 if font_name != 'Helvetica' else 11)
        curr_y = y_pos
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - 1.5*cm, curr_y, prepared_text)
            curr_y -= 0.60*cm

    def _draw_footer(self, canvas, doc, config, draw_legal_ids=False, user=None):
        """Pied de page premium Architecture 2 Colonnes (70% Texte / 30% QR)."""
        p_width, _ = doc.pagesize
        left_margin = 1.5 * cm
        
        # Couleurs
        p_color = self._get_val(config, 'primary_color', '#003380')
        s_color = self._get_val(config, 'secondary_color', '#666666')
        
        # Trait de séparation
        canvas.setStrokeColor(colors.HexColor(p_color))
        canvas.setLineWidth(0.5)
        canvas.line(left_margin, 2.5*cm, p_width - left_margin, 2.5*cm)
        
        # Colonne Gauche (Texte) : Centrée dans les 70% d'espace libre
        font_name = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        center_text_x = (p_width / 2) - 1.0 * cm
        
        address = self._get_val(config, 'footer_address')
        if not address:
            address = self._get_val(user, "adresse_complete") or "Votre adresse de cabinet"
            
        canvas.setFont(font_name, 9)
        canvas.setFillColor(colors.HexColor(p_color))
        canvas.drawCentredString(center_text_x, 2.0*cm, self._prepare_arabic(address))
        
        # Contacts
        contacts_to_show = []
        c_json = self._get_val(config, 'contacts_json')
        if c_json:
            labels = {"fixe": "Tél", "mobile": "Mob", "whatsapp": "WhatsApp", "instagram": "Insta"}
            for key in ["fixe", "mobile", "whatsapp", "instagram"]:
                info = c_json.get(key)
                if isinstance(info, dict) and info.get("enabled") and info.get("value"):
                    contacts_to_show.append(f"{labels[key]} : {info['value'].strip()}")
        
        if not contacts_to_show:
            phones = self._get_val(config, 'footer_phones')
            if not phones:
                phones = self._get_val(user, "telephone_fixe") or self._get_val(user, "telephone_mobile") or "Contactez-nous"
            contacts_to_show = [phones]
            
        contact_str = " / ".join(contacts_to_show)
        
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor(s_color))
        canvas.drawCentredString(center_text_x, 1.5*cm, self._prepare_arabic(contact_str))
        
        # Identifiants Légaux
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
                canvas.setFont("Helvetica", 7)
                canvas.setFillColor(colors.HexColor("#777777"))
                canvas.drawCentredString(center_text_x, 1.1*cm, legal_str)

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
            email = getattr(user, 'email', '')
            address = self._get_val(config, 'footer_address') or self._get_val(user, 'adresse_complete', '')
            qr_data = QRService.generate_vcard(name, phone, email, address=address)
        elif qr_type == 'INSTAGRAM' and qr_value:
            if not qr_value.startswith('http'):
                qr_data = f"https://instagram.com/{qr_value.replace('@', '')}"
        elif qr_type == 'VALIDATION':
            # Mode validation : pointe vers le portail de vérification (URL de base + ID document)
            qr_data = f"https://digitalcrown.ai/verify/{getattr(doc, 'doc_id', 'DOC-TEMP')}"
        elif qr_type == 'PAYMENT':
            # Suivi de paiement / Progression (nouveau mode Elite v4.2)
            qr_data = f"https://digitalcrown.ai/track/{getattr(doc, 'doc_id', 'DOC-TEMP')}"
        elif qr_type == 'WHATSAPP':
            # Contact direct WhatsApp (v4.2)
            phone = self._get_val(config, 'footer_phones') or self._get_val(user, 'telephone_mobile') or ""
            msg = "Bonjour Dr, je souhaite confirmer mon rendez-vous."
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

            qr_bytes = QRService.generate_qr_bytes(qr_data, color=qr_color_hex, box_size=5, add_logo=True, logo_path=actual_logo_path)
            if qr_bytes:
                p_width, _ = doc.pagesize
                qr_size = 1.6 * cm
                # Colonne Droite (Action/Interaction) : Ancré en bas à droite
                x_pos = p_width - 1.5 * cm - qr_size
                y_pos = 0.8 * cm

                # ImageReader est obligatoire pour que ReportLab accepte un BytesIO
                canvas.drawImage(ImageReader(qr_bytes), x_pos, y_pos, width=qr_size, height=qr_size, mask='auto')

                # Label "Scannez pour nous écrire" : placé proprement sous ou à gauche du QR
                if qr_label:
                    canvas.setFont("Helvetica-Bold", 6)
                    canvas.setFillColor(colors.HexColor("#334155"))  # Slate-700
                    # On centre le label exactement au milieu du QR Code, en dessous
                    canvas.drawCentredString(x_pos + (qr_size / 2), y_pos - 0.3 * cm, self._prepare_arabic(qr_label))
        except Exception as e:
            # Ne jamais bloquer la génération du PDF pour un QR défaillant
            import logging
            logging.getLogger(__name__).warning(f"QR Code ignoré (erreur rendu): {e}")