"""LOT08.2-B FUE-0: executable isolated real SQLite journey + negative oracles.

Not an API/browser/physical Windows acceptance test. Fixtures only.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore, OperatorError
from queue_core.security.rbac import AuthorizationError, Permission, Role, TargetScope


def _setup(tmp_path):
    clock = [1_800_000_000]
    auth = LocalIdentityStore(
        tmp_path / "fue-b2-synthetic.sqlite",
        local_guard=lambda: None,
        clock=lambda: clock[0],
    )
    challenge = auth.begin_bootstrap()
    recovery = auth.enroll_first_admin(challenge, "labadmin", "SyntheticAdminPassword!!2026")
    root_session = auth.login("labadmin", "SyntheticAdminPassword!!2026")
    operators = LocalOperatorStore(auth, clock=lambda: clock[0])
    root_actor = operators.bind_first_admin(
        first_admin_session=root_session, tenant_id="SyntheticTenant1",
    )
    return auth, operators, root_session, root_actor, recovery, clock


def _scope(tenant="SyntheticTenant1", queue="Q1", resource="CHAIR1"):
    return TargetScope(
        tenant_id=tenant, queue_id=queue,
        visit_id="SYNTH_VISIT_1", visit_tenant_id=tenant, visit_queue_id=queue,
        resource_id=resource, resource_tenant_id=tenant, resource_queue_id=queue,
    )


def _auth_code(call, code, status):
    with pytest.raises(AuthorizationError) as exc:
        call()
    assert (exc.value.code, exc.value.status_code) == (code, status)


def test_fue_before_action_after_restart_revoke_and_offline_recovery(tmp_path):
    auth, operators, admin, _, recovery, _ = _setup(tmp_path)
    staff_id = operators.create_operator(
        admin, "labstaff", "SyntheticStaffPassword!!2026", Role.STAFF,
        queue_ids=("Q1",), resource_ids=("CHAIR1",),
        grants=(Permission.QUEUE_DONE,),
    )
    staff_token = operators.login_operator(
        "SyntheticTenant1", "labstaff", "SyntheticStaffPassword!!2026",
    )
    before = operators.authorizer()
    assert before.require(staff_token, Permission.QUEUE_DONE, _scope()).actor_id == staff_id
    _auth_code(lambda: before.require(staff_token, Permission.QUEUE_DONE, _scope("OTHER")),
               "AUTHZ_DENIED", 403)
    _auth_code(lambda: before.require(staff_token, Permission.QUEUE_CHAIR, _scope()),
               "AUTHZ_DENIED", 403)

    # Actual persistent SQLite close/reopen, not a mocked principal.
    restarted = LocalOperatorStore(auth, clock=operators._clock)
    assert restarted.authorizer().require(
        staff_token, Permission.QUEUE_DONE, _scope()
    ).actor_id == staff_id

    # Every rights update invalidates the session and audit is committed.
    operators.replace_rights(
        admin, staff_id, queue_ids=("Q2",), grants=(),
    )
    _auth_code(lambda: restarted.authorizer().require(
        staff_token, Permission.QUEUE_DONE, _scope()), "AUTH_REQUIRED", 401)
    replacement = restarted.login_operator(
        "SyntheticTenant1", "labstaff", "SyntheticStaffPassword!!2026",
    )
    _auth_code(lambda: restarted.authorizer().require(
        replacement, Permission.QUEUE_DONE, _scope()), "AUTHZ_DENIED", 403)

    # Offline A recovery is one transaction and invalidates BOTH session stores.
    new_recovery = auth.recover_admin(recovery, "NewSyntheticAdminPassword!!2026")
    assert new_recovery and new_recovery != recovery
    assert restarted.resolve_session(replacement) is None
    assert restarted.resolve_session(admin) is None
    with sqlite3.connect(auth.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM operator_sessions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM local_sessions").fetchone()[0] == 0
        actions = [row[0] for row in conn.execute("SELECT action FROM operator_audit ORDER BY id")]
    assert actions == ["first_admin_bound", "operator_created", "operator_login",
                       "rights_replaced", "operator_login"]


def test_fue_concurrent_revoke_serializes_without_stale_authorization(tmp_path):
    _, store, admin, _, _, _ = _setup(tmp_path)
    worker = store.create_operator(
        admin, "staff2", "SyntheticStaffPassword!!2026", Role.STAFF,
        queue_ids=("Q1",), resource_ids=("CHAIR1",),
    )
    session = store.login_operator("SyntheticTenant1", "staff2", "SyntheticStaffPassword!!2026")
    # Two concurrent admin writes compete for BEGIN IMMEDIATE; all resolvers
    # after both commits must fail with revoked token.
    begin = Event()

    def change(i):
        begin.wait(timeout=10)
        store.replace_rights(admin, worker, queue_ids=(f"Q{i}",))
        return i

    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = [pool.submit(change, i) for i in (2, 3)]
        begin.set()
        assert sorted(t.result(timeout=20) for t in tasks) == [2, 3]

    _auth_code(lambda: store.authorizer().require(
        session, Permission.QUEUE_READ, TargetScope("SyntheticTenant1", "Q1")),
        "AUTH_REQUIRED", 401)
    with sqlite3.connect(store.auth.path) as c:
        assert c.execute("SELECT count(*) FROM operator_audit WHERE action='rights_replaced'").fetchone()[0] == 2
        assert c.execute("SELECT count(*) FROM operator_assignments WHERE actor_id=? AND kind='queue'",
                         (worker,)).fetchone()[0] == 1


def test_fue_corrupt_sqlite_never_allows_authenticated_action(tmp_path):
    auth, store, admin, _, _, _ = _setup(tmp_path)
    operator = store.create_operator(
        admin, "staff3", "SyntheticStaffPassword!!2026", Role.STAFF,
        queue_ids=("Q1",),
    )
    token = store.login_operator("SyntheticTenant1", "staff3", "SyntheticStaffPassword!!2026")
    with sqlite3.connect(auth.path) as c:
        c.execute("PRAGMA ignore_check_constraints=ON")
        c.execute("UPDATE operators SET role='INVALID_ROLE' WHERE actor_id=?", (operator,))
    # Damaged persisted role cannot become an authorized principal.
    assert store.resolve_session(token) is None
    _auth_code(lambda: store.authorizer().require(
        token, Permission.OPERATOR_MANAGE, TargetScope("SyntheticTenant1")),
        "AUTH_REQUIRED", 401)
