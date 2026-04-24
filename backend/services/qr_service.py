import qrcode
import io
import base64
from typing import Optional

class QRService:
    """
    Service de génération de signatures QR sécurisées pour les documents cliniques.
    Génère des codes QR pointant vers une interface de validation 'Elite'.
    """
    
    def generate_document_qr(self, document_id: str, public_id: str, base_url: str = "http://localhost:5173") -> str:
        """
        Génère un QR code en Base64 pour un document spécifique.
        Le lien pointe vers l'interface de vérification publique.
        """
        # Construction de l'URL de vérification
        verify_url = f"{base_url}/verify/{public_id}/{document_id}"
        
        # Configuration premium du QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)

        # Création de l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Conversion en Base64 pour injection HTML/PDF
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_base64}"

# Singleton instance
qr_service = QRService()
