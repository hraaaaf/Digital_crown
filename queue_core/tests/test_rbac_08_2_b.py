"""LOT08.2-B synthetic authorization oracles; no patient files or real credentials."""
import pytest

from queue_core.security.rbac import (
    AuthorizationError, Permission as P, Role, VerifiedPrincipal,
    TargetScope, QueueAuthorizer,
)


def actor(role, *, tenant="T1", queues=("Q1",), resources=("C1",), grants=()):
    return VerifiedPrincipal(
        actor_id="human-1", tenant_id=tenant,
        roles=frozenset({role}), queue_ids=frozenset(queues),
        resource_ids=frozenset(resources),
        explicit_permissions=frozenset(grants),
    )


def visit_scope(tenant="T1", queue="Q1", resource=None):
    return TargetScope(
        tenant_id=tenant, queue_id=queue,
        visit_id="V1", visit_tenant_id=tenant, visit_queue_id=queue,
        resource_id=resource,
        resource_tenant_id=tenant if resource else None,
        resource_queue_id=queue if resource else None,
    )


def resolver_for(principal):
    live = {"opaque-synthetic": principal}
    return QueueAuthorizer(lambda token: live.get(token)), live


def denied(fn, code="AUTHZ_DENIED", status=403):
    with pytest.raises(AuthorizationError) as err:
        fn()
    assert err.value.code == code
    assert err.value.status_code == status


def test_missing_unknown_and_revoked_session_are_401_immediately():
    auth, sessions = resolver_for(actor(Role.RECEPTION))
    scope = TargetScope("T1", queue_id="Q1")
    denied(lambda: auth.require("", P.QUEUE_READ, scope), "AUTH_REQUIRED", 401)
    denied(lambda: auth.require("unknown", P.QUEUE_READ, scope), "AUTH_REQUIRED", 401)
    assert auth.require("opaque-synthetic", P.QUEUE_READ, scope).actor_id == "human-1"
    del sessions["opaque-synthetic"]
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, scope), "AUTH_REQUIRED", 401)


def test_resolver_error_fail_closed():
    auth = QueueAuthorizer(lambda _: 1 / 0)
    denied(lambda: auth.require("token", P.QUEUE_READ, TargetScope("T1", "Q1")), "AUTH_REQUIRED", 401)


def test_disabled_account_and_empty_roles_fail_closed():
    auth, live = resolver_for(actor(Role.RECEPTION))
    live["opaque-synthetic"] = VerifiedPrincipal("u1", "T1", frozenset({Role.RECEPTION}), active=False)
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, TargetScope("T1", "Q1")), "AUTH_REQUIRED", 401)
    live["opaque-synthetic"] = VerifiedPrincipal("u1", "T1", frozenset())
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, TargetScope("T1", "Q1")), "AUTH_REQUIRED", 401)


@pytest.mark.parametrize("role", [Role.ADMIN, Role.RECEPTION, Role.STAFF])
def test_cross_tenant_and_cross_queue_denied(role):
    auth, _ = resolver_for(actor(role))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, TargetScope("T2", "Q1")))
    if role is not Role.ADMIN:
        denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, TargetScope("T1", "Q2")))


def test_admin_configuration_and_audit_are_tenant_bound_but_not_operational():
    auth, _ = resolver_for(actor(Role.ADMIN, queues=()))
    assert auth.require("opaque-synthetic", P.OPERATOR_MANAGE, TargetScope("T1"))
    assert auth.require("opaque-synthetic", P.AUDIT_EXPORT, TargetScope("T1"))
    denied(lambda: auth.require("opaque-synthetic", P.OPERATOR_MANAGE, TargetScope("T2")))
    denied(lambda: auth.require("opaque-synthetic", P.VISIT_CHECK_IN, visit_scope()))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CALL, visit_scope(resource="C1")))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_OVERRIDE, visit_scope(), reason="urgent"))


def test_reception_scoped_create_checkin_qr_without_staff_actions():
    auth, _ = resolver_for(actor(Role.RECEPTION))
    assert auth.require("opaque-synthetic", P.VISIT_CREATE, TargetScope("T1", "Q1"))
    assert auth.require("opaque-synthetic", P.VISIT_CHECK_IN, visit_scope())
    assert auth.require("opaque-synthetic", P.QR_ISSUE, visit_scope())
    denied(lambda: auth.require("opaque-synthetic", P.VISIT_CREATE, TargetScope("T1", "Q2")))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CALL, visit_scope(resource="C1")))


def test_staff_call_recall_require_assigned_queue_and_resource():
    auth, _ = resolver_for(actor(Role.STAFF))
    assert auth.require("opaque-synthetic", P.QUEUE_CALL, visit_scope(resource="C1"))
    assert auth.require("opaque-synthetic", P.QUEUE_RECALL, visit_scope(resource="C1"))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CALL, visit_scope()))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CALL, visit_scope(resource="C2")))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CALL, visit_scope(queue="Q2", resource="C1")))


