"""LOT06 B06 product-side read-only native capture boundary.

A trusted local bootstrap (NOT HTTP parameters) supplies a tenant/station-bound
bridge after the Windows service has been installed and its OS identity verified.
No automatic patient linking, HTTP media streaming, ClinicalAsset or receipt.
Default product startup leaves the bridge absent and fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Callable

from tools.imaging_gateway.media_validation import validated_mime
from tools.imaging_gateway.native_inventory_protocol_v15 import (
    NativeInventoryDenied, UnassignedCapture, encode_inventory,
)
from tools.imaging_gateway.native_inventory_windows_v15 import read_native_unassigned
from tools.imaging_gateway.native_media_windows_v15 import read_native_capture_bytes

# Unassigned inventory has no patient or staff field. Limit byte reads to the
# currently certified Win32 protocol, not the future clinical-sized format.
_NATIVE_TEST_MEDIA_MAX = 16_384


@dataclass(frozen=True)
class LocalNativeCaptureBridge:
    tenant_id: int
    workstation_id: str
    inventory_reader: Callable[[], UnassignedCapture | None]
    media_reader: Callable[[UnassignedCapture], bytes]

    def _scope(self, tenant_id: int, workstation_id: str) -> None:
        if (type(self.tenant_id) is not int or self.tenant_id <= 0
                or not isinstance(self.workstation_id, str)
                or not self.workstation_id
                or int(tenant_id) != self.tenant_id
                or workstation_id != self.workstation_id):
            raise NativeInventoryDenied("NATIVE_BRIDGE_TENANT_STATION_DENIED")

    def inventory(self, *, tenant_id: int, workstation_id: str) -> UnassignedCapture | None:
        self._scope(tenant_id, workstation_id)
        capture = self.inventory_reader()
        # Canonical protocol validator prevents patient/filename fields and
        # rejects a malformed or forged native inventory record.
        encode_inventory(capture)
        return capture

    def read_verified_media(
        self, capture: UnassignedCapture, *, tenant_id: int,
        workstation_id: str,
    ) -> bytes:
        """For a future staff-bound preview, NOT an exposed API in B06-1/5."""
        self._scope(tenant_id, workstation_id)
        if (not isinstance(capture, UnassignedCapture)
                or capture.mime != "image/png"
                or type(capture.size) is not int
                or not 0 < capture.size <= _NATIVE_TEST_MEDIA_MAX):
            raise NativeInventoryDenied("NATIVE_BRIDGE_MEDIA_SCOPE_DENIED")
        if self.inventory(tenant_id=tenant_id, workstation_id=workstation_id) != capture:
            raise NativeInventoryDenied("NATIVE_BRIDGE_CAPTURE_CHANGED")
        media = self.media_reader(capture)
        if (not isinstance(media, bytes)
                or len(media) != capture.size
                or hashlib.sha256(media).hexdigest() != capture.digest
                or not validated_mime(media, capture.mime)):
            raise NativeInventoryDenied("NATIVE_BRIDGE_MEDIA_INTEGRITY_DENIED")
        if self.inventory(tenant_id=tenant_id, workstation_id=workstation_id) != capture:
            raise NativeInventoryDenied("NATIVE_BRIDGE_CAPTURE_CHANGED")
        return media


def windows_native_bridge(*, tenant_id: int, workstation_id: str,
                          pipe_name: str) -> LocalNativeCaptureBridge:
    """Uses actual Win32 SCM transport; its existing OS+LAB guards remain.

    An installer/SCM attestation must provide the trusted pipe at runtime.
    This function never accepts a pipe from an HTTP request.
    """
    return LocalNativeCaptureBridge(
        tenant_id=tenant_id,
        workstation_id=workstation_id,
        inventory_reader=lambda: read_native_unassigned(pipe_name),
        media_reader=lambda capture: read_native_capture_bytes(pipe_name, capture),
    )
