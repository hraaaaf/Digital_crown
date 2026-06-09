import io
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class LogoProcessor:
    @staticmethod
    def process_logo(image_bytes: bytes, target_size: int = 400) -> bytes:
        """
        Prend une image brute, normalise la taille (max target_size)
        et retourne les bytes de l'image au format PNG, en préservant la transparence
        et le texte d'origine sans utiliser de détourage IA (qui supprime souvent le texte).
        """
        try:
            # 1. Ouverture avec Pillow
            img = Image.open(io.BytesIO(image_bytes))
            
            # 2. Préservation de la transparence
            if img.mode not in ('RGBA', 'LA'):
                if 'transparency' in img.info:
                    img = img.convert('RGBA')
                else:
                    # Si c'est un JPG ou sans transparence, on peut le convertir en RGBA
                    # pour standardiser la sortie en PNG
                    img = img.convert('RGBA')
            else:
                img = img.convert('RGBA')

            # 3. Redimensionnement (contain dans target_size max, sans changer le ratio)
            # L'utilisation de thumbnail garde les proportions sans rajouter de padding.
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

            # 4. Conversion en PNG bytes
            out_buffer = io.BytesIO()
            img.save(out_buffer, format="PNG", optimize=True)
            
            return out_buffer.getvalue()

        except Exception as e:
            logger.error(f"Erreur lors du traitement normal du logo: {str(e)}")
            raise e
