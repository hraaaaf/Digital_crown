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

_WEAK_LOCAL_VAULT_KEYS = {
    "SET_A_REAL_SECRET_KEY_IN_ENV",
    "dev_only_secret_key_change_me",
    "default-dc-fallback-key",
    "changeme",
    "secret",
}


class LicenseService:
    _instance = None
    _db = None
    OFFLINE_GRACE_HOURS = 72

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
                    logger.warning(
                        "Firebase credentials missing. Local database decryption and "
                        "offline verification will be enforced."
                    )
            except Exception as e:
                logger.error(f"Failed to init Firebase: {e}")
        return cls._instance

    @staticmethod
    def _as_utc(value: datetime.datetime | None) -> datetime.datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)

    @staticmethod
    def _vault_path():
        return AppPaths.get_user_data_dir() / "license_vault.bin"

    @staticmethod
    def _local_vault_master_key() -> str:
        master_key = (
            os.getenv("CABINET_MASTER_KEY_HEX")
            or os.getenv("SECRET_KEY")
            or ""
        ).strip()
        if (
            not master_key
            or master_key in _WEAK_LOCAL_VAULT_KEYS
            or len(master_key) < 32
        ):
            raise RuntimeError(
                "Local licence vault key unavailable: configure a strong destination-local secret."
            )
        return master_key

    def _get_fernet(self) -> Fernet:
        key_32bytes = hashlib.sha256(self._local_vault_master_key().encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_32bytes)
        return Fernet(fernet_key)

    def _read_local_vault(self) -> dict:
        vault_path = self._vault_path()
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
        vault_path = self._vault_path()
        try:
            vault_path.parent.mkdir(parents=True, exist_ok=True)
            f = self._get_fernet()
            raw_bytes = json.dumps(data).encode()
            encrypted_data = f.encrypt(raw_bytes)
            vault_path.write_bytes(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to write/encrypt local license vault: {e}")

    def _clear_local_vault(self) -> None:
        vault_path = self._vault_path()
        try:
            vault_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear local license vault: {e}")

    def _validate_offline_vault(
        self,
        clinic_id: str,
        now: datetime.datetime,
    ) -> dict:
        logger.warning("🔌 Mode hors-ligne détecté. Analyse du délai de grâce local...")
        local_data = self._read_local_vault()
        if not local_data:
            logger.warning("⚠️ Aucune preuve de licence locale trouvée.")
            return {"active": False, "expiration_date": None, "source": "offline"}

        if local_data.get("clinic_id") != clinic_id:
            logger.error("❌ Conflit d'identifiant de cabinet dans le coffre-fort local.")
            return {"active": False, "expiration_date": None, "source": "offline"}

        try:
            last_validated = self._as_utc(
                datetime.datetime.fromisoformat(local_data["last_validated"])
            )
            max_seen_time = self._as_utc(
                datetime.datetime.fromisoformat(local_data["max_seen_time"])
            )
            expiration_str = local_data.get("expiration_date")
            expiration = self._as_utc(
                datetime.datetime.fromisoformat(expiration_str)
            ) if expiration_str else None
        except Exception as e:
            logger.error(f"❌ Données de licence locales corrompues : {e}")
            return {"active": False, "expiration_date": None, "source": "offline"}

        if now < last_validated or now < max_seen_time:
            logger.critical(
                "🚨 Horloge système reculée : preuve de licence locale refusée."
            )
            return {"active": False, "expiration_date": expiration, "source": "offline"}

        if expiration and now > expiration:
            logger.error(f"❌ La licence a expiré le {expiration}.")
            return {"active": False, "expiration_date": expiration, "source": "offline"}

        grace_limit = last_validated + datetime.timedelta(hours=self.OFFLINE_GRACE_HOURS)
        if now > grace_limit:
            logger.error("❌ Délai de grâce de 72 heures expiré.")
            return {"active": False, "expiration_date": expiration, "source": "offline"}

        local_data["max_seen_time"] = now.isoformat()
        self._write_local_vault(local_data)
        remaining_hours = int((grace_limit - now).total_seconds() / 3600)
        logger.warning(
            f"🛡️ Mode dégradé hors-ligne actif. Temps restant : {remaining_hours} heures."
        )
        return {"active": True, "expiration_date": expiration, "source": "offline"}

    async def validate_license(self, clinic_id: str) -> bool:
        """Validate online when possible, otherwise apply the strict local grace policy."""
        result = await self.validate_license_with_expiry(clinic_id)
        if result.get("active") is None:
            result = self._validate_offline_vault(
                clinic_id,
                datetime.datetime.now(datetime.timezone.utc),
            )
        return bool(result.get("active"))

    async def validate_license_with_expiry(self, clinic_id: str) -> dict:
        """
        Read the authoritative Firebase licence state without destroying local truth.

        active=None means Firebase is unavailable/not configured. Startup callers
        must preserve SQLite state in that case; validate_license() separately
        applies the 72-hour offline vault policy for request-time validation.
        """
        now = datetime.datetime.now(datetime.timezone.utc)

        if not self._db:
            return {
                "active": None,
                "expiration_date": None,
                "source": "unavailable",
            }

        try:
            doc_ref = self._db.collection("licenses").document(clinic_id)
            doc = doc_ref.get()
            if not doc.exists:
                self._clear_local_vault()
                logger.warning(
                    f"⚠️ Aucun document de licence trouvé pour le cabinet '{clinic_id}'."
                )
                return {
                    "active": False,
                    "expiration_date": None,
                    "source": "firebase",
                }

            data = doc.to_dict()
            is_active = bool(data.get("active", False))
            expiration = self._as_utc(data.get("expiration_date"))

            if not is_active:
                self._clear_local_vault()
                logger.error(
                    f"❌ La licence du cabinet '{clinic_id}' a été désactivée."
                )
                return {
                    "active": False,
                    "expiration_date": expiration,
                    "source": "firebase",
                }

            if expiration and now > expiration:
                self._clear_local_vault()
                logger.error(
                    f"❌ La licence du cabinet '{clinic_id}' a expiré le {expiration}."
                )
                return {
                    "active": False,
                    "expiration_date": expiration,
                    "source": "firebase",
                }

            self._write_local_vault(
                {
                    "clinic_id": clinic_id,
                    "last_validated": now.isoformat(),
                    "expiration_date": expiration.isoformat() if expiration else None,
                    "max_seen_time": now.isoformat(),
                }
            )
            logger.info(
                "✅ Licence validée en ligne avec succès. Coffre-fort local mis à jour."
            )
            return {
                "active": True,
                "expiration_date": expiration,
                "source": "firebase",
            }
        except Exception as e:
            logger.error(
                f"❌ Échec de la vérification de licence en ligne : {e}. "
                "État local conservé."
            )
            return {
                "active": None,
                "expiration_date": None,
                "source": "unavailable",
            }

    async def write_license(self, public_id: str, active: bool, expiration_date=None) -> bool:
        """Écrit/Met à jour l'entrée de licence dans Firestore (dashboard SuperAdmin)."""
        if not self._db:
            return False
        try:
            doc_ref = self._db.collection("licenses").document(public_id)
            data = {"active": active}
            if expiration_date:
                data["expiration_date"] = expiration_date
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            logger.error(f"Erreur écriture Firebase pour {public_id}: {e}")
            return False
