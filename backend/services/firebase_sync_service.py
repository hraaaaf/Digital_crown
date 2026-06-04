import os
import logging
from datetime import datetime
from backend.services.license_service import LicenseService

logger = logging.getLogger(__name__)

class FirebaseSyncService:
    """
    Relais Cloud (Firebase) pour les snapshots chiffrés.
    Le serveur Firebase ne stocke que des blobs AES-GCM illisibles.
    """
    
    def __init__(self):
        # On utilise le db initialisé dans license_service pour ne pas dupliquer l'initialisation
        self.license_service = LicenseService()

    def push_snapshot(self, public_id: str, encrypted_blob: str) -> bool:
        """
        Pousse ou met à jour le snapshot chiffré dans Firebase Firestore.
        """
        db = self.license_service._db
        if not db:
            logger.error("Configuration Firebase manquante ou non initialisée.")
            return False
            
        try:
            doc_ref = db.collection('cabinet_snapshots').document(public_id)
            doc_ref.set({
                "public_id": public_id,
                "encrypted_data": encrypted_blob,
                "updated_at": datetime.now()
            }, merge=True)
            return True
        except Exception as e:
            logger.error(f"Erreur réseau lors du PUSH ZKA vers Firebase: {e}")
            return False

firebase_sync_service = FirebaseSyncService()
