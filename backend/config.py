from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.env_loader import BASE_DIR

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Digital Crown API"
    DEBUG: bool = False
    SECRET_KEY: str = "SET_A_REAL_SECRET_KEY_IN_ENV"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30            # 30 minutes (rotation via refresh token)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30             # 30 jours

    # Database
    DATABASE_URL: str = "sqlite:///./digital_crown.db"

    # Environment
    ENVIRONMENT: str = "development"
    APP_PUBLIC_URL: str = "http://localhost:5173"
    SUPPORT_EMAIL: str = "support@digitalcrown.local"
    # Legacy compatibility only. Authorization by email is deliberately disabled.
    # Existing code that still reads this setting therefore fails closed.
    SUPERADMIN_EMAIL: str = ""
    # Optional display/bootstrap contact. Never use as an authorization root.
    SUPERADMIN_DISPLAY_EMAIL: str = "benmoussa.achraf@gmail.com"
    # Immutable server-side identity used for platform SuperAdmin authorization.
    # 0 means "not provisioned" and therefore fails closed.
    SUPERADMIN_USER_ID: int = 0
    # Platform administration/signing surfaces are absent logically from cabinet
    # installs unless this control-plane switch is explicitly provisioned server-side.
    PLATFORM_CONTROL_PLANE_ENABLED: bool = False

    # Security
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173,https://127.0.0.1:5173"
    RATE_LIMIT_LOGIN: str = "10/minute"

    @field_validator("SUPERADMIN_EMAIL", mode="before")
    @classmethod
    def disable_legacy_superadmin_email_authority(cls, _value: str) -> str:
        """SEC-1: legacy env values cannot reactivate email-based SuperAdmin authority."""
        return ""

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def include_stable_mobile_origin(cls, value: str) -> str:
        """M6-I: a legacy .env must not silently omit the stable WebAuthn origin."""
        stable = "https://digitalcrown.local:5173"
        origins = [item.strip() for item in str(value).split(",") if item.strip()]
        if stable not in origins:
            origins.append(stable)
        return ",".join(origins)

    # Télémétrie / remontée cloud (P0.1) — OFF par défaut, opt-in EXPLICITE.
    # Tant que ce flag est False, AUCUNE statistique ne quitte le cabinet.
    TELEMETRY_ENABLED: bool = False

    # Storage
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 # 10 Mo

    # Firebase
    # Les clés Firebase sont gérées par le fichier firebase_creds.json

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # Transactional Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@digitalcrown.local"
    SMTP_FROM_NAME: str = "Digital Crown"
    SMTP_USE_TLS: bool = True
    ADMIN_NOTIFICATION_EMAIL: str = ""

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env.local"), str(BASE_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()