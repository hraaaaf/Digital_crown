"""
Générateur CSS WeasyPrint pour les documents PDF de Digital Crown.

Ce module génère des feuilles de styles CSS dynamiques basées sur la configuration
du cabinet, avec support des marges personnalisées et des bordures fines.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class MarginConfig:
    """Configuration des marges pour les documents PDF."""
    top: float = 3.0      # cm
    bottom: float = 2.5   # cm
    left: float = 1.5     # cm
    right: float = 1.5    # cm


@dataclass
class ColorConfig:
    """Configuration des couleurs du document."""
    primary: str = "#003380"
    secondary: str = "#0055AA"
    background: str = "#FFFFFF"
    text: str = "#1F2937"


@dataclass
class HeaderFooterConfig:
    """Configuration spécifique pour l'en-tête et le pied de page."""
    # Option A: Génération automatique
    auto_generate: bool = True
    logo_enabled: bool = True
    logo_size_cm: float = 2.5
    
    # Option B: Papier en-tête personnalisé
    letterhead_enabled: bool = False
    letterhead_path: Optional[str] = None
    letterhead_margins: Optional[MarginConfig] = None
    
    # Masquer header/footer par défaut si letterhead activé
    hide_default_header: bool = False
    hide_default_footer: bool = False


class CSSGenerator:
    """
    Générateur de styles CSS pour WeasyPrint.
    
    Génère des feuilles de styles dynamiques avec:
    - Bordures fines pour les sections
    - Gestion des marges personnalisées
    - Support du papier en-tête A5
    - Variables CSS pour la cohérence visuelle
    """
    
    def __init__(
        self,
        colors: Optional[ColorConfig] = None,
        margins: Optional[MarginConfig] = None,
        header_footer: Optional[HeaderFooterConfig] = None
    ):
        self.colors = colors or ColorConfig()
        self.margins = margins or MarginConfig()
        self.header_footer = header_footer or HeaderFooterConfig()
    
    def generate_document_css(self, page_size: str = "A5") -> str:
        """
        Génère la feuille de styles CSS complète pour un document.
        
        Args:
            page_size: Format de page (A4, A5, etc.)
            
        Returns:
            Chaîne CSS complète prête pour WeasyPrint
        """
        css_parts = [
            self._generate_css_variables(),
            self._generate_page_rules(page_size),
            self._generate_header_styles(),
            self._generate_footer_styles(),
            self._generate_content_styles(),
            self._generate_typography_styles(),
        ]
        
        return "\n\n".join(css_parts)
    
    def _generate_css_variables(self) -> str:
        """Génère les variables CSS personnalisées."""
        return f"""
/* =============================================================================
   VARIABLES CSS - Digital Crown
   ============================================================================= */
:root {{
    /* Couleurs principales */
    --primary-color: {self.colors.primary};
    --primary-light: {self._lighten_color(self.colors.primary, 20)};
    --primary-dark: {self._darken_color(self.colors.primary, 15)};
    --secondary-color: {self.colors.secondary};
    
    /* Couleurs de fond et texte */
    --background-color: {self.colors.background};
    --text-color: {self.colors.text};
    --text-muted: #6B7280;
    
    /* Bordures */
    --border-color: #E5E7EB;
    --border-primary: {self.colors.primary};
    
    /* Espacements */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    
    /* Typographie */
    --font-primary: 'Helvetica', 'Arial', sans-serif;
    --font-arabic: 'Amiri', 'Arial', sans-serif;
    --font-size-base: 10pt;
    --line-height-base: 1.4;
}}
"""
    
    def _generate_page_rules(self, page_size: str) -> str:
        """Génère les règles @page pour WeasyPrint."""
        # Ajuster les marges si papier en-tête activé
        if self.header_footer.letterhead_enabled and self.header_footer.letterhead_margins:
            margins = self.header_footer.letterhead_margins
            margin_top = f"{margins.top}cm"
            margin_bottom = f"{margins.bottom}cm"
        else:
            margin_top = f"{self.margins.top}cm"
            margin_bottom = f"{self.margins.bottom}cm"
        
        margin_left = f"{self.margins.left}cm"
        margin_right = f"{self.margins.right}cm"
        
        return f"""
/* =============================================================================
   RÈGLES DE PAGE
   ============================================================================= */
@page {{
    size: {page_size};
    margin-top: {margin_top};
    margin-bottom: {margin_bottom};
    margin-left: {margin_left};
    margin-right: {margin_right};
    
    @top-center {{
        content: "";
    }}
    
    @bottom-center {{
        content: "";
    }}
}}
"""
    
    def _generate_header_styles(self) -> str:
        """Génère les styles pour l'en-tête du document."""
        if self.header_footer.hide_default_header:
            return """
/* =============================================================================
   EN-TÊTE (Masqué - Mode papier en-tête)
   ============================================================================= */
.doc-header {
    display: none !important;
}
"""
        
        return """
/* =============================================================================
   EN-TÊTE DU DOCUMENT
   ============================================================================= */
.doc-header {
    width: 100%;
    padding-bottom: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
    border-bottom: 0.5pt solid var(--border-color);
}

.doc-header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.doc-header-left,
.doc-header-right {
    flex: 1;
}

.doc-header-center {
    text-align: center;
    padding: 0 var(--spacing-md);
}

.doc-header-logo {
    max-width: 2.5cm;
    max-height: 2.5cm;
    object-fit: contain;
}

.doc-practitioner-name {
    font-family: var(--font-primary);
    font-size: 11pt;
    font-weight: bold;
    color: var(--primary-color);
    margin: 0 0 var(--spacing-xs) 0;
}

.doc-practitioner-title {
    font-family: var(--font-primary);
    font-size: 9pt;
    color: var(--text-muted);
    margin: 0;
}

.doc-specialties {
    font-family: var(--font-primary);
    font-size: 8pt;
    color: var(--primary-color);
    margin-top: var(--spacing-xs);
}

/* Version arabe de l'en-tête */
.doc-header-arabic {
    direction: rtl;
    text-align: right;
    font-family: var(--font-arabic);
}
"""
    
    def _generate_footer_styles(self) -> str:
        """Génère les styles pour le pied de page avec bordure supérieure fine."""
        if self.header_footer.hide_default_footer:
            return """
/* =============================================================================
   PIED DE PAGE (Masqué - Mode papier en-tête)
   ============================================================================= */
.doc-footer {
    display: none !important;
}
"""
        
        return """
/* =============================================================================
   PIED DE PAGE AVEC BORDURE SUPÉRIEURE FINE
   ============================================================================= */
.doc-footer {
    width: 100%;
    /* 
     * BORDURE SUPÉRIEURE FINE 
     * Ligne fine de 1px (0.75pt en print) avec la couleur primaire
     * Padding top pour espacer le contenu de la bordure
     */
    border-top: 0.75pt solid var(--primary-color);
    padding-top: 10px;
    margin-top: var(--spacing-xl);
    
    /* Typographie du footer */
    font-family: var(--font-primary);
    font-size: 8pt;
    color: var(--text-muted);
    text-align: center;
}

.doc-footer-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-xs);
}

.doc-footer-address {
    font-style: normal;
    margin: 0;
    line-height: var(--line-height-base);
}

.doc-footer-contacts {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--spacing-sm);
    margin: 0;
}

.doc-footer-contact-item {
    white-space: nowrap;
}

/* Séparateur visuel subtil optionnel */
.doc-footer-separator {
    width: 30%;
    height: 0.5pt;
    background-color: var(--border-color);
    margin: var(--spacing-xs) auto;
}

/* Version pour documents bilangues */
.doc-footer-bilingual {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.doc-footer-bilingual .doc-footer-left,
.doc-footer-bilingual .doc-footer-right {
    flex: 1;
}

.doc-footer-bilingual .doc-footer-right {
    direction: rtl;
    text-align: right;
    font-family: var(--font-arabic);
}

/* Style alternatif avec bordure plus discrète */
.doc-footer-subtle {
    border-top: 0.5pt solid var(--border-color);
    padding-top: 8px;
}

/* Style avec bordure double (option premium) */
.doc-footer-premium {
    border-top: 1.5pt double var(--primary-color);
    padding-top: 12px;
}
"""
    
    def _generate_content_styles(self) -> str:
        """Génère les styles pour le contenu principal."""
        return """
/* =============================================================================
   CONTENU PRINCIPAL
   ============================================================================= */
.doc-content {
    font-family: var(--font-primary);
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--text-color);
}

.doc-title {
    font-family: var(--font-primary);
    font-size: 14pt;
    font-weight: bold;
    color: var(--primary-color);
    text-align: center;
    text-decoration: underline;
    margin-bottom: var(--spacing-lg);
    margin-top: var(--spacing-md);
}

.doc-subtitle {
    font-family: var(--font-primary);
    font-size: 11pt;
    font-weight: bold;
    color: var(--primary-color);
    margin-top: var(--spacing-lg);
    margin-bottom: var(--spacing-sm);
}

.doc-section {
    margin-bottom: var(--spacing-lg);
}

.doc-paragraph {
    margin-bottom: var(--spacing-md);
    text-align: justify;
}

/* Tableaux */
.doc-table {
    width: 100%;
    border-collapse: collapse;
    margin: var(--spacing-md) 0;
    font-size: 9pt;
}

.doc-table th {
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    padding: var(--spacing-sm);
    text-align: center;
    border: 0.5pt solid var(--primary-color);
}

.doc-table td {
    padding: var(--spacing-sm);
    border: 0.5pt solid var(--border-color);
}

.doc-table tr:nth-child(even) {
    background-color: #F9FAFB;
}

/* Listes */
.doc-list {
    margin: var(--spacing-md) 0;
    padding-left: var(--spacing-lg);
}

.doc-list-item {
    margin-bottom: var(--spacing-xs);
}

/* Médicaments (ordonnances) */
.doc-medication {
    margin-bottom: var(--spacing-md);
    page-break-inside: avoid;
}

.doc-medication-name {
    font-weight: bold;
    color: var(--primary-color);
    font-size: 10pt;
}

.doc-medication-dosage {
    font-size: 9pt;
    color: var(--text-muted);
    margin-left: var(--spacing-md);
}

.doc-medication-posology {
    font-size: 9pt;
    font-style: italic;
    margin-left: var(--spacing-lg);
    margin-top: var(--spacing-xs);
}
"""
    
    def _generate_typography_styles(self) -> str:
        """Génère les styles typographiques additionnels."""
        return """
/* =============================================================================
   TYPOGRAPHIE ET UTILITAIRES
   ============================================================================= */

/* Texte en arabe */
.arabic {
    direction: rtl;
    text-align: right;
    font-family: var(--font-arabic);
}

/* Alignements */
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-justify { text-align: justify; }

/* Gras et italique */
.font-bold { font-weight: bold; }
.font-normal { font-weight: normal; }
.italic { font-style: italic; }

/* Couleurs utilitaires */
.text-primary { color: var(--primary-color); }
.text-muted { color: var(--text-muted); }

/* Espacements */
.mt-0 { margin-top: 0; }
.mt-1 { margin-top: var(--spacing-xs); }
.mt-2 { margin-top: var(--spacing-sm); }
.mt-3 { margin-top: var(--spacing-md); }
.mt-4 { margin-top: var(--spacing-lg); }

.mb-0 { margin-bottom: 0; }
.mb-1 { margin-bottom: var(--spacing-xs); }
.mb-2 { margin-bottom: var(--spacing-sm); }
.mb-3 { margin-bottom: var(--spacing-md); }
.mb-4 { margin-bottom: var(--spacing-lg); }

/* Saut de page */
.page-break { page-break-after: always; }
.page-break-before { page-break-before: always; }
.avoid-break { page-break-inside: avoid; }

/* Filigrane (watermark) */
.watermark {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    opacity: 0.10;
    z-index: -1;
    pointer-events: none;
}

.watermark img {
    max-width: 7cm;
    max-height: 7cm;
}
"""
    
    def generate_letterhead_css(self, letterhead_path: str, margins: MarginConfig) -> str:
        """
        Génère les styles CSS spécifiques pour l'utilisation d'un papier en-tête.
        
        Args:
            letterhead_path: Chemin vers l'image du papier en-tête
            margins: Marges personnalisées
            
        Returns:
            CSS pour l'intégration du papier en-tête
        """
        return f"""
/* =============================================================================
   PAPIER EN-TÊTE PERSONNALISÉ
   ============================================================================= */
@page {{
    background-image: url("{letterhead_path}");
    background-size: cover;
    background-position: center top;
    margin-top: {margins.top}cm;
    margin-bottom: {margins.bottom}cm;
    margin-left: 1.5cm;
    margin-right: 1.5cm;
}}

/* Masquer les éléments générés automatiquement */
.doc-header,
.doc-footer {{
    display: none !important;
}}

/* Ajuster le contenu pour le papier en-tête */
.doc-content {{
    padding-top: 0;
}}
"""
    
    def _lighten_color(self, hex_color: str, percent: int) -> str:
        """Éclaircit une couleur hexadécimale."""
        # Convertir hex en RGB
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Éclaircir
        r = min(255, int(r + (255 - r) * percent / 100))
        g = min(255, int(g + (255 - g) * percent / 100))
        b = min(255, int(b + (255 - b) * percent / 100))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _darken_color(self, hex_color: str, percent: int) -> str:
        """Assombrit une couleur hexadécimale."""
        # Convertir hex en RGB
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Assombrir
        r = max(0, int(r * (100 - percent) / 100))
        g = max(0, int(g * (100 - percent) / 100))
        b = max(0, int(b * (100 - percent) / 100))
        
        return f"#{r:02x}{g:02x}{b:02x}"


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def generate_default_css(
    primary_color: str = "#003380",
    margins: Optional[Dict[str, float]] = None,
    letterhead_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    Fonction utilitaire pour générer rapidement un CSS par défaut.
    
    Args:
        primary_color: Couleur principale du cabinet
        margins: Dict avec 'top', 'bottom', 'left', 'right' en cm
        letterhead_config: Configuration du papier en-tête
        
    Returns:
        Chaîne CSS complète
    """
    colors = ColorConfig(primary=primary_color)
    
    margin_config = MarginConfig(
        top=margins.get('top', 3.0) if margins else 3.0,
        bottom=margins.get('bottom', 2.5) if margins else 2.5,
        left=margins.get('left', 1.5) if margins else 1.5,
        right=margins.get('right', 1.5) if margins else 1.5,
    )
    
    hf_config = HeaderFooterConfig()
    if letterhead_config:
        hf_config.letterhead_enabled = letterhead_config.get('enabled', False)
        hf_config.letterhead_path = letterhead_config.get('path')
        hf_config.hide_default_header = letterhead_config.get('hide_header', False)
        hf_config.hide_default_footer = letterhead_config.get('hide_footer', False)
        
        if 'margins' in letterhead_config:
            m = letterhead_config['margins']
            hf_config.letterhead_margins = MarginConfig(
                top=m.get('top', 3.0),
                bottom=m.get('bottom', 2.5)
            )
    
    generator = CSSGenerator(
        colors=colors,
        margins=margin_config,
        header_footer=hf_config
    )
    
    return generator.generate_document_css()


def get_footer_border_css(primary_color: str = "#003380", style: str = "single") -> str:
    """
    Retourne uniquement le CSS pour la bordure du footer.
    
    Args:
        primary_color: Couleur de la bordure
        style: 'single', 'subtle', ou 'premium'
        
    Returns:
        Règle CSS pour .doc-footer
    """
    styles = {
        'single': f"""
.doc-footer {{
    border-top: 0.75pt solid {primary_color};
    padding-top: 10px;
}}""",
        'subtle': f"""
.doc-footer {{
    border-top: 0.5pt solid #E5E7EB;
    padding-top: 8px;
}}""",
        'premium': f"""
.doc-footer {{
    border-top: 1.5pt double {primary_color};
    padding-top: 12px;
}}"""
    }
    
    return styles.get(style, styles['single'])


# Instance singleton pour usage rapide
default_generator = CSSGenerator()