def test_chair_and_done_are_separate_explicit_per_user_grants():
    auth, live = resolver_for(actor(Role.STAFF, grants=(P.QUEUE_CHAIR,)))
    assert auth.require("opaque-synthetic", P.QUEUE_CHAIR, visit_scope(resource="C1"))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_DONE, visit_scope(resource="C1")))
    live["opaque-synthetic"] = actor(Role.STAFF, grants=(P.QUEUE_DONE,))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CHAIR, visit_scope(resource="C1")))
    assert auth.require("opaque-synthetic", P.QUEUE_DONE, visit_scope(resource="C1"))


def test_admin_and_reception_cannot_gain_chair_done_without_staff_role():
    for role in (Role.ADMIN, Role.RECEPTION):
        auth, _ = resolver_for(actor(role, grants=(P.QUEUE_CHAIR, P.QUEUE_DONE)))
        denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CHAIR, visit_scope(resource="C1")))
        denied(lambda: auth.require("opaque-synthetic", P.QUEUE_DONE, visit_scope(resource="C1")))


def test_no_show_explicit_only_for_reception_and_off_by_default():
    auth, live = resolver_for(actor(Role.RECEPTION))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_NO_SHOW, visit_scope()))
    live["opaque-synthetic"] = actor(Role.RECEPTION, grants=(P.QUEUE_NO_SHOW,))
    assert auth.require("opaque-synthetic", P.QUEUE_NO_SHOW, visit_scope())
    live["opaque-synthetic"] = actor(Role.ADMIN, grants=(P.QUEUE_NO_SHOW,))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_NO_SHOW, visit_scope()))


def test_override_requires_explicit_grant_and_nonempty_auditable_reason():
    auth, live = resolver_for(actor(Role.STAFF))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_OVERRIDE, visit_scope(), reason="reason"))
    live["opaque-synthetic"] = actor(Role.STAFF, grants=(P.QUEUE_OVERRIDE,))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_OVERRIDE, visit_scope()), "OVERRIDE_REASON_REQUIRED")
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_OVERRIDE, visit_scope(), reason=" "), "OVERRIDE_REASON_REQUIRED")
    assert auth.require("opaque-synthetic", P.QUEUE_OVERRIDE, visit_scope(), reason="emergency delay")


def test_visit_and_resource_idor_refusals():
    auth, _ = resolver_for(actor(Role.STAFF))
    invalid_visit = TargetScope("T1", "Q1", visit_id="V1", visit_tenant_id="T2", visit_queue_id="Q1")
    denied(lambda: auth.require("opaque-synthetic", P.VISIT_READ, invalid_visit))
    invalid_queue = TargetScope("T1", "Q1", visit_id="V1", visit_tenant_id="T1", visit_queue_id="Q2")
    denied(lambda: auth.require("opaque-synthetic", P.VISIT_READ, invalid_queue))
    denied(lambda: auth.require("opaque-synthetic", P.VISIT_READ, TargetScope("T1", "Q1")))
    invalid_resource = TargetScope("T1", "Q1", visit_id="V1", visit_tenant_id="T1", visit_queue_id="Q1", resource_id="C1", resource_tenant_id="T2", resource_queue_id="Q1")
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_CALL, invalid_resource))


def test_permission_unknown_and_invalid_target_fail_closed():
    auth, _ = resolver_for(actor(Role.RECEPTION))
    denied(lambda: auth.require("opaque-synthetic", "superuser", TargetScope("T1", "Q1")))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, {"tenant_id": "T1"}))


def test_same_token_rechecks_live_assignment_and_permissions_each_call():
    auth, live = resolver_for(actor(Role.STAFF, queues=("Q1",), resources=("C1",), grants=(P.QUEUE_DONE,)))
    assert auth.require("opaque-synthetic", P.QUEUE_DONE, visit_scope(resource="C1"))
    live["opaque-synthetic"] = actor(Role.STAFF, queues=("Q2",), resources=("C1",), grants=(P.QUEUE_DONE,))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_DONE, visit_scope(resource="C1")))
    live["opaque-synthetic"] = actor(Role.STAFF, queues=("Q1",), resources=("C1",))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_DONE, visit_scope(resource="C1")))


def test_queue_roles_cannot_read_global_audit_and_admin_cannot_view_queue():
    for role in (Role.RECEPTION, Role.STAFF):
        auth, _ = resolver_for(actor(role))
        denied(lambda: auth.require("opaque-synthetic", P.AUDIT_READ, TargetScope("T1")))
    auth, _ = resolver_for(actor(Role.ADMIN))
    denied(lambda: auth.require("opaque-synthetic", P.QUEUE_READ, TargetScope("T1", "Q1")))
