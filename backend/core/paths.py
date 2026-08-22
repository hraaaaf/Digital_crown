import sys
from pathlib import Path

from backend.core.platform import get_platform_adapter


class AppPaths:
    """Canonical filesystem paths for development and packaged Digital Crown."""

    @staticmethod
    def get_base_dir() -> Path:
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(__file__).parent.parent.parent

    @staticmethod
    def get_user_data_dir() -> Path:
        adapter = get_platform_adapter()
        return adapter.ensure_private_directory(adapter.user_data_dir())

    @staticmethod
    def get_config_dir() -> Path:
        adapter = get_platform_adapter()
        return adapter.ensure_private_directory(adapter.config_dir())

    @staticmethod
    def get_log_dir() -> Path:
        adapter = get_platform_adapter()
        return adapter.ensure_private_directory(adapter.log_dir())

    @staticmethod
    def get_runtime_dir() -> Path:
        adapter = get_platform_adapter()
        return adapter.ensure_private_directory(adapter.runtime_dir())

    @staticmethod
    def get_env_path() -> Path:
        adapter = get_platform_adapter()
        return adapter.cabinet_env_path()

    @staticmethod
    def get_db_url() -> str:
        db_path = AppPaths.get_user_data_dir() / "clinical_vault.db"
        return f"sqlite:///{db_path}"

    @staticmethod
    def get_static_dir() -> Path:
        return AppPaths.get_base_dir() / "frontend" / "dist"

    @staticmethod
    def get_model_path(model_name: str) -> Path:
        return AppPaths.get_base_dir() / "backend" / "ai_models" / model_name
