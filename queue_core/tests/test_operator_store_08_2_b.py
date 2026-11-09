"""B-2 synthetic SQLite/operator RBAC: no clinic data, credentials or production files."""
import sqlite3

import pytest

from queue_core.security.local_auth import LocalIdentityError, LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore, OperatorError
from queue_core.security.rbac import (
    AuthorizationError, Permission as P, Role, TargetScope,
)


PASSWORD = "SyntheticAdminStrongPassword!2026"
STAFF_PASSWORD = "SyntheticOperatorSecret!2026"
NEW_PASSWORD = "SyntheticRotatedSecret!2026"


@pytest.fixture
def lab(tmp_path):
    tick = [1_800_000_000]
    auth = LocalIdentityStore(
        tmp_path / "sandbox-auth.sqlite", local_guard=lambda: None,
        clock=lambda: tick[0],
    )
    challenge = auth.begin_bootstrap()
    recovery = auth.enroll_first_admin(challenge, "seedadmin", PASSWORD)
    admin_token = auth.login("seedadmin", PASSWORD)
    operators = LocalOperatorStore(auth, clock=lambda: tick[0])
    root_id = operators.bind_first_admin(first_admin_session=admin_token, tenant_id="T1")
    return auth, operators, admin_token, root_id, recovery, tick


def denies(function, code="AUTHZ_DENIED", status=403):
    with pytest.raises(AuthorizationError) as error:
        function()
    assert error.value.code == code
    assert error.value.status_code == status


def test_bootstrap_admin_is_bound_and_admin_has_no_queue_power(lab):
    _, store, token, root_id, _, _ = lab
    p = store.resolve_session(token)
    assert p.actor_id == root_id and p.tenant_id == "T1"
    assert p.roles == frozenset({Role.ADMIN})
    assert not p.queue_ids and not p.resource_ids
    assert store.authorizer().require(token, P.OPERATOR_MANAGE, TargetScope("T1"))
    denies(lambda: store.authorizer().require(token, P.QUEUE_CALL, TargetScope("T1", "Q1")))
    denies(lambda: store.authorizer().require(token, P.OPERATOR_MANAGE, TargetScope("T2")))
    with pytest.raises(OperatorError, match="ALREADY_PROVISIONED"):
        store.bind_first_admin(first_admin_session=token, tenant_id="T2")


def test_disabled_local_guard_prevents_first_tenant_binding(tmp_path):
    auth = LocalIdentityStore(tmp_path / "local.sqlite", local_guard=lambda: None)
    challenge = auth.begin_bootstrap()
    auth.enroll_first_admin(challenge, "seedadmin", PASSWORD)
    token = auth.login("seedadmin", PASSWORD)
    blocked = LocalIdentityStore(
        auth.path, local_guard=lambda: (_ for _ in ()).throw(LocalIdentityError("LOCAL_ONLY")),
    )
    with pytest.raises(LocalIdentityError, match="LOCAL_ONLY"):
        LocalOperatorStore(blocked).bind_first_admin(first_admin_session=token, tenant_id="T1")


def test_reception_persistence_and_tenant_idor_refusals(lab):
    auth, store, admin, _, _, tick = lab
    person = store.create_operator(admin, "reception1", STAFF_PASSWORD, Role.RECEPTION, queue_ids=["Q1"])
    token = store.login_operator("T1", "reception1", STAFF_PASSWORD)
    independently_reopened = LocalOperatorStore(auth, clock=lambda: tick[0])
    assert independently_reopened.resolve_session(token).actor_id == person
    a = independently_reopened.authorizer()
    assert a.require(token, P.QUEUE_READ, TargetScope("T1", "Q1")).actor_id == person
    denies(lambda: a.require(token, P.QUEUE_READ, TargetScope("T2", "Q1")))
    denies(lambda: a.require(token, P.QUEUE_READ, TargetScope("T1", "Q2")))
    denies(lambda: a.require(token, P.AUDIT_EXPORT, TargetScope("T1")))
    with pytest.raises(OperatorError, match="AUTHZ_DENIED"):
        store.create_operator(token, "eviluser", STAFF_PASSWORD, Role.ADMIN)


