import qrcode
import io
import base64
from typing import Optional
from PIL import Image, ImageDraw

class QRService:
    """
    Service de génération de signatures QR sécurisées pour les documents cliniques.
    Génère des codes QR pointant vers une interface de validation 'Elite'.
    """
    
    @staticmethod
    def generate_qr_bytes(data: str, color: str = "#003380", box_size: int = 10, add_logo: bool = False, logo_path: Optional[str] = None, qr_style: str = "dots") -> io.BytesIO:
        """Génère un QR code moderne avec styles nommés (classic, dots, rounded, elite)."""
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers import (
            RoundedModuleDrawer, SquareModuleDrawer, CircleModuleDrawer, GaliModuleDrawer
        )
        from qrcode.image.styles.colormasks import SolidFillColorMask
        
        # On augmente la correction à M (Medium) par défaut
        error_corr = qrcode.constants.ERROR_CORRECT_H if add_logo else qrcode.constants.ERROR_CORRECT_M
        
        qr = qrcode.QRCode(
            version=None,
            error_correction=error_corr,
            box_size=box_size,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Conversion couleur
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            fill_color = (r, g, b)
        else:
            fill_color = (0, 51, 128)

        # Mapping des styles
        style_map = {
            "classic": SquareModuleDrawer(),
            "dots": CircleModuleDrawer(),
            "rounded": RoundedModuleDrawer(),
            "elite": GaliModuleDrawer()
        }
        drawer = style_map.get(qr_style, CircleModuleDrawer())

        # Génération Elite
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=drawer,
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=fill_color),
            embeded_image_path=logo_path if add_logo and logo_path else None
        ).convert('RGB')
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True)
        buffered.seek(0)
        return buffered

    @staticmethod
    def generate_vcard(name: str, phone: str, email: str, address: str = "") -> str:
        """Génère une chaîne vCard v3.0."""
        vcard = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{name}",
            f"TEL;TYPE=CELL:{phone}",
            f"EMAIL:{email}",
            f"ADR;TYPE=WORK:;;{address}" if address else "",
            "END:VCARD"
        ]
        return "\n".join(filter(None, vcard))

    @staticmethod
    def generate_whatsapp_url(phone: str, message: str = "") -> str:
        """Génère une URL WhatsApp robuste avec message pré-rempli."""
        import urllib.parse
        if not phone:
            return ""
            
        # Nettoyage strict : on ne garde que les chiffres
        clean_phone = "".join(filter(str.isdigit, phone))
        
        # Gestion intelligente du format local (ex: 06 12 34 56 78)
        # Si le numéro commence par 0 et fait 10 chiffres, on injecte le code pays par défaut (212 pour Digital Crown)
        if clean_phone.startswith("0") and not clean_phone.startswith("00") and len(clean_phone) == 10:
            clean_phone = "212" + clean_phone[1:]
        elif clean_phone.startswith("00"):
            clean_phone = clean_phone[2:]
            
        # Format wa.me plus court et mieux interprété par les scanners mobiles (v4.2)
        base_url = f"https://wa.me/{clean_phone}"
        if message:
            import urllib.parse
            base_url += f"?text={urllib.parse.quote(message)}"
            
        return base_url

    @staticmethod
    def generate_maps_url(address: str) -> str:
        """Génère une URL Google Maps pour une adresse."""
        import urllib.parse
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"

    def generate_document_qr_base64(self, document_id: str, public_id: str, base_url: str = "https://digitalcrown.ai", color: str = "#003380", qr_style: str = "dots") -> str:
        """Méthode legacy mise à jour pour supporter les styles Elite."""
        verify_url = f"{base_url}/verify/{public_id}/{document_id}"
        buffered = self.generate_qr_bytes(verify_url, color=color, qr_style=qr_style)
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{qr_base64}"

# Singleton instance
qr_service = QRService()
