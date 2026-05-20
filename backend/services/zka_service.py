import os
import base64
import json
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ZKAService:
    """
    Moteur de chiffrement Zero-Knowledge Authentifié (AES-GCM 256).
    Garantit Confidentialité + Intégrité + Interopérabilité avec Web Crypto API.
    
    Standard de sécurité : 
    - AES-GCM 256 bits
    - IV de 12 octets (recommandé pour GCM)
    - Tag d'authentification de 16 octets (inclus à la fin du ciphertext)
    """
    
    @staticmethod
    def encrypt_payload(data: Dict[str, Any], key_hex: str) -> str:
        """
        Chiffre un dictionnaire JSON et retourne un blob Base64.
        Format du blob retourné : BASE64( IV(12 bytes) + CIPHERTEXT + TAG(16 bytes) )
        """
        try:
            # 1. Préparation de la clé (32 bytes pour AES-256)
            key = bytes.fromhex(key_hex)
            aesgcm = AESGCM(key)
            
            # 2. Génération de l'IV (96 bits / 12 bytes recommandé)
            iv = os.urandom(12)
            
            # 3. Sérialisation JSON
            payload_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
            
            # 4. Chiffrement (Le tag est concaténé à la fin automatiquement)
            ciphertext_with_tag = aesgcm.encrypt(iv, payload_bytes, None)
            
            # 5. Construction du blob final (IV + DATA + TAG)
            final_blob = iv + ciphertext_with_tag
            
            return base64.b64encode(final_blob).decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur de chiffrement ZKA: {e}")
            raise

    @staticmethod
    def decrypt_payload(base64_blob: str, key_hex: str) -> Dict[str, Any]:
        """
        Déchiffre un blob (Base64) et retourne le dictionnaire JSON original.
        """
        try:
            key = bytes.fromhex(key_hex)
            aesgcm = AESGCM(key)
            
            blob_bytes = base64.b64decode(base64_blob)
            
            # Extraction des composants
            iv = blob_bytes[:12]
            ciphertext_with_tag = blob_bytes[12:]
            
            decrypted_bytes = aesgcm.decrypt(iv, ciphertext_with_tag, None)
            return json.loads(decrypted_bytes.decode('utf-8'))
        except Exception as e:
            logger.error(f"Erreur de déchiffrement ZKA: {e}")
            raise

    @staticmethod
    def generate_master_key() -> str:
        """Génère une nouvelle clé secrète de 256 bits en hexadécimal."""
        return os.urandom(32).hex()

    def rotate_master_key(self, env_path: str) -> str:
        """Génère une nouvelle clé et met à jour le fichier .env de manière persistante."""
        new_key = self.generate_master_key()
        
        # 1. Mise à jour dans l'environnement courant
        os.environ["CABINET_MASTER_KEY_HEX"] = new_key
        
        # 2. Mise à jour du fichier .env
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(env_path, 'w', encoding='utf-8') as f:
                found = False
                for line in lines:
                    if line.startswith("CABINET_MASTER_KEY_HEX="):
                        f.write(f"CABINET_MASTER_KEY_HEX={new_key}\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    f.write(f"\nCABINET_MASTER_KEY_HEX={new_key}\n")
        
        return new_key

zka_service = ZKAService()
