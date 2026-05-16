import datetime
import logging
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
                # Initialisation silencieuse de Firebase
                # En mode EXE, on peut inclure le JSON des credentials dans les ressources
                cred_path = AppPaths.get_base_dir() / "backend" / "core" / "firebase_creds.json"
                if cred_path.exists():
                    cred = credentials.Certificate(str(cred_path))
                    initialize_app(cred)
                    cls._db = firestore.client()
                else:
                    logger.warning("Firebase credentials missing. Running in trial mode offline.")
            except Exception as e:
                logger.error(f"Failed to init Firebase: {e}")
        return cls._instance

    async def validate_license(self, clinic_id: str) -> bool:
        """
        Vérifie si le cabinet a toujours le droit d'utiliser l'application.
        """
        if not self._db:
            # Mode dégradé si pas de réseau/creds : on autorise par défaut pour le MVP
            # ou on refuse selon ta politique de sécurité stricte.
            return True 

        try:
            doc_ref = self._db.collection('licenses').document(clinic_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                is_active = data.get('active', False)
                expiration = data.get('expiration_date')

                if not is_active:
                    return False

                if expiration:
                    # Comparaison avec la date actuelle (UTC)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if now > expiration:
                        return False

                return True
            else:
                # Nouvelle licence : on peut créer une période d'essai auto ici
                return True
        except Exception as e:
            logger.error(f"License check failed: {e}")
            return True # Best effort : on laisse passer si le serveur Firebase est inaccessible
