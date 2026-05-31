import io
import base64
from PIL import Image
import rembg
import logging

logger = logging.getLogger(__name__)

class LogoProcessor:
    @staticmethod
    def process_logo(image_bytes: bytes, target_size: int = 400) -> bytes:
        """
        Prend une image brute, retire le fond (IA), normalise la taille et
        retourne les bytes de l'image au format PNG.
        """
        try:
            # 1. Suppression du fond avec rembg
            # rembg.remove accepte des bytes et retourne des bytes
            no_bg_bytes = rembg.remove(image_bytes)

            # 2. Ouverture avec Pillow pour normalisation
            img = Image.open(io.BytesIO(no_bg_bytes))
            
            # S'assurer qu'on est en RGBA (transparence)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Crop aux limites réelles du logo (trim transparent pixels)
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)

            # 3. Redimensionnement (contain dans target_size x target_size avec padding)
            # Calcul du ratio
            w, h = img.size
            ratio = min((target_size - 40) / w, (target_size - 40) / h) # 20px padding
            new_w, new_h = int(w * ratio), int(h * ratio)
            
            # Anti-aliasing (LANCZOS)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Création d'un fond blanc pur et totalement opaque (pas de transparence)
            new_img = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 255))
            
            # Collage au centre (utilisation du logo comme masque alpha)
            paste_x = (target_size - new_w) // 2
            paste_y = (target_size - new_h) // 2
            new_img.paste(img, (paste_x, paste_y), img)

            # Conversion en RGB pour SUPPRIMER définitivement la transparence
            # (ceci empêchera les moteurs PDF de générer un fond noir)
            final_img = new_img.convert('RGB')

            # 4. Conversion en PNG bytes
            out_buffer = io.BytesIO()
            final_img.save(out_buffer, format="PNG")
            
            return out_buffer.getvalue()

        except Exception as e:
            logger.error(f"Erreur lors du traitement premium du logo: {str(e)}")
            raise e