def test_assignment_and_grant_change_revoke_old_session_atomically(lab):
    _, store, admin, _, _, _ = lab
    person = store.create_operator(admin, "staff01", STAFF_PASSWORD, Role.STAFF,
                                   queue_ids=["Q1"], resource_ids=["C1"], grants=[P.QUEUE_DONE])
    token = store.login_operator("T1", "staff01", STAFF_PASSWORD)
    target = TargetScope("T1", "Q1", "V1", "T1", "Q1", "C1", "T1", "Q1")
    assert store.authorizer().require(token, P.QUEUE_DONE, target)
    store.replace_rights(admin, person, queue_ids=["Q2"], grants=[])
    denies(lambda: store.authorizer().require(token, P.QUEUE_DONE, target), "AUTH_REQUIRED", 401)
    next_token = store.login_operator("T1", "staff01", STAFF_PASSWORD)
    denies(lambda: store.authorizer().require(next_token, P.QUEUE_DONE, target))
    assert store.authorizer().require(next_token, P.QUEUE_READ, TargetScope("T1", "Q2"))
    denies(lambda: store.authorizer().require(next_token, P.QUEUE_READ, TargetScope("T1", "Q1")))


def test_override_and_no_show_are_explicit_and_role_restricted(lab):
    _, store, admin, _, _, _ = lab
    with pytest.raises(OperatorError, match="INVALID_GRANT"):
        store.create_operator(admin, "badstaff", STAFF_PASSWORD, Role.STAFF, grants=[P.QUEUE_NO_SHOW])
    with pytest.raises(OperatorError, match="INVALID_GRANT"):
        store.create_operator(admin, "badreception", STAFF_PASSWORD, Role.RECEPTION, grants=[P.QUEUE_DONE])
    actor = store.create_operator(admin, "reception2", STAFF_PASSWORD, Role.RECEPTION,
                                  queue_ids=["Q1"], grants=[P.QUEUE_NO_SHOW, P.QUEUE_OVERRIDE])
    token = store.login_operator("T1", "reception2", STAFF_PASSWORD)
    v = TargetScope("T1", "Q1", "V1", "T1", "Q1")
    assert store.authorizer().require(token, P.QUEUE_NO_SHOW, v)
    denies(lambda: store.authorizer().require(token, P.QUEUE_OVERRIDE, v),
           "OVERRIDE_REASON_REQUIRED")
    assert store.authorizer().require(token, P.QUEUE_OVERRIDE, v, reason="synthetic reason")
    store.replace_rights(admin, actor, grants=[])
    assert store.resolve_session(token) is None


def test_bootstrap_admin_immutable_preserves_last_admin(lab):
    _, store, admin, root_id, _, _ = lab
    with pytest.raises(OperatorError, match="BOOTSTRAP_ADMIN_IMMUTABLE"):
        store.disable_operator(admin, root_id)
    with pytest.raises(OperatorError, match="BOOTSTRAP_ADMIN_IMMUTABLE"):
        store.replace_rights(admin, root_id, role=Role.STAFF)
    assert store.resolve_session(admin).roles == frozenset({Role.ADMIN})
    another = store.create_operator(admin, "admin002", STAFF_PASSWORD, Role.ADMIN)
    store.disable_operator(admin, another)
    assert store.resolve_session(admin).roles == frozenset({Role.ADMIN})


def test_disable_operator_and_password_reset_deny_old_tokens(lab):
    _, store, admin, _, _, _ = lab
    person = store.create_operator(admin, "operator3", STAFF_PASSWORD, Role.STAFF, queue_ids=["Q1"])
    t1 = store.login_operator("T1", "operator3", STAFF_PASSWORD)
    store.reset_password(admin, person, NEW_PASSWORD)
    assert store.resolve_session(t1) is None
    with pytest.raises(OperatorError, match="INVALID_CREDENTIALS"):
        store.login_operator("T1", "operator3", STAFF_PASSWORD)
    t2 = store.login_operator("T1", "operator3", NEW_PASSWORD)
    assert store.resolve_session(t2) is not None
    store.disable_operator(admin, person)
    assert store.resolve_session(t2) is None
    with pytest.raises(OperatorError, match="INVALID_CREDENTIALS"):
        store.login_operator("T1", "operator3", NEW_PASSWORD)


