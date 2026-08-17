import pytest

from backend import env_loader


def test_cabinet_without_crypto_secret_fails_closed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.delenv("CABINET_MASTER_KEY_HEX", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="mode cabinet refuse"):
        env_loader._enforce_cabinet_crypto_secret()


@pytest.mark.parametrize("weak", [
    "default-dc-fallback-key",
    "changeme",
    "secret",
    "too-short",
])
def test_cabinet_rejects_weak_shared_secret(monkeypatch, weak):
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.delenv("CABINET_MASTER_KEY_HEX", raising=False)
    monkeypatch.setenv("SECRET_KEY", weak)

    with pytest.raises(RuntimeError):
        env_loader._enforce_cabinet_crypto_secret()


def test_cabinet_accepts_strong_dedicated_master_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "a" * 64)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    env_loader._enforce_cabinet_crypto_secret()


def test_non_cabinet_keeps_development_flexibility(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.delenv("CABINET_MASTER_KEY_HEX", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    env_loader._enforce_cabinet_crypto_secret()
