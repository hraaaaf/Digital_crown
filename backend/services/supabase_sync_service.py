import httpx
import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseSyncService:
    """
    Relais Cloud (Supabase) pour les snapshots chiffrés.
    Le serveur Supabase ne stocke que des blobs AES-GCM illisibles.
    """
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        # Table cible : cabinet_snapshots (public_id text PK, encrypted_data text, updated_at timestamptz)
        self.table_url = f"{self.url}/rest/v1/cabinet_snapshots"

    def push_snapshot(self, public_id: str, encrypted_blob: str) -> bool:
        """
        Pousse ou met à jour le snapshot chiffré dans Supabase.
        Utilise l'upsert via l'en-tête 'Prefer: resolution=merge-duplicates'.
        """
        if not self.url or not self.key:
            logger.error("Configuration Supabase manquante dans .env")
            return False

        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        payload = {
            "public_id": public_id,
            "encrypted_data": encrypted_blob,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.table_url, 
                    json=payload, 
                    headers=headers
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Erreur Supabase ({response.status_code}): {response.text}")
                    return False
                    
                return True
        except Exception as e:
            logger.error(f"Erreur réseau lors du PUSH ZKA: {e}")
            return False

supabase_sync_service = SupabaseSyncService()
