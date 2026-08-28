from backend import models
from backend.config import settings
from backend import seed_user


class _FakeQuery:
    def __init__(self, existing):
        self.existing = existing

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.existing


class _FakeDB:
    def __init__(self, existing=None, assigned_id=17):
        self.existing = existing
        self.assigned_id = assigned_id
        self.added = None
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def query(self, _model):
        return _FakeQuery(self.existing)

    def add(self, value):
        self.added = value

    def flush(self):
        if self.added is not None and getattr(self.added, "id", None) is None:
            self.added.id = self.assigned_id

    def commit(self):
        self.committed = True

    def refresh(self, _value):
        return None

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_seed_requires_explicit_password_and_never_generates_one(monkeypatch, capsys):
    db = _FakeDB()
    monkeypatch.setattr(seed_user, "SessionLocal", lambda: db)
    monkeypatch.setattr(settings, "SUPERADMIN_DISPLAY_EMAIL", "owner@example.com")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 0)
    monkeypatch.delenv("SUPERADMIN_INITIAL_PASSWORD", raising=False)

    result = seed_user.seed_admin_user()
    output = capsys.readouterr().out

    assert result is None
    assert db.added is None
    assert db.committed is False
    assert "SUPERADMIN_INITIAL_PASSWORD requis" in output
    assert "généré" in output


def test_seed_bootstrap_email_does_not_grant_platform_authority(monkeypatch, capsys):
    db = _FakeDB(assigned_id=17)
    monkeypatch.setattr(seed_user, "SessionLocal", lambda: db)
    monkeypatch.setattr(settings, "SUPERADMIN_DISPLAY_EMAIL", "owner@example.com")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 0)
    monkeypatch.setenv("SUPERADMIN_INITIAL_PASSWORD", "BootstrapPass123!")

    result = seed_user.seed_admin_user()
    output = capsys.readouterr().out

    assert result is not None
    assert result.id == 17
    assert result.email == "owner@example.com"
    assert result.role == models.UserRole.ADMIN
    assert db.committed is True
    assert "BootstrapPass123!" not in output
    assert "Provisionnez SUPERADMIN_USER_ID" in output
    # ID 0 remains fail-closed: creating the bootstrap account does not itself grant root authority.
    from backend.platform_access import is_platform_superadmin
    assert is_platform_superadmin(result) is False


def test_seed_rejects_existing_owner_id_mismatch(monkeypatch, capsys):
    existing = models.User(
        id=17,
        email="owner@example.com",
        hashed_password="unused",
        role=models.UserRole.ADMIN,
        is_active=True,
    )
    db = _FakeDB(existing=existing)
    monkeypatch.setattr(seed_user, "SessionLocal", lambda: db)
    monkeypatch.setattr(settings, "SUPERADMIN_DISPLAY_EMAIL", "owner@example.com")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 42)

    result = seed_user.seed_admin_user()
    output = capsys.readouterr().out

    assert result is None
    assert db.rolled_back is True
    assert "ne correspond pas" in output
