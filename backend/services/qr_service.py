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
    def generate_qr_bytes(data: str, color: str = "black", box_size: int = 10, add_logo: bool = False, logo_path: Optional[str] = None) -> io.BytesIO:
        """Génère les octets d'un QR code minimaliste et universellement lisible."""
        qr = qrcode.QRCode(
            version=None,
            # Niveau L (Low) pour la grille la plus simple et la moins encombrée
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=color, back_color="white").convert('RGB')
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
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
            
        # Format universel api.whatsapp.com souvent plus stable que wa.me sur certains devices
        base_url = "https://api.whatsapp.com/send"
        params = {"phone": clean_phone}
        if message:
            params["text"] = message
            
        return f"{base_url}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def generate_maps_url(address: str) -> str:
        """Génère une URL Google Maps pour une adresse."""
        import urllib.parse
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"

    def generate_document_qr_base64(self, document_id: str, public_id: str, base_url: str = "https://digitalcrown.ai") -> str:
        """Méthode legacy pour compatibilité Base64."""
        verify_url = f"{base_url}/verify/{public_id}/{document_id}"
        buffered = self.generate_qr_bytes(verify_url)
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{qr_base64}"

# Singleton instance
qr_service = QRService()
