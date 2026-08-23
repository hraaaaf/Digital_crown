import os
import json
import base64
import hashlib
import datetime
import logging
from cryptography.fernet import Fernet
from firebase_admin import firestore, credentials, initialize_app
from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter

logger = logging.getLogger("license_service")

_WEAK_LOCAL_SECRETS = {
    "SET_A_REAL_SECRET_KEY_IN_ENV",
    "dev_only_secret_key_change_me",
    "default-dc-fallback-key",
    "changeme",
    "secret",
}


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

    @staticmethod
    def _vault_master_key() -> str:
        """Return the destination-local key material used for the licence vault."""
        dedicated = os.getenv("CABINET_MASTER_KEY_HEX", "").strip()
        shared = os.getenv("SECRET_KEY", "").strip()
        master_key = dedicated or shared
        if not master_key or master_key in _WEAK_LOCAL_SECRETS or len(master_key) < 32:
            raise RuntimeError(
                "Secure local licence vault key unavailable: configure a unique "
                "CABINET_MASTER_KEY_HEX or SECRET_KEY (>= 32 characters)."
            )
        return master_key

    def _get_fernet(self) -> Fernet:
        master_key = self._vault_master_key()
        key_32bytes = hashlib.sha256(master_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_32bytes)
        return Fernet(fernet_key)

    @staticmethod
    def _vault_path():
        return AppPaths.get_user_data_dir() / "license_vault.bin"

    def _read_local_vault(self) -> dict:
        vault_path = self._vault_path()
        if not vault_path.exists():
            return {}
        try:
            f = self._get_fernet()
            encrypted_data = vault_path.read_bytes()
            decrypted_data = f.decrypt(encrypted_data)
            payload = json.loads(decrypted_data.decode())
            return payload if isinstance(payload, dict) else {}
        except Exception as e:
            logger.error(f"Failed to read/decrypt local license vault: {e}")
            return {}

    def _write_local_vault(self, data: dict) -> bool:
        vault_path = self._vault_path()
        try:
            f = self._get_fernet()
            raw_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
            encrypted_data = f.encrypt(raw_bytes)
            get_platform_adapter().atomic_write_text(
                vault_path,
                encrypted_data.decode("ascii"),
                encoding="ascii",
                mode=0o600,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to write/encrypt local license vault: {e}")
            return False

    def clear_local_vault_for_rebind(self) -> bool:
        """Remove only machine-local licence proof before destination re-acquisition."""
        vault_path = self._vault_path()
        try:
            vault_path.unlink(missing_ok=True)
            return not vault_path.exists()
        except OSError as e:
            logger.error(f"Failed to clear local license vault for rebind: {e}")
            return False

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

                    if expiration:
                        if expiration.tzinfo is None:
                            expiration = expiration.replace(tzinfo=datetime.timezone.utc)
                        if now > expiration:
                            logger.error(f"❌ La licence du cabinet '{clinic_id}' a expiré le {expiration}.")
                            return False

                    expiration_str = expiration.isoformat() if expiration else None
                    local_data = {
                        "clinic_id": clinic_id,
                        "last_validated": now.isoformat(),
                        "expiration_date": expiration_str,
                        "max_seen_time": now.isoformat()
                    }
                    if self._write_local_vault(local_data):
                        logger.info("✅ Licence validée en ligne avec succès. Coffre-fort local mis à jour.")
                    else:
                        logger.error(
                            "Licence validée en ligne, mais la preuve hors-ligne n'a pas pu être persistée."
                        )
                    return True
                else:
                    logger.warning(f"⚠️ Aucun document de licence trouvé pour le cabinet '{clinic_id}'.")
            except Exception as e:
                logger.error(f"❌ Échec de la vérification de licence en ligne : {e}. Passage en mode hors-ligne.")

        logger.warning("🔌 Mode hors-ligne détecté. Analyse du délai de grâce local...")
        local_data = self._read_local_vault()

        if not local_data:
            logger.warning("⚠️ Aucune preuve de licence locale exploitable. Validation refusée.")
            return False

        if local_data.get("clinic_id") != clinic_id:
            logger.error("❌ Conflit d'identifiant de cabinet dans le coffre-fort local.")
            return False

        try:
            last_validated = datetime.datetime.fromisoformat(local_data["last_validated"])
            max_seen_time = datetime.datetime.fromisoformat(local_data["max_seen_time"])
            expiration_str = local_data.get("expiration_date")
            expiration = datetime.datetime.fromisoformat(expiration_str) if expiration_str else None
        except Exception as e:
            logger.error(f"❌ Données de licence locales corrompues : {e}")
            return False

        if now < last_validated or now < max_seen_time:
            logger.critical("🚨 ATTAQUE DÉTECTÉE : L'horloge système a été reculée pour contourner la licence !")
            return False

        if expiration and now > expiration:
            logger.error(f"❌ La licence a expiré le {expiration}. Connexion Internet requise pour renouveler.")
            return False

        grace_limit = last_validated + datetime.timedelta(hours=72)
        if now > grace_limit:
            logger.error("❌ Délai de grâce de 72 heures expiré. Une synchronisation en ligne est requise.")
            return False
        else:
            remaining_hours = int((grace_limit - now).total_seconds() / 3600)
            logger.warning(f"🛡️ Mode dégradé hors-ligne actif. Temps restant avant blocage : {remaining_hours} heures.")

            local_data["max_seen_time"] = now.isoformat()
            if not self._write_local_vault(local_data):
                logger.error("❌ Impossible de persister l'état anti-rollback de la licence.")
                return False
            return True

    async def validate_license_with_expiry(self, clinic_id: str) -> dict:
        """
        Retourne l'état complet depuis Firebase pour synchronisation avec SQLite.

        active=None signifie "Firebase injoignable/non configuré : aucune réponse
        obtenue" — l'appelant doit alors CONSERVER l'état local plutôt que de
        l'écraser. active=False reste une réponse DÉFINITIVE de Firebase.
        """
        if not self._db:
            return {"active": None, "expiration_date": None}

        try:
            doc_ref = self._db.collection('licenses').document(clinic_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return {
                    "active": data.get('active', False),
                    "expiration_date": data.get('expiration_date')
                }
            return {"active": False, "expiration_date": None}
        except Exception as e:
            logger.error(f"Erreur lecture Firebase pour {clinic_id} : {e}")
            return {"active": None, "expiration_date": None}

    async def write_license(self, public_id: str, active: bool, expiration_date=None) -> bool:
        """Écrit/Met à jour l'entrée de licence dans Firestore (appelé par le dashboard SuperAdmin)."""
        if not self._db:
            return False
        try:
            doc_ref = self._db.collection('licenses').document(public_id)
            data = {"active": active}
            if expiration_date:
                data["expiration_date"] = expiration_date
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            logger.error(f"Erreur écriture Firebase pour {public_id}: {e}")
            return False
