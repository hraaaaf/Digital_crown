import pytest
from pydantic import ValidationError

from backend.config import Settings


def _settings(**overrides):
    return Settings(_env_file=None, **overrides)


def test_environment_is_normalized_to_known_value():
    settings = _settings(ENVIRONMENT=" Production ")
    assert settings.ENVIRONMENT == "production"


def test_unknown_environment_fails_closed():
    with pytest.raises(ValidationError, match="ENVIRONMENT invalide"):
        _settings(ENVIRONMENT="prodction")


def test_cabinet_cannot_enable_platform_control_plane():
    with pytest.raises(ValidationError, match="PLATFORM_CONTROL_PLANE_ENABLED interdit"):
        _settings(ENVIRONMENT="cabinet", PLATFORM_CONTROL_PLANE_ENABLED=True)


def test_cabinet_license_control_plane_url_must_be_https():
    with pytest.raises(ValidationError, match="doit utiliser HTTPS"):
        _settings(
            ENVIRONMENT="cabinet",
            LICENSE_CONTROL_PLANE_URL="http://control-plane.example.test",
        )
