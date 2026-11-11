"""LOT08.2-C FUE-I: real isolated SQLite, live admin rights, restart and race.

All files and identities are synthetic and created under pytest tmp_path.
No patient records, hardware, network endpoints, migrations, or activation.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3

import pytest

from queue_core.security.device_pairing_lab import (
    DeviceCapability, DeviceIdentityError, DeviceKind,
)
from queue_core.security.device_store_lab import DurableDeviceStoreLab
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.rbac import AuthorizationError, Role


ADMIN_PASSWORD = "SyntheticAdminPassword!!2026"
OPERATOR_PASSWORD = "SyntheticReceptionPassword!!2026"


@pytest.fixture
def local(tmp_path):
    now = [1_800_000_000]
    auth = LocalIdentityStore(
        tmp_path / "operator-synthetic.sqlite",
        local_guard=lambda: None,
        clock=lambda: now[0],
    )
    code = auth.begin_bootstrap()
    auth.enroll_first_admin(code, "testadmin", ADMIN_PASSWORD)
    admin = auth.login("testadmin", ADMIN_PASSWORD)
    operators = LocalOperatorStore(auth, clock=lambda: now[0])
    operators.bind_first_admin(first_admin_session=admin, tenant_id="T1")
    operators.create_operator(
        admin, "reception1", OPERATOR_PASSWORD, Role.RECEPTION,
        queue_ids=("Q1",),
    )
    reception = operators.login_operator("T1", "reception1", OPERATOR_PASSWORD)
    path = tmp_path / "devices-synthetic.sqlite"
    store = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    return now, operators, admin, reception, store, path


def _issue(store, admin, device="K1", kind=DeviceKind.KIOSK):
    return store.issue(admin, tenant_id="T1", device_id=device, kind=kind)


def _pair(store, admin, device="K1", kind=DeviceKind.KIOSK):
    ticket = _issue(store, admin, device, kind)
    bearer = store.redeem(tenant_id="T1", device_id=device, ticket=ticket)
    return ticket, bearer


def test_no_implicit_creation_or_clinical_schema(local):
    _, _, admin, _, store, path = local
    assert not path.exists()
    with pytest.raises(DeviceIdentityError, match="DEVICE_STORE_NOT_INITIALIZED"):
        _issue(store, admin)
    assert not path.exists()
    store.initialize_lab()
    with pytest.raises(DeviceIdentityError, match="DEVICE_STORE_ALREADY_EXISTS"):
        store.initialize_lab()
    with sqlite3.connect(path) as db:
        tables = {row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert tables == {"devices", "device_sessions"}


def test_live_admin_only_and_tenant_binding(local):
    _, operators, admin, reception, store, _ = local
    store.initialize_lab()
    with pytest.raises(AuthorizationError):
        store.issue(
            reception, tenant_id="T1", device_id="K1",
            kind=DeviceKind.KIOSK,
        )
    with pytest.raises(AuthorizationError):
        store.issue(
            admin, tenant_id="T2", device_id="K1",
            kind=DeviceKind.KIOSK,
        )
    with pytest.raises(DeviceIdentityError, match="DEVICE_MANAGE_FORBIDDEN"):
        store.issue(
            "invalid_admin", tenant_id="T1", device_id="K1",
            kind=DeviceKind.KIOSK,
        )
    ticket = _issue(store, admin)
    assert ticket
    assert operators.revoke_session(admin)
    with pytest.raises(AuthorizationError):
        _issue(store, admin, "K2")


def test_restart_preserves_active_session_and_least_privilege(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    ticket, bearer = _pair(store, admin)
    restarted = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    principal = restarted.require(
        bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
    )
    assert principal.tenant_id == "T1"
    assert principal.device_id == "K1"
    assert principal.kind is DeviceKind.KIOSK
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        restarted.require(
            bearer, tenant_id="T1", capability=DeviceCapability.PUBLIC_QUEUE_READ,
        )
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        restarted.require(
            bearer, tenant_id="T2", capability=DeviceCapability.QR_REDEEM,
        )
    assert ticket.encode() not in path.read_bytes()
    assert bearer.encode() not in path.read_bytes()


def test_wall_cannot_redeem_qr_after_restart(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    _, bearer = _pair(store, admin, "W1", DeviceKind.WALL)
    after_restart = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    after_restart.require(
        bearer, tenant_id="T1", capability=DeviceCapability.PUBLIC_QUEUE_READ,
    )
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        after_restart.require(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        )


def test_single_use_and_wrong_device_ticket_fail(local):
    _, _, admin, _, store, _ = local
    store.initialize_lab()
    ticket = _issue(store, admin)
    with pytest.raises(DeviceIdentityError, match="PAIRING_REJECTED"):
        store.redeem(tenant_id="T1", device_id="W1", ticket=ticket)
    bearer = store.redeem(tenant_id="T1", device_id="K1", ticket=ticket)
    assert bearer
    with pytest.raises(DeviceIdentityError, match="PAIRING_REJECTED"):
        store.redeem(tenant_id="T1", device_id="K1", ticket=ticket)


def test_repair_revokes_sessions_durably(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    old_ticket, old_bearer = _pair(store, admin)
    new_ticket = store.issue(
        admin, tenant_id="T1", device_id="K1", kind=DeviceKind.WALL,
    )
    restarted = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    with pytest.raises(DeviceIdentityError, match="PAIRING_REJECTED"):
        restarted.redeem(tenant_id="T1", device_id="K1", ticket=old_ticket)
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        restarted.require(
            old_bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        )
    new_bearer = restarted.redeem(
        tenant_id="T1", device_id="K1", ticket=new_ticket,
    )
    restarted.require(
        new_bearer, tenant_id="T1",
        capability=DeviceCapability.PUBLIC_QUEUE_READ,
    )


def test_revocation_survives_restart(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    _, bearer = _pair(store, admin)
    store.revoke(admin, tenant_id="T1", device_id="K1")
    restarted = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        restarted.require(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        )


def test_expiration_survives_restart(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    ticket = store.issue(
        admin, tenant_id="T1", device_id="K1",
        kind=DeviceKind.KIOSK, ttl_seconds=60,
    )
    now[0] += 60
    restarted = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    with pytest.raises(DeviceIdentityError, match="PAIRING_REJECTED"):
        restarted.redeem(tenant_id="T1", device_id="K1", ticket=ticket)
    _, bearer = _pair(store, admin)
    now[0] += 3600
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        restarted.require(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        )


def test_concurrent_redemption_has_exactly_one_winner(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    ticket = _issue(store, admin)
    def redeem(_index):
        # Distinct connection simulates separate processes sharing one DB.
        other = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
        try:
            return other.redeem(tenant_id="T1", device_id="K1", ticket=ticket)
        except DeviceIdentityError:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(redeem, range(8)))
    assert sum(bool(x) for x in results) == 1


def test_admin_revocation_denies_device_manage_but_not_existent_device(local):
    now, operators, admin, _, store, path = local
    store.initialize_lab()
    _, bearer = _pair(store, admin)
    assert operators.revoke_session(admin)
    restarted = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])
    with pytest.raises(AuthorizationError):
        restarted.revoke(admin, tenant_id="T1", device_id="K1")
    # A device's separately-issued session is not implicitly the admin session.
    # Device revoke is still gated by a current Admin.
    restarted.require(
        bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
    )


def test_store_does_not_migrate_existing_unrelated_database(local):
    _, operators, _, _, _, path = local
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated(val INTEGER)")
    other = DurableDeviceStoreLab(operators, path, clock=lambda: 1_800_000_000)
    with pytest.raises(DeviceIdentityError, match="DEVICE_STORE_ALREADY_EXISTS"):
        other.initialize_lab()
    with sqlite3.connect(path) as db:
        tables = {r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert tables == {"unrelated"}


def test_guarded_device_session_blocks_concurrent_revocation_until_release(local):
    """Two SQLite connections serialize active device check and revocation."""
    from threading import Event
    from concurrent.futures import TimeoutError

    now, operators, admin, _, store, path = local
    store.initialize_lab()
    _, bearer = _pair(store, admin)
    verified = Event()
    allow_exit = Event()
    revoke_started = Event()
    contender = DurableDeviceStoreLab(operators, path, clock=lambda: now[0])

    def hold_authorization():
        with store._guarded_device_session(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        ) as device:
            assert device.device_id == "K1"
            verified.set()
            assert allow_exit.wait(timeout=10)

    def revoke_concurrently():
        revoke_started.set()
        contender.revoke(admin, tenant_id="T1", device_id="K1")

    with ThreadPoolExecutor(max_workers=2) as pool:
        holding = pool.submit(hold_authorization)
        assert verified.wait(timeout=8)
        revocation = pool.submit(revoke_concurrently)
        assert revoke_started.wait(timeout=8)
        # AUTH -> DEVICE lease prevents revoke taking effect mid-authorization.
        with pytest.raises(TimeoutError):
            revocation.result(timeout=0.2)
        allow_exit.set()
        holding.result(timeout=10)
        revocation.result(timeout=10)

    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        store.require(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        )


def test_guarded_device_session_denies_stale_or_wrong_tenant(local):
    _, _, admin, _, store, _ = local
    store.initialize_lab()
    _, bearer = _pair(store, admin)
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        with store._guarded_device_session(
            bearer, tenant_id="T2", capability=DeviceCapability.QR_REDEEM,
        ):
            pytest.fail("cross-tenant device guard must not open")
    store.revoke(admin, tenant_id="T1", device_id="K1")
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        with store._guarded_device_session(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        ):
            pytest.fail("revoked device guard must not open")


def test_guarded_device_session_exception_releases_both_locks(local):
    _, _, admin, _, store, _ = local
    store.initialize_lab()
    _, bearer = _pair(store, admin)
    with pytest.raises(RuntimeError, match="synthetic_abort"):
        with store._guarded_device_session(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        ):
            raise RuntimeError("synthetic_abort")
    # A crashed guarded operation must not strand either DB lock.
    store.revoke(admin, tenant_id="T1", device_id="K1")
    with pytest.raises(DeviceIdentityError, match="DEVICE_CAPABILITY_DENIED"):
        store.require(
            bearer, tenant_id="T1", capability=DeviceCapability.QR_REDEEM,
        )
