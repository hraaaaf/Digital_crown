"""08.2-A synthetic local identity safety checks; never touch clinic data."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading

import pytest

from queue_core.security.local_auth import (
    LocalIdentityError, LocalIdentityStore,
    BOOTSTRAP_TTL_SECONDS, SESSION_TTL_SECONDS, LOCK_SECONDS,
)
from queue_core.security.windows_console import LocalConsoleRequired


@pytest.fixture
def env(tmp_path):
    now = [1_700_000_000]
    guard = [True]

    def privileged():
        if not guard[0]:
            raise LocalConsoleRequired("LOCAL_CONSOLE_REQUIRED")

    store = LocalIdentityStore(
        tmp_path / "dedicated-identity.sqlite",
        local_guard=privileged,
        clock=lambda: now[0],
    )
    return store, now, guard


def initialize(env):
    store, _, _ = env
    code = store.begin_bootstrap()
    offline = store.enroll_first_admin(code, "owner.admin", "CorrectHorseWithEntropy123!")
    return offline


def test_one_time_bootstrap_no_plaintext_credentials_or_clinical_tables(env):
    store, _, _ = env
    assert not store.path.exists()
    challenge = store.begin_bootstrap()
    assert 40 <= len(challenge) <= 64
    assert not store.is_initialized()
    offline = store.enroll_first_admin(
        challenge, "Owner.Admin", "CorrectHorseWithEntropy123!"
    )
    assert store.is_initialized()
    assert len(offline) >= 40 and offline != challenge
    with pytest.raises(LocalIdentityError, match="BOOTSTRAP_ALREADY_CLAIMED"):
        store.enroll_first_admin(challenge, "other", "NewVeryStrongPassword123!")
    with pytest.raises(LocalIdentityError, match="BOOTSTRAP_ALREADY_CLAIMED"):
        store.begin_bootstrap()
    raw = store.path.read_bytes()
    assert challenge.encode() not in raw
    assert offline.encode() not in raw
    assert b"CorrectHorseWithEntropy123!" not in raw
    with sqlite3.connect(store.path) as c:
        tables = {x[0] for x in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert tables.issuperset({
        "auth_meta", "local_admin", "local_sessions", "local_auth_audit"
    })
    assert not any("patient" in x or "appointment" in x for x in tables)


def test_bootstrap_code_expiry_and_new_issue_revokes_old(env):
    store, now, _ = env
    first = store.begin_bootstrap()
    now[0] += BOOTSTRAP_TTL_SECONDS
    with pytest.raises(LocalIdentityError, match="BOOTSTRAP_INVALID"):
        store.enroll_first_admin(first, "owner", "CorrectHorseWithEntropy123!")
    second = store.begin_bootstrap()
    with pytest.raises(LocalIdentityError, match="BOOTSTRAP_INVALID"):
        store.enroll_first_admin(first, "owner", "CorrectHorseWithEntropy123!")
    assert store.enroll_first_admin(second, "owner", "CorrectHorseWithEntropy123!")


def test_five_invalid_bootstrap_attempts_fail_closed_until_reissue(env):
    store, _, _ = env
    code = store.begin_bootstrap()
    for i in range(5):
        with pytest.raises(LocalIdentityError, match="BOOTSTRAP_INVALID"):
            store.enroll_first_admin("wrong", "owner", "CorrectHorseWithEntropy123!")
    with pytest.raises(LocalIdentityError, match="BOOTSTRAP_LOCKED"):
        store.enroll_first_admin(code, "owner", "CorrectHorseWithEntropy123!")
    fresh = store.begin_bootstrap()
    assert store.enroll_first_admin(fresh, "owner", "CorrectHorseWithEntropy123!")


def test_bootstrap_concurrent_claim_has_exactly_one_winner(env):
    store, _, _ = env
    token = store.begin_bootstrap()
    barrier = threading.Barrier(2)

    def attempt(i):
        barrier.wait()
        try:
            recovery = store.enroll_first_admin(
                token, f"owner{i}", "CorrectHorseWithEntropy123!"
            )
            return ("success", recovery)
        except LocalIdentityError as error:
            return ("denied", str(error))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))
    assert [x[0] for x in results].count("success") == 1
    assert [x[0] for x in results].count("denied") == 1


def test_login_session_opaque_expiry_revoke_and_no_secrets_in_database(env):
    store, now, _ = env
    offline = initialize(env)
    session = store.login("OWNER.ADMIN", "CorrectHorseWithEntropy123!")
    assert len(session) >= 40
    assert store.session_valid(session)
    assert not store.session_valid(session + "_wrong")
    data = store.path.read_bytes()
    assert session.encode() not in data and offline.encode() not in data
    assert store.revoke_session(session)
    assert not store.session_valid(session)
    assert not store.revoke_session(session)
    token = store.login("owner.admin", "CorrectHorseWithEntropy123!")
    now[0] += SESSION_TTL_SECONDS
    assert not store.session_valid(token)


def test_bruteforce_locked_then_valid_login_after_lock(env):
    store, now, _ = env
    initialize(env)
    for _ in range(5):
        with pytest.raises(LocalIdentityError, match="INVALID_CREDENTIALS"):
            store.login("owner.admin", "wrong")
    with pytest.raises(LocalIdentityError, match="TEMPORARILY_LOCKED"):
        store.login("owner.admin", "CorrectHorseWithEntropy123!")
    now[0] += LOCK_SECONDS
    assert store.login("owner.admin", "CorrectHorseWithEntropy123!")


def test_unknown_username_does_not_login(env):
    store, _, _ = env
    initialize(env)
    with pytest.raises(LocalIdentityError, match="INVALID_CREDENTIALS"):
        store.login("somebodyelse", "CorrectHorseWithEntropy123!")


def test_recovery_rotates_offline_secret_revokes_sessions_and_old_password(env):
    store, _, _ = env
    original = initialize(env)
    token = store.login("owner.admin", "CorrectHorseWithEntropy123!")
    rotated = store.recover_admin(original, "NewVeryStrongPassword456!")
    assert rotated != original
    assert not store.session_valid(token)
    with pytest.raises(LocalIdentityError, match="INVALID_CREDENTIALS"):
        store.login("owner.admin", "CorrectHorseWithEntropy123!")
    assert store.login("owner.admin", "NewVeryStrongPassword456!")
    with pytest.raises(LocalIdentityError, match="RECOVERY_INVALID"):
        store.recover_admin(original, "AnotherStrongPassword789!")
    assert store.recover_admin(rotated, "AnotherStrongPassword789!")


def test_recovery_rate_limit_and_unlock(env):
    store, now, _ = env
    offline = initialize(env)
    for _ in range(5):
        with pytest.raises(LocalIdentityError, match="RECOVERY_INVALID"):
            store.recover_admin("invalid-offline", "NewVeryStrongPassword456!")
    with pytest.raises(LocalIdentityError, match="RECOVERY_LOCKED"):
        store.recover_admin(offline, "NewVeryStrongPassword456!")
    now[0] += LOCK_SECONDS
    assert store.recover_admin(offline, "NewVeryStrongPassword456!")


def test_bootstrap_and_recovery_denied_without_local_elevated_guard(env):
    store, _, guard = env
    guard[0] = False
    assert not store.path.exists()
    with pytest.raises(LocalConsoleRequired):
        store.begin_bootstrap()
    assert not store.path.exists()
    guard[0] = True
    offline = initialize(env)
    guard[0] = False
    with pytest.raises(LocalConsoleRequired):
        store.begin_bootstrap()
    with pytest.raises(LocalConsoleRequired):
        store.enroll_first_admin("any", "owner", "CorrectHorseWithEntropy123!")
    with pytest.raises(LocalConsoleRequired):
        store.recover_admin(offline, "NewVeryStrongPassword456!")


def test_policy_rejects_invalid_username_and_password(env):
    store, _, _ = env
    challenge = store.begin_bootstrap()
    for username in ("", "a", "with spaces", "ü"):
        with pytest.raises(LocalIdentityError, match="USERNAME_POLICY"):
            store.enroll_first_admin(challenge, username, "CorrectHorseWithEntropy123!")
    for pw in ("", "short", "x" * 129, "secret\x00hidden"):
        with pytest.raises(LocalIdentityError, match="PASSWORD_POLICY"):
            store.enroll_first_admin(challenge, "owner", pw)
    assert store.enroll_first_admin(challenge, "owner", "CorrectHorseWithEntropy123!")


def test_audit_never_contains_sensitive_values(env):
    store, _, _ = env
    challenge = store.begin_bootstrap()
    offline = store.enroll_first_admin(challenge, "owner", "CorrectHorseWithEntropy123!")
    store.login("owner", "CorrectHorseWithEntropy123!")
    try:
        store.recover_admin("wrong", "NewVeryStrongPassword456!")
    except LocalIdentityError:
        pass
    with sqlite3.connect(store.path) as c:
        rows = c.execute("SELECT action,outcome FROM local_auth_audit").fetchall()
    assert rows
    assert all(action in {"bootstrap_issued", "bootstrap_claim", "login", "recovery", "logout"}
               and outcome in {"ok", "denied"} for action, outcome in rows)
    assert offline.encode() not in store.path.read_bytes()


def test_missing_database_login_fails_without_creating_files(env):
    store, _, _ = env
    with pytest.raises(LocalIdentityError, match="LOCAL_AUTH_NOT_INITIALIZED"):
        store.login("owner", "any")
    assert not store.path.exists()
