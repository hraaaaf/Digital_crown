import os
import json
import base64
import hashlib
import datetime
import logging
from cryptography.fernet import Fernet
from firebase_admin import firestore, credentials, initialize_app
from backend.core.paths import AppPaths

logger = logging.getLogger("license_service")


class LicenseService:
    _instance = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LicenseService, cls).__new__(cls)
            try:
                cred_path = AppPaths.get_base_dir() / "backend" / "core" / "firebase_creds.json"
                if cred_path.exists():
                    cred = credentials.Certificate(str(cred_path))
                    try:
                        initialize_app(cred)
                    except ValueError:
                        pass  # Firebase app already initialized
                    cls._db = firestore.client()
                else:
                    logger.warning("Firebase credentials missing. Local database decryption and offline verification will be enforced.")
            except Exception as e:
                logger.error(f"Failed to init Firebase: {e}")
        return cls._instance

    def _get_fernet(self) -> Fernet:
        master_key = os.getenv("CABINET_MASTER_KEY_HEX", os.getenv("SECRET_KEY", "default-dc-fallback-key"))
        key_32bytes = hashlib.sha256(master_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_32bytes)
        return Fernet(fernet_key)

    def _read_local_vault(self) -> dict:
        vault_path = AppPaths.get_user_data_dir() / "license_vault.bin"
        if not vault_path.exists():
            return {}
        try:
            f = self._get_fernet()
            encrypted_data = vault_path.read_bytes()
            decrypted_data = f.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to read/decrypt local license vault: {e}")
            return {}

    def _write_local_vault(self, data: dict) -> None:
        vault_path = AppPaths.get_user_data_dir() / "license_vault.bin"
        try:
            f = self._get_fernet()
            raw_bytes = json.dumps(data).encode()
            encrypted_data = f.encrypt(raw_bytes)
            vault_path.write_bytes(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to write/encrypt local license vault: {e}")

    async def validate_license(self, clinic_id: str) -> bool:
        """
        Vérifie la licence en ligne via Firebase Firestore.
        Si hors-ligne, applique un délai de grâce strict de 72 heures avec détection anti-rollback de l'horloge système.
        """
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Tenter la validation en ligne si Firebase est disponible
        if self._db:
            try:
                doc_ref = self._db.collection('licenses').document(clinic_id)
                doc = doc_ref.get()

                if doc.exists:
                    data = doc.to_dict()
                    is_active = data.get('active', False)
                    expiration = data.get('expiration_date')  # Firestore retourne un datetime UTC

                    if not is_active:
                        logger.error(f"❌ La licence du cabinet '{clinic_id}' a été désactivée par l'administrateur.")
                        return False

                    # Si expiration définie, valider par rapport à la date Firestore
                    if expiration:
                        # Convertir expiration en offset-aware UTC si ce n'est pas déjà le cas
                        if expiration.tzinfo is None:
                            expiration = expiration.replace(tzinfo=datetime.timezone.utc)
                        if now > expiration:
                            logger.error(f"❌ La licence du cabinet '{clinic_id}' a expiré le {expiration}.")
                            return False

                    # Tout est OK en ligne -> Écrire/Mettre à jour le coffre local sécurisé
                    expiration_str = expiration.isoformat() if expiration else None
                    local_data = {
                        "clinic_id": clinic_id,
                        "last_validated": now.isoformat(),
                        "expiration_date": expiration_str,
                        "max_seen_time": now.isoformat()
                    }
                    self._write_local_vault(local_data)
                    logger.info("✅ Licence validée en ligne avec succès. Coffre-fort local mis à jour.")
                    return True
                else:
                    logger.warning(f"⚠️ Aucun document de licence trouvé pour le cabinet '{clinic_id}'.")
            except Exception as e:
                logger.error(f"❌ Échec de la vérification de licence en ligne : {e}. Passage en mode hors-ligne.")

        # 2. Validation Hors-Ligne (Grace Period)
        logger.warning("🔌 Mode hors-ligne détecté. Analyse du délai de grâce local...")
        local_data = self._read_local_vault()

        if not local_data:
            logger.error("❌ Aucune preuve de licence locale trouvée. Connexion requise.")
            return False

        # Vérifier que le clinic_id correspond
        if local_data.get("clinic_id") != clinic_id:
            logger.error("❌ Conflit d'identifiant de cabinet dans le coffre-fort local.")
            return False

        # Extraire les dates locales
        try:
            last_validated = datetime.datetime.fromisoformat(local_data["last_validated"])
            max_seen_time = datetime.datetime.fromisoformat(local_data["max_seen_time"])
            expiration_str = local_data.get("expiration_date")
            expiration = datetime.datetime.fromisoformat(expiration_str) if expiration_str else None
        except Exception as e:
            logger.error(f"❌ Données de licence locales corrompues : {e}")
            return False

        # Sécurité 1 : Anti-Clock Rollback (Recul de l'horloge)
        if now < last_validated or now < max_seen_time:
            logger.critical("🚨 ATTAQUE DÉTECTÉE : L'horloge système a été reculée pour contourner la licence !")
            return False

        # Sécurité 2 : Expiration de la licence d'origine
        if expiration and now > expiration:
            logger.error(f"❌ La licence a expiré le {expiration}. Connexion Internet requise pour renouveler.")
            return False

        # Sécurité 3 : Limite de la Grace Period (72 heures maximum)
        grace_limit = last_validated + datetime.timedelta(hours=72)
        if now > grace_limit:
            logger.error("❌ Délai de grâce de 72 heures expiré. Une synchronisation en ligne est requise.")
            return False
        else:
            remaining_hours = int((grace_limit - now).total_seconds() / 3600)
            logger.warning(f"🛡️ Mode dégradé hors-ligne actif. Temps restant avant blocage : {remaining_hours} heures.")

            # Mettre à jour max_seen_time pour empêcher les futurs retours en arrière
            local_data["max_seen_time"] = now.isoformat()
            self._write_local_vault(local_data)
            return True
