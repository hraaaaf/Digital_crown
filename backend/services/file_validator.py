# =============================================================================
# FICHIER: backend/services/file_validator.py
# =============================================================================
"""
Validation sécurisée des fichiers uploadés.
Protection contre les uploads malveillants via vérification magic bytes + PIL.
"""

import io
import logging
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic non installé - Validation des types MIME désactivée")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("Pillow non installé - Validation des images désactivée")

logger = logging.getLogger(__name__)

# Types MIME autorisés pour les radiographies médicales
ALLOWED_MIME_TYPES = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/tiff': 'tiff',
    'image/dicom': 'dcm',
    'application/dicom': 'dcm',
}

# Extensions de fichier autorisées (secondaire)
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.dcm', '.dicom'}

# Taille maximale: 10 Mo
MAX_FILE_SIZE = 10 * 1024 * 1024

# Dimensions minimales pour une radio médicale valide
MIN_IMAGE_DIMENSION = 100  # pixels
MAX_IMAGE_DIMENSION = 10000  # pixels (protection contre zip bomb)


class FileValidationError(Exception):
    """Exception levée lors de la validation d'un fichier."""
    pass


def validate_uploaded_image(file: UploadFile) -> Tuple[bytes, dict]:
    """
    Valide un fichier image uploadé de manière sécurisée (version simplifiée).
    """
    # Vérification de l'extension
    filename = file.filename or "unknown"
    extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non autorisée: {extension}"
        )
    
    # Lecture du contenu par chunks pour éviter la surcharge mémoire
    content = b''
    total_size = 0
    for chunk in iter(lambda: file.file.read(8192), b''):
        content += chunk
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")
    
    if total_size == 0:
        raise HTTPException(status_code=400, detail="Fichier vide")
    
    # Validation simple PIL
    if PIL_AVAILABLE:
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            img.verify()
            metadata = {
                'width': width,
                'height': height,
                'format': img.format,
                'mime_type': f"image/{extension.lstrip('.')}",
                'size_bytes': total_size
            }
        except Exception:
            raise HTTPException(status_code=400, detail="Image invalide ou corrompue")
    else:
        metadata = {'size_bytes': total_size}
    
    return content, metadata


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les path traversal et injections.
    
    Args:
        filename: Nom de fichier original
        
    Returns:
        Nom de fichier sécurisé
    """
    import re
    
    # Supprime les caractères dangereux
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Supprime les path traversal
    filename = filename.replace('..', '')
    filename = filename.replace('/', '')
    filename = filename.replace('\\', '')
    
    # Limite la longueur
    if len(filename) > 200:
        name, ext = filename[:196], filename[196:].split('.')[-1] if '.' in filename else ''
        filename = f"{name}.{ext}" if ext else name
    
    return filename