def test_recovery_revokes_all_operator_and_bootstrap_sessions(lab):
    auth, store, admin, _, recovery, _ = lab
    store.create_operator(admin, "operator4", STAFF_PASSWORD, Role.STAFF, queue_ids=["Q1"])
    worker = store.login_operator("T1", "operator4", STAFF_PASSWORD)
    assert store.resolve_session(worker)
    replacement = auth.recover_admin(recovery, NEW_PASSWORD)
    assert replacement and replacement != recovery
    assert store.resolve_session(worker) is None
    assert store.resolve_session(admin) is None
    fresh = auth.login("seedadmin", NEW_PASSWORD)
    assert store.resolve_session(fresh).roles == frozenset({Role.ADMIN})


def test_no_unapproved_tenant_scope_and_no_plain_password_at_rest(lab):
    auth, store, admin, _, _, _ = lab
    actor = store.create_operator(admin, "operator5", STAFF_PASSWORD, Role.STAFF, queue_ids=["Q1"])
    with sqlite3.connect(auth.path) as c:
        row = c.execute("SELECT tenant_id,username,password_digest FROM operators WHERE actor_id=?", (actor,)).fetchone()
        assert row[0] == "T1" and row[1] == "operator5"
        assert STAFF_PASSWORD not in str(row) and len(row[2]) == 64
        assert c.execute("SELECT count(*) FROM operator_audit").fetchone()[0] >= 2
        with pytest.raises(sqlite3.DatabaseError, match="APPEND_ONLY_AUDIT"):
            c.execute("DELETE FROM operator_audit")


def test_logins_are_rate_limited_and_session_expiration_fails_closed(lab):
    _, store, admin, _, _, tick = lab
    store.create_operator(admin, "operator6", STAFF_PASSWORD, Role.STAFF, queue_ids=["Q1"])
    with pytest.raises(OperatorError, match="INVALID_CREDENTIALS"):
        store.login_operator("T2", "operator6", STAFF_PASSWORD)
    for _ in range(5):
        with pytest.raises(OperatorError, match="INVALID_CREDENTIALS"):
            store.login_operator("T1", "operator6", "DefinitelyWrongPassword!")
    with pytest.raises(OperatorError, match="INVALID_CREDENTIALS"):
        store.login_operator("T1", "operator6", STAFF_PASSWORD)
    tick[0] += 901
    token = store.login_operator("T1", "operator6", STAFF_PASSWORD)
    assert store.resolve_session(token)
    tick[0] += 8*3600
    assert store.resolve_session(token) is None


def test_second_session_revoked_and_audit_same_transaction(lab):
    auth, store, admin, _, _, _ = lab
    actor = store.create_operator(admin, "operator7", STAFF_PASSWORD, Role.STAFF)
    token1 = store.login_operator("T1", "operator7", STAFF_PASSWORD)
    token2 = store.login_operator("T1", "operator7", STAFF_PASSWORD)
    assert store.revoke_session(token1)
    assert store.resolve_session(token1) is None
    assert store.resolve_session(token2) is not None
    with sqlite3.connect(auth.path) as c:
        assert c.execute("SELECT count(*) FROM operator_audit WHERE action='operator_logout'").fetchone()[0] == 1
    store.disable_operator(admin, actor)
    assert store.resolve_session(token2) is None


