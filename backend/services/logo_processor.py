import io
import base64
from PIL import Image
import rembg
import logging

logger = logging.getLogger(__name__)

class LogoProcessor:
    @staticmethod
    def process_logo(image_bytes: bytes, target_size: int = 400) -> str:
        """
        Prend une image brute, retire le fond (IA), normalise la taille et
        retourne une chaîne SVG valide contenant l'image en base64 pour une intégration parfaite.
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

            # Création du fond transparent cible
            new_img = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
            
            # Collage au centre
            paste_x = (target_size - new_w) // 2
            paste_y = (target_size - new_h) // 2
            new_img.paste(img, (paste_x, paste_y), img)

            # 4. Conversion en PNG bytes
            out_buffer = io.BytesIO()
            new_img.save(out_buffer, format="PNG")
            final_png_bytes = out_buffer.getvalue()

            # 5. Encodage Base64
            b64_str = base64.b64encode(final_png_bytes).decode('utf-8')

            # 6. Génération du wrapper SVG Premium
            # On crée un SVG fluide qui conserve les dimensions exactes
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {target_size} {target_size}" width="100%" height="100%">
  <image href="data:image/png;base64,{b64_str}" width="{target_size}" height="{target_size}" />
</svg>"""
            
            return svg_content

        except Exception as e:
            logger.error(f"Erreur lors du traitement premium du logo: {str(e)}")
            raise e
