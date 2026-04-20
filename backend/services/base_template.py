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

    def draw_static_elements(self, canvas, doc, config=None, draw_legal_ids=False, user=None):
        """
        Dessine les éléments statiques du Template Mère.
        Supporte : Filigrane, et Header/Footer Premium dynamique.
        Le mode Letterhead ne masque plus le header/footer : il s'intègre en-dessous.
        """
        canvas.saveState()
        
        # 1. Récupération des paramètres
        primary_color = colors.HexColor(config.primary_color) if config else NAVY_BLUE
        secondary_color = colors.HexColor(config.secondary_color) if config else colors.HexColor('#666666')
        accent_color = colors.HexColor(config.accent_color) if config else colors.HexColor('#0055AA')
        
        logo_path = None
        if config and config.logo_path:
            logo_path = os.path.join(self.base_path, "static", "uploads", config.logo_path)
        if not logo_path or not os.path.exists(logo_path):
            logo_path = self.default_logo_path if os.path.exists(self.default_logo_path) else None

        p_width, p_height = doc.pagesize
        
        # 1. Fond de page / Letterhead (Supprimé pour privilégier le rendu natif "Ghost Elite")
        # Le système n'utilise plus d'image de fond statique pour éviter les flous d'impression.
        
        # 2. Watermark Central (Opalescent)
        # Transparent et majestueux
        if config and config.watermark_enabled and logo_path:
            canvas.saveState()
            opacity = config.watermark_opacity if hasattr(config, 'watermark_opacity') else 0.10
            canvas.setFillAlpha(opacity)
            w_size = 9*cm # Légèrement plus grand comme demandé
            canvas.drawImage(logo_path, (p_width - w_size)/2, (p_height - w_size)/2, width=w_size, height=w_size, mask='auto')
            canvas.restoreState()

        # 4. RENDU DU MASTER TEMPLATE (LE SEUL, L'UNIQUE)
        # Appelé inconditionnellement pour normaliser le rendu.
        self._draw_auto_header(canvas, config, logo_path, primary_color, secondary_color, accent_color, p_width, p_height)
        self._draw_footer(canvas, doc, config, draw_legal_ids, user)

        canvas.restoreState()

    def _draw_auto_header(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height):
        """
        En-tête Premium en 3 colonnes:
        Gauche (Français), Centre (Logo), Droite (Arabe).
        """
        y_pos = p_height - 1.5*cm
        
        fr_lines = config.header_lines_fr if config and config.header_lines_fr else ["Dr. Nom Prénom", "Chirurgien Dentiste"]
        ar_lines = config.header_lines_ar if config and config.header_lines_ar else ["د. الإسم الكامل", "طبيب جراح للأسنان"]

        # Centre : Logo
        if logo_path:
            logo_size = 2.8*cm
            canvas.drawImage(logo_path, (p_width - logo_size)/2, p_height - 3.5*cm, width=logo_size, height=logo_size, mask='auto')

        # Police dynamique
        font_name = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        
        # Gauche : FR
        canvas.setFillColor(p_color)
        curr_y = y_pos
        for i, line in enumerate(fr_lines):
            # Utiliser Helvetica pour le français si la police arabe n'est pas multi-langue
            # Mais ici on garde Helvetica pour le FR pour la clarté, sauf si demandé autrement
            canvas.setFont('Helvetica-Bold' if i == 0 else 'Helvetica', 12 if i == 0 else 10)
            if i == 1:
                canvas.setFillColor(s_color)
            canvas.drawString(1.5*cm, curr_y, line)
            curr_y -= 0.55*cm

        # Droite : AR
        canvas.setFont(font_name, 13 if font_name != 'Helvetica' else 11)
        curr_y = y_pos
        for i, line in enumerate(ar_lines):
            if i == 1:
                canvas.setFillColor(s_color)
            else:
                canvas.setFillColor(p_color)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - 1.5*cm, curr_y, prepared_text)
            curr_y -= 0.60*cm

    def _draw_footer(self, canvas, doc, config, draw_legal_ids=False, user=None):
        """Pied de page premium avec adresse et identifiants légaux."""
        p_width, _ = doc.pagesize
        
        # Couleurs
        p_color = config.primary_color if config else "#003380"
        s_color = config.secondary_color if config else "#666666"
        
        # Trait de séparation
        canvas.setStrokeColor(colors.HexColor(p_color))
        canvas.setLineWidth(0.5)
        canvas.line(1.5*cm, 2.5*cm, p_width - 1.5*cm, 2.5*cm)
        
        # Adresse et Téléphone
        font_name = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        canvas.setFont(font_name, 9)
        canvas.setFillColor(colors.HexColor(p_color))
        
        # Nettoyage profond
        def _clean(val):
            return str(val).strip() if val else ""

        address = _clean(config.footer_address) if config else ""
        if not address:
            address = _clean(getattr(user, "adresse_complete", None)) or "Votre adresse de cabinet"
            
        center_x = p_width / 2
        canvas.drawCentredString(center_x, 2.0*cm, self._prepare_arabic(address))
        
        # Gestion des contacts granulaires (Sprint 59)
        contacts_to_show = []
        if config and config.contacts_json:
            c_json = config.contacts_json
            labels = {"fixe": "Tél", "mobile": "Mob", "whatsapp": "WhatsApp", "instagram": "Insta"}
            for key in ["fixe", "mobile", "whatsapp", "instagram"]:
                info = c_json.get(key)
                if isinstance(info, dict) and info.get("enabled") and info.get("value"):
                    contacts_to_show.append(f"{labels[key]} : {info['value'].strip()}")
        
        # Fallback sur footer_phones si contacts_json vide
        if not contacts_to_show:
            phones = _clean(config.footer_phones) if config else ""
            if not phones:
                phones = _clean(getattr(user, "telephone_fixe", None)) or _clean(getattr(user, "telephone_mobile", None)) or "Contactez-nous"
            contacts_to_show = [phones]
            
        contact_str = " / ".join(contacts_to_show)
        
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor(s_color))
        canvas.drawCentredString(center_x, 1.5*cm, self._prepare_arabic(contact_str))
        
        # Identifiants Légaux (ICE, IF, INPE) pour documents financiers
        if draw_legal_ids:
            identifiants = []
            if config:
                c_ice = str(config.ice).strip() if getattr(config, 'ice', None) else ""
                c_if = str(config.if_).strip() if getattr(config, 'if_', None) else ""
                c_inpe = str(config.inpe).strip() if getattr(config, 'inpe', None) else ""
                
                if c_ice: identifiants.append(f"ICE : {c_ice}")
                if c_inpe: identifiants.append(f"INP : {c_inpe}")
                if c_if: identifiants.append(f"IF : {c_if}")
            
            # Fallback sur l'utilisateur si non trouvé dans config
            if not identifiants and getattr(user, "identifiants_legaux", None):
                ids = user.identifiants_legaux
                if ids.get("ice"): identifiants.append(f"ICE : {str(ids['ice']).strip()}")
                if ids.get("inpe"): identifiants.append(f"INP : {str(ids['inpe']).strip()}")
                if ids.get("if"): identifiants.append(f"IF : {str(ids['if']).strip()}")
                
            if identifiants:
                legal_str = "  |  ".join(identifiants)
                canvas.setFont("Helvetica", 7)
                canvas.setFillColor(colors.HexColor("#777777"))
                canvas.drawCentredString(p_width/2, 1.0*cm, legal_str)