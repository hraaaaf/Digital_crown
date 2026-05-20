import threading
import logging
import os
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import Session
from backend import models
from backend.database import SessionLocal
from backend.services.zka_service import zka_service
from backend.services.state_extractor import state_extractor
from backend.services.supabase_sync_service import supabase_sync_service

logger = logging.getLogger(__name__)

class SyncManager:
    """
    Gestionnaire de synchronisation Zero-Knowledge.
    Intercepte les changements DB, agrège les données et les pousse vers le cloud après chiffrement.
    Utilise un mécanisme de Debouncing pour optimiser les ressources.
    """
    
    def __init__(self, debounce_seconds=10.0):
        self.debounce_seconds = debounce_seconds
        self.timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()
        self._pending_employers = set()

    def start_listening(self):
        """Active les listeners SQLAlchemy pour les modèles critiques."""
        models_to_watch = [models.Appointment, models.Payment, models.Patient, models.Acte]
        
        for model in models_to_watch:
            event.listen(model, 'after_insert', self._on_change)
            event.listen(model, 'after_update', self._on_change)
            event.listen(model, 'after_delete', self._on_change)
            
        logger.info(f"📡 SyncManager ZKA : Observation active sur {len(models_to_watch)} modèles.")

    def _on_change(self, mapper, connection, target):
        """Callback appelé lors de toute modification en base de données."""
        # Récupération de l'ID employeur (tenant)
        employer_id = getattr(target, 'employer_id', None)
        
        # Cas spécial pour les Actes qui sont liés au praticien
        if not employer_id and hasattr(target, 'praticien_id'):
            employer_id = target.praticien_id
            
        if employer_id:
            self._schedule_sync(employer_id)

    def _schedule_sync(self, employer_id: int):
        """Planifie la synchronisation avec debounce."""
        with self.lock:
            self._pending_employers.add(employer_id)
            
            if self.timer is not None:
                self.timer.cancel()
            
            self.timer = threading.Timer(
                self.debounce_seconds, 
                self._perform_bulk_sync
            )
            self.timer.start()

    def _perform_bulk_sync(self):
        """Exécute la synchronisation pour tous les cabinets ayant eu des modifications."""
        with self.lock:
            employers_to_sync = list(self._pending_employers)
            self._pending_employers.clear()
            self.timer = None

        if not employers_to_sync:
            return

        db = SessionLocal()
        try:
            for emp_id in employers_to_sync:
                self._sync_single_cabinet(db, emp_id)
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation en rafale : {e}")
        finally:
            db.close()

    def _sync_single_cabinet(self, db: Session, employer_id: int):
        """Synchronise un cabinet spécifique."""
        try:
            # 1. Récupération de l'identifiant public du cabinet
            config = db.query(models.CabinetConfig).filter(
                models.CabinetConfig.owner_id == employer_id
            ).first()
            
            if not config:
                logger.warning(f"Pas de CabinetConfig trouvé pour l'employeur {employer_id}. Synchro ignorée.")
                return

            # 2. Extraction du snapshot JSON
            raw_state = state_extractor.get_full_snapshot(db, employer_id)
            
            # 3. Récupération de la clé maître (Locale au PC)
            # Dans une version prod, cette clé serait lue depuis un keystore sécurisé ou le .env local
            master_key = os.getenv("CABINET_MASTER_KEY_HEX")
            
            if not master_key:
                # Fallback dev uniquement - NE PAS UTILISER EN PROD
                logger.warning("CABINET_MASTER_KEY_HEX manquante. Utilisation d'une clé de test.")
                master_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

            # 4. Chiffrement AES-GCM 256
            encrypted_blob = zka_service.encrypt_payload(raw_state, master_key)
            
            # 5. Push vers le relais Cloud
            success = supabase_sync_service.push_snapshot(config.public_id, encrypted_blob)
            
            if success:
                logger.info(f"✅ Sync ZKA réussie pour le cabinet {config.public_id}")
            else:
                logger.error(f"❌ Échec du PUSH ZKA pour le cabinet {config.public_id}")

        except Exception as e:
            logger.error(f"Erreur lors de la synchro du cabinet {employer_id} : {e}")

sync_manager = SyncManager()
