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
    def generate_qr_bytes(data: str, color: str = "black", box_size: int = 10, add_logo: bool = True, logo_path: Optional[str] = None) -> io.BytesIO:
        """Génère les octets d'un QR code avec support de logo personnalisé au centre."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=color, back_color="white").convert('RGB')
        
        if add_logo:
            width, height = img.size
            logo_size = width // 5
            logo_box = (
                (width - logo_size) // 2,
                (height - logo_size) // 2,
                (width + logo_size) // 2,
                (height + logo_size) // 2
            )
            
            draw = ImageDraw.Draw(img)
            draw.rectangle(logo_box, fill="white")
            
            if logo_path:
                try:
                    # Chargement et redimensionnement du logo réel
                    logo = Image.open(logo_path).convert("RGBA")
                    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                    # On crée un fond blanc pour le logo s'il a de la transparence
                    logo_bg = Image.new("RGBA", logo.size, "WHITE")
                    logo_final = Image.alpha_composite(logo_bg, logo).convert("RGB")
                    img.paste(logo_final, (logo_box[0], logo_box[1]))
                except Exception as e:
                    print(f"Erreur chargement logo QR: {e}")
                    # Fallback sur le sceau minimaliste si le logo échoue
                    inner_margin = logo_size // 5
                    inner_box = (logo_box[0] + inner_margin, logo_box[1] + inner_margin, logo_box[2] - inner_margin, logo_box[3] - inner_margin)
                    draw.rectangle(inner_box, fill=color)
            else:
                # Sceau minimaliste par défaut
                inner_margin = logo_size // 5
                inner_box = (logo_box[0] + inner_margin, logo_box[1] + inner_margin, logo_box[2] - inner_margin, logo_box[3] - inner_margin)
                draw.rectangle(inner_box, fill=color)
            
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
        """Génère une URL WhatsApp avec message pré-rempli."""
        import urllib.parse
        clean_phone = phone.replace(" ", "").replace("+", "")
        url = f"https://wa.me/{clean_phone}"
        if message:
            url += f"?text={urllib.parse.quote(message)}"
        return url

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
