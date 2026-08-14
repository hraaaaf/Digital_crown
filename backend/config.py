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
    MOBILE_TOKEN_EXPIRE_HOURS: int = 24             # P1-2: bearer mobile court, ré-appairage explicite
    
    # Database
    DATABASE_URL: str = "sqlite:///./digital_crown.db"
    
    # Environment
    ENVIRONMENT: str = "development"
    APP_PUBLIC_URL: str = "http://localhost:5173"
    SUPPORT_EMAIL: str = "support@digitalcrown.local"
    SUPERADMIN_EMAIL: str = "benmoussa.achraf@gmail.com"

    # Security
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173,https://127.0.0.1:5173"
    RATE_LIMIT_LOGIN: str = "10/minute"

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
