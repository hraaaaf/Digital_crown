import os
import sys
from pathlib import Path

class AppPaths:
    """
    Gestionnaire de chemins intelligent pour Digital Crown.
    Gère la transition entre le mode développement et l'exécutable PyInstaller.
    """
    @staticmethod
    def get_base_dir():
        if hasattr(sys, '_MEIPASS'):
            # Chemin temporaire PyInstaller
            return Path(sys._MEIPASS)
        # Chemin racine du projet en dev
        return Path(__file__).parent.parent.parent

    @staticmethod
    def get_user_data_dir():
        """
        Retourne le chemin vers le dossier de données utilisateur (%APPDATA% sur Windows).
        C'est ici que SQLite et le .env persistant seront stockés.
        """
        app_name = "DigitalCrown"
        if os.name == 'nt':
            base = Path(os.environ.get("APPDATA", Path.home()))
        else:
            base = Path.home() / ".config"
            
        data_dir = base / app_name
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @staticmethod
    def get_db_url():
        db_path = AppPaths.get_user_data_dir() / "clinical_vault.db"
        return f"sqlite:///{db_path}"

    @staticmethod
    def get_static_dir():
        return AppPaths.get_base_dir() / "frontend" / "dist"

    @staticmethod
    def get_model_path(model_name: str):
        return AppPaths.get_base_dir() / "backend" / "ai_models" / model_name