def test_duplicate_user_is_atomic_and_old_admin_session_is_not_tenant_client_controlled(lab):
    auth, store, admin, _, _, _ = lab
    store.create_operator(admin, "operator8", STAFF_PASSWORD, Role.RECEPTION, queue_ids=["Q1"])
    with pytest.raises(sqlite3.IntegrityError):
        store.create_operator(admin, "operator8", STAFF_PASSWORD, Role.STAFF, queue_ids=["Q2"])
    with sqlite3.connect(auth.path) as c:
        assert c.execute("SELECT count(*) FROM operators WHERE username='operator8'").fetchone()[0] == 1
        assert c.execute("SELECT count(*) FROM operator_assignments WHERE scope_id='Q2'").fetchone()[0] == 0
    assert store.authorizer().require(admin, P.OPERATOR_MANAGE, TargetScope("T1"))
    denies(lambda: store.authorizer().require(admin, P.OPERATOR_MANAGE, TargetScope("T2")))


def test_audit_insert_failure_rolls_back_rights_and_session_revocation(lab):
    auth, store, admin, _, _, _ = lab
    actor = store.create_operator(admin, "operator9", STAFF_PASSWORD, Role.STAFF,
                                  queue_ids=["Q1"], grants=[P.QUEUE_CHAIR])
    session = store.login_operator("T1", "operator9", STAFF_PASSWORD)
    with sqlite3.connect(auth.path) as c:
        c.execute("""CREATE TRIGGER synthetic_audit_write_failure
                    BEFORE INSERT ON operator_audit BEGIN
                    SELECT RAISE(ABORT, 'AUDIT_UNAVAILABLE'); END""")
    with pytest.raises(sqlite3.DatabaseError, match="AUDIT_UNAVAILABLE"):
        store.replace_rights(admin, actor, queue_ids=["Q2"], grants=[])
    assert store.resolve_session(session).queue_ids == frozenset({"Q1"})
    assert P.QUEUE_CHAIR in store.resolve_session(session).explicit_permissions


def test_corrupt_rights_fail_closed_not_auto_promoted(lab):
    auth, store, admin, _, _, _ = lab
    actor = store.create_operator(admin, "operator10", STAFF_PASSWORD, Role.STAFF)
    session = store.login_operator("T1", "operator10", STAFF_PASSWORD)
    with sqlite3.connect(auth.path) as c:
        c.execute("INSERT INTO operator_grants(actor_id,permission) VALUES(?,?)",
                  (actor, "not.a.permission"))
    assert store.resolve_session(session) is None
    denies(lambda: store.authorizer().require(session, P.QUEUE_READ, TargetScope("T1","Q1")),
           "AUTH_REQUIRED", 401)


def test_unrecognized_first_admin_token_cannot_bind_tenant(tmp_path):
    auth = LocalIdentityStore(tmp_path / "local.sqlite", local_guard=lambda: None)
    challenge = auth.begin_bootstrap()
    auth.enroll_first_admin(challenge, "seedadmin", PASSWORD)
    store = LocalOperatorStore(auth)
    with pytest.raises(OperatorError, match="AUTH_REQUIRED"):
        store.bind_first_admin(first_admin_session="not-a-valid-session", tenant_id="T1")
    with sqlite3.connect(auth.path) as c:
        assert c.execute("SELECT 1 FROM sqlite_master WHERE name='operators'").fetchone() is None


def test_sql_guard_prevents_bootstrap_mutation_and_last_admin_bypass(lab):
    auth, _, _, root_id, _, _ = lab
    with sqlite3.connect(auth.path) as c:
        with pytest.raises(sqlite3.IntegrityError, match="LAST_ADMIN_REQUIRED"):
            c.execute("UPDATE operators SET enabled=0 WHERE actor_id=?", (root_id,))
        c.rollback()
        with pytest.raises(sqlite3.IntegrityError, match="BOOTSTRAP_ADMIN_IMMUTABLE"):
            c.execute("DELETE FROM operators WHERE actor_id=?", (root_id,))
        c.rollback()
        with pytest.raises(sqlite3.IntegrityError, match="BOOTSTRAP_ADMIN_IMMUTABLE"):
            c.execute("UPDATE operators SET tenant_id='T2' WHERE actor_id=?", (root_id,))
        c.rollback()
        assert c.execute("SELECT enabled,role,tenant_id FROM operators WHERE actor_id=?",
                         (root_id,)).fetchone() == (1, "admin", "T1")
