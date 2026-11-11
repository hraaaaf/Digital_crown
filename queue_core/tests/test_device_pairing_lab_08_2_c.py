"""08.2-C FUE-0: genuine synthetic device pairing / least privilege."""
import unittest

from queue_core.security.device_pairing_lab import (
    DeviceCapability, DeviceIdentityError, DeviceKind, DevicePairingLab,
)


class FakeClock:
    def __init__(self):
        self.now = 10000

    def __call__(self):
        return self.now


class TestDevicePairingLab(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.devices = DevicePairingLab(clock=self.clock)

    def pair(self, tenant="A", name="D1", kind=DeviceKind.KIOSK):
        code = self.devices.issue(
            tenant_id=tenant, device_id=name, kind=kind, admin_allowed=True
        )
        session = self.devices.redeem(tenant_id=tenant, device_id=name, ticket=code)
        return code, session

    def test_kiosk_may_only_redeem_qr(self):
        _, session = self.pair()
        principal = self.devices.require(
            session, tenant_id="A", capability=DeviceCapability.QR_REDEEM,
        )
        self.assertEqual(principal.kind, DeviceKind.KIOSK)
        self.assertEqual(principal.device_id, "D1")
        with self.assertRaisesRegex(DeviceIdentityError, "DEVICE_CAPABILITY_DENIED"):
            self.devices.require(
                session, tenant_id="A",
                capability=DeviceCapability.PUBLIC_QUEUE_READ,
            )

    def test_wall_is_read_only_and_cannot_redeem_qr(self):
        _, session = self.pair(kind=DeviceKind.WALL)
        self.devices.require(
            session, tenant_id="A", capability=DeviceCapability.PUBLIC_QUEUE_READ,
        )
        with self.assertRaisesRegex(DeviceIdentityError, "DEVICE_CAPABILITY_DENIED"):
            self.devices.require(
                session, tenant_id="A", capability=DeviceCapability.QR_REDEEM,
            )

    def test_redeem_is_single_use_even_after_success(self):
        ticket, _ = self.pair()
        with self.assertRaisesRegex(DeviceIdentityError, "PAIRING_REJECTED"):
            self.devices.redeem(tenant_id="A", device_id="D1", ticket=ticket)

    def test_tenant_and_device_binding_fail_closed(self):
        code = self.devices.issue(
            tenant_id="A", device_id="D1",
            kind=DeviceKind.KIOSK, admin_allowed=True,
        )
        with self.assertRaisesRegex(DeviceIdentityError, "PAIRING_REJECTED"):
            self.devices.redeem(tenant_id="B", device_id="D1", ticket=code)
        with self.assertRaisesRegex(DeviceIdentityError, "PAIRING_REJECTED"):
            self.devices.redeem(tenant_id="A", device_id="D2", ticket=code)
        valid = self.devices.redeem(tenant_id="A", device_id="D1", ticket=code)
        with self.assertRaisesRegex(DeviceIdentityError, "DEVICE_CAPABILITY_DENIED"):
            self.devices.require(
                valid, tenant_id="B", capability=DeviceCapability.QR_REDEEM,
            )

    def test_expired_pairing_and_session_are_denied(self):
        ticket = self.devices.issue(
            tenant_id="A", device_id="D1", kind=DeviceKind.KIOSK,
            admin_allowed=True, ttl_seconds=60,
        )
        self.clock.now += 60
        with self.assertRaisesRegex(DeviceIdentityError, "PAIRING_REJECTED"):
            self.devices.redeem(tenant_id="A", device_id="D1", ticket=ticket)
        _, bearer = self.pair()
        self.clock.now += 3600
        with self.assertRaisesRegex(DeviceIdentityError, "DEVICE_CAPABILITY_DENIED"):
            self.devices.require(
                bearer, tenant_id="A", capability=DeviceCapability.QR_REDEEM,
            )

    def test_revoke_invalidates_session_and_pending(self):
        _, bearer = self.pair()
        ticket = self.devices.issue(
            tenant_id="A", device_id="D2",
            kind=DeviceKind.WALL, admin_allowed=True,
        )
        self.devices.revoke(tenant_id="A", device_id="D1", admin_allowed=True)
        self.devices.revoke(tenant_id="A", device_id="D2", admin_allowed=True)
        with self.assertRaises(DeviceIdentityError):
            self.devices.require(
                bearer, tenant_id="A", capability=DeviceCapability.QR_REDEEM,
            )
        with self.assertRaises(DeviceIdentityError):
            self.devices.redeem(tenant_id="A", device_id="D2", ticket=ticket)

    def test_repair_rotates_and_invalidates_prior_session(self):
        _, bearer = self.pair()
        ticket = self.devices.issue(
            tenant_id="A", device_id="D1",
            kind=DeviceKind.WALL, admin_allowed=True,
        )
        with self.assertRaises(DeviceIdentityError):
            self.devices.require(
                bearer, tenant_id="A", capability=DeviceCapability.QR_REDEEM,
            )
        new_bearer = self.devices.redeem(tenant_id="A", device_id="D1", ticket=ticket)
        self.devices.require(
            new_bearer, tenant_id="A",
            capability=DeviceCapability.PUBLIC_QUEUE_READ,
        )

    def test_manage_permission_is_explicit(self):
        with self.assertRaisesRegex(DeviceIdentityError, "DEVICE_MANAGE_FORBIDDEN"):
            self.devices.issue(
                tenant_id="A", device_id="D1",
                kind=DeviceKind.KIOSK, admin_allowed=False,
            )
        _, bearer = self.pair()
        with self.assertRaisesRegex(DeviceIdentityError, "DEVICE_MANAGE_FORBIDDEN"):
            self.devices.revoke(tenant_id="A", device_id="D1", admin_allowed=False)
        self.devices.require(
            bearer, tenant_id="A", capability=DeviceCapability.QR_REDEEM,
        )

    def test_invalid_scope_ttl_kind_or_secret_rejected(self):
        bad = [
            dict(tenant_id=" A", device_id="D1", kind=DeviceKind.KIOSK,
                 admin_allowed=True),
            dict(tenant_id="A", device_id="D1", kind="KIOSK",
                 admin_allowed=True),
            dict(tenant_id="A", device_id="D1", kind=DeviceKind.KIOSK,
                 admin_allowed=True, ttl_seconds=59),
            dict(tenant_id="A", device_id="D1", kind=DeviceKind.KIOSK,
                 admin_allowed=True, ttl_seconds=True),
        ]
        for case in bad:
            with self.subTest(case=case), self.assertRaises(DeviceIdentityError):
                self.devices.issue(**case)
        with self.assertRaises(DeviceIdentityError):
            self.devices.require("short", tenant_id="A", capability=DeviceCapability.QR_REDEEM)


if __name__ == "__main__":
    unittest.main()
