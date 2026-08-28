import os
import json
import base64
import hashlib
import datetime
import logging
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet
from firebase_admin import firestore, credentials, initialize_app

from backend.config import settings
from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter
from backend.license_security import LicenseSecurityError, VerifiedLicense, verify_license
from backend.license_trust import TRUSTED_LICENSE_PUBLIC_KEYS

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
                        pass
                    cls._db = firestore.client()
                else:
                    logger.warning(
                        "Firebase credentials missing. Local signed-license "
                        "verification and offline grace will be enforced."
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
        return Fernet(base64.urlsafe_b64encode(key_32bytes))

    def _read_local_vault(self) -> dict:
        vault_path = self._vault_path()
        if not vault_path.exists():
            return {}
        try:
            decrypted_data = self._get_fernet().decrypt(vault_path.read_bytes())
            value = json.loads(decrypted_data.decode())
            return value if isinstance(value, dict) else {}
        except Exception as e:
            logger.error(f"Failed to read/decrypt local license vault: {e}")
            return {}

    def _write_local_vault(self, data: dict) -> bool:
        """Atomically persist the local signed-licence vault.

        Existing callers may ignore the boolean, but activation/install paths use
        it as a hard gate so local commercial state is never committed when the
        cryptographic proof could not actually be persisted.
        """
        vault_path = self._vault_path()
        temp_path: Path | None = None
        platform_adapter = get_platform_adapter()
        try:
            vault_path.parent.mkdir(parents=True, exist_ok=True)
            encrypted_data = self._get_fernet().encrypt(json.dumps(data).encode())
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{vault_path.name}.",
                suffix=".tmp",
                dir=str(vault_path.parent),
            )
            temp_path = Path(temp_name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(encrypted_data)
                handle.flush()
                os.fsync(handle.fileno())
            if not platform_adapter.is_windows:
                temp_path.chmod(0o600)
            os.replace(temp_path, vault_path)
            if not platform_adapter.is_windows:
                vault_path.chmod(0o600)
            return True
        except Exception as e:
            logger.error(f"Failed to write/encrypt local license vault: {e}")
            return False
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _clear_local_vault(self) -> None:
        try:
            self._vault_path().unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear local license vault: {e}")

    @staticmethod
    def _verify_signed_license(
        signed_license: str,
        clinic_id: str,
        now: datetime.datetime,
        *,
        allow_inactive: bool = False,
    ) -> VerifiedLicense:
        verified = verify_license(
            signed_license,
            TRUSTED_LICENSE_PUBLIC_KEYS,
            expected_cabinet_id=clinic_id,
            now=now,
            allow_inactive=allow_inactive,
        )

        # OWNER is the sole commercial exemption and must be cryptographically
        # tied to the immutable platform owner id. A copied OWNER token cannot
        # become valid merely by editing an email, role or local user record.
        if verified.license_type == "OWNER":
            configured_owner_id = int(getattr(settings, "SUPERADMIN_USER_ID", 0) or 0)
            if configured_owner_id <= 0:
                raise LicenseSecurityError(
                    "OWNER license cannot be trusted before SUPERADMIN_USER_ID is provisioned"
                )
            if verified.subject_user_id != configured_owner_id:
                raise LicenseSecurityError("OWNER subject mismatch")

        return verified

    @staticmethod
    def _verified_result(verified: VerifiedLicense, source: str) -> dict:
        return {
            "active": verified.status == "ACTIVE",
            "expiration_date": verified.expires_at,
            "source": source,
            "license_type": verified.license_type,
            "feature_set": verified.claims.get("feature_set"),
            "release_channel": verified.claims.get("release_channel"),
            "license_id": verified.license_id,
            "key_id": verified.key_id,
        }

    def install_signed_license(self, clinic_id: str, signed_license: str) -> dict:
        """Verify a control-plane token and install it into the local cabinet vault.

        This is the cabinet-safe activation boundary: no Firebase service account
        or signing key is required. The token must verify against an embedded
        trusted public key and the exact local cabinet id before any local mirror
        may be marked licensed.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        verified = self._verify_signed_license(signed_license, str(clinic_id), now)
        if verified.status != "ACTIVE":
            raise LicenseSecurityError("license is not active")

        vault = {
            "clinic_id": str(clinic_id),
            "signed_license": signed_license,
            "last_validated": now.isoformat(),
            "max_seen_time": now.isoformat(),
        }
        if not self._write_local_vault(vault):
            raise RuntimeError("signed licence could not be persisted locally")

        # Read-back is part of the install transaction. A write that cannot be
        # decrypted/parsed immediately is not accepted as installed.
        read_back = self._read_local_vault()
        if (
            read_back.get("clinic_id") != str(clinic_id)
            or read_back.get("signed_license") != signed_license
        ):
            self._clear_local_vault()
            raise RuntimeError("signed licence local persistence verification failed")
        return self._verified_result(verified, "activation")

    def _validate_offline_vault(
        self,
        clinic_id: str,
        now: datetime.datetime,
    ) -> dict:
        logger.warning("Mode hors-ligne détecté. Vérification de la preuve signée locale...")
        local_data = self._read_local_vault()
        if not local_data:
            logger.warning("Aucune preuve de licence locale trouvée.")
            return {"active": False, "expiration_date": None, "source": "offline"}
        if local_data.get("clinic_id") != clinic_id:
            logger.error("Conflit d'identifiant de cabinet dans le coffre-fort local.")
            return {"active": False, "expiration_date": None, "source": "offline"}

        signed_license = local_data.get("signed_license")
        if not isinstance(signed_license, str) or not signed_license:
            logger.error("Coffre local legacy/non signé refusé.")
            return {"active": False, "expiration_date": None, "source": "offline"}

        try:
            verified = self._verify_signed_license(signed_license, clinic_id, now)
            last_validated = self._as_utc(datetime.datetime.fromisoformat(local_data["last_validated"]))
            max_seen_time = self._as_utc(datetime.datetime.fromisoformat(local_data["max_seen_time"]))
        except (LicenseSecurityError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Preuve de licence locale invalide : {e}")
            return {"active": False, "expiration_date": None, "source": "offline"}

        expiration = verified.expires_at
        if now < last_validated or now < max_seen_time:
            logger.critical("Horloge système reculée : preuve de licence locale refusée.")
            return {"active": False, "expiration_date": expiration, "source": "offline"}

        grace_limit = last_validated + datetime.timedelta(hours=self.OFFLINE_GRACE_HOURS)
        if now > grace_limit:
            logger.error(f"Délai de grâce de {self.OFFLINE_GRACE_HOURS} heures expiré.")
            return {"active": False, "expiration_date": expiration, "source": "offline"}

        local_data["max_seen_time"] = now.isoformat()
        self._write_local_vault(local_data)
        remaining_hours = int((grace_limit - now).total_seconds() / 3600)
        logger.warning(f"Mode dégradé hors-ligne actif. Temps restant : {remaining_hours} heures.")
        return self._verified_result(verified, "offline")

    async def get_effective_license(self, clinic_id: str) -> dict:
        """Return the effective signed entitlement, falling back to the signed offline vault."""
        result = await self.validate_license_with_expiry(clinic_id)
        if result.get("active") is None:
            result = self._validate_offline_vault(
                clinic_id,
                datetime.datetime.now(datetime.timezone.utc),
            )
        return result

    async def validate_license(self, clinic_id: str) -> bool:
        result = await self.get_effective_license(clinic_id)
        return bool(result.get("active"))

    async def validate_license_with_expiry(self, clinic_id: str) -> dict:
        """Validate Firebase truth cryptographically, preserving offline state on outages."""
        now = datetime.datetime.now(datetime.timezone.utc)
        if not self._db:
            return {"active": None, "expiration_date": None, "source": "unavailable"}

        try:
            doc = self._db.collection("licenses").document(clinic_id).get()
        except Exception as e:
            logger.error(
                f"Échec de lecture Firebase pour '{clinic_id}': {e}. État local conservé."
            )
            return {"active": None, "expiration_date": None, "source": "unavailable"}

        if not doc.exists:
            self._clear_local_vault()
            logger.warning(f"Aucun document de licence trouvé pour le cabinet '{clinic_id}'.")
            return {"active": False, "expiration_date": None, "source": "firebase"}

        data = doc.to_dict() or {}
        signed_license = data.get("signed_license")
        if not isinstance(signed_license, str) or not signed_license:
            self._clear_local_vault()
            logger.error(f"Licence legacy/non signée refusée pour le cabinet '{clinic_id}'.")
            return {
                "active": False,
                "expiration_date": None,
                "source": "firebase",
                "reason": "unsigned_license",
            }

        try:
            verified = self._verify_signed_license(signed_license, clinic_id, now)
        except LicenseSecurityError as e:
            self._clear_local_vault()
            logger.error(f"Licence signée invalide pour '{clinic_id}': {e}")
            return {
                "active": False,
                "expiration_date": None,
                "source": "firebase",
                "reason": "invalid_signature_or_claims",
            }

        self._write_local_vault(
            {
                "clinic_id": clinic_id,
                "signed_license": signed_license,
                "last_validated": now.isoformat(),
                "max_seen_time": now.isoformat(),
            }
        )
        logger.info("Licence signée validée en ligne. Coffre local mis à jour.")
        return self._verified_result(verified, "firebase")

    async def write_signed_license(self, public_id: str, signed_license: str) -> bool:
        """Write only a cryptographically authentic license, including REVOKED tombstones."""
        if not self._db:
            return False

        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            verified = self._verify_signed_license(
                signed_license,
                public_id,
                now,
                allow_inactive=True,
            )
        except LicenseSecurityError as e:
            logger.error(f"Refus d'écriture d'une licence invalide pour {public_id}: {e}")
            return False

        try:
            doc_ref = self._db.collection("licenses").document(public_id)
            doc_ref.set(
                {
                    "signed_license": signed_license,
                    # Informational mirrors only. Client authority remains the signed token.
                    "active": verified.status == "ACTIVE",
                    "expiration_date": verified.expires_at,
                    "license_type": verified.license_type,
                    "feature_set": verified.claims.get("feature_set"),
                    "release_channel": verified.claims.get("release_channel"),
                    "license_id": verified.license_id,
                    "key_id": verified.key_id,
                },
                merge=True,
            )
            return True
        except Exception as e:
            logger.error(f"Erreur écriture Firebase pour {public_id}: {e}")
            return False

    async def write_license(self, public_id: str, active: bool, expiration_date=None) -> bool:
        """Legacy unsigned writer intentionally disabled by SEC-1."""
        raise RuntimeError(
            "Unsigned license writes are disabled. Issue and store a signed license instead."
        )