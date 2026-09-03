"""Fail-closed deployment topology for privileged platform sessions."""
import pytest
from pydantic import ValidationError

from backend.config import Settings


def test_control_plane_rejects_non_production_environment():
    with pytest.raises(ValidationError, match="exige ENVIRONMENT=production"):
        Settings(
            ENVIRONMENT="development",
            PLATFORM_CONTROL_PLANE_ENABLED=True,
            APP_PUBLIC_URL="https://admin.example.test",
            FRONTEND_URL="https://admin.example.test",
            ALLOWED_ORIGINS="https://admin.example.test",
        )


def test_control_plane_rejects_http_public_url():
    with pytest.raises(ValidationError, match="APP_PUBLIC_URL doit utiliser HTTPS"):
        Settings(
            ENVIRONMENT="production",
            PLATFORM_CONTROL_PLANE_ENABLED=True,
            APP_PUBLIC_URL="http://admin.example.test",
            FRONTEND_URL="https://admin.example.test",
            ALLOWED_ORIGINS="https://admin.example.test",
        )


def test_control_plane_rejects_http_cors_origin():
    with pytest.raises(ValidationError, match="uniquement des origines HTTPS"):
        Settings(
            ENVIRONMENT="production",
            PLATFORM_CONTROL_PLANE_ENABLED=True,
            APP_PUBLIC_URL="https://admin.example.test",
            FRONTEND_URL="https://admin.example.test",
            ALLOWED_ORIGINS="https://admin.example.test,http://127.0.0.1:5173",
        )


def test_control_plane_accepts_explicit_https_production_topology():
    cfg = Settings(
        ENVIRONMENT="production",
        PLATFORM_CONTROL_PLANE_ENABLED=True,
        APP_PUBLIC_URL="https://admin.example.test",
        FRONTEND_URL="https://admin.example.test",
        ALLOWED_ORIGINS="https://admin.example.test",
    )
    assert cfg.ENVIRONMENT == "production"
    assert cfg.PLATFORM_CONTROL_PLANE_ENABLED is True
    assert all(
        origin.startswith("https://")
        for origin in cfg.ALLOWED_ORIGINS.split(",")
    )
