"""B06 per-capture native metadata protocol FUE-0, no network or patient data."""
import dataclasses

import pytest

from tools.imaging_gateway.native_inventory_protocol_v15 import (
    DENIED, EMPTY, FRAME_BYTES, NativeInventoryDenied,
    decode_inventory, encode_inventory,
)
from tools.imaging_gateway.unassigned_queue_v15 import UnassignedCapture


@pytest.fixture
def capture():
    return UnassignedCapture(
        id=17, digest="a" * 64, size=991,
        mime="image/png", category="RADIOGRAPH",
    )


def test_b06_round_trip_no_patient_or_media_capture(capture):
    frame = encode_inventory(capture)
    assert len(frame) == FRAME_BYTES == 86
    assert frame.startswith(b"I1")
    assert decode_inventory(frame) == capture
    assert set(dataclasses.asdict(decode_inventory(frame))) == {
        "id", "digest", "size", "mime", "category",
    }
    assert all(word not in frame for word in (
        b"patient", b"dossier", b"appointment", b"filename", b"staff", b"PNG",
    ))
    assert decode_inventory(encode_inventory(None)) is None
    assert decode_inventory(EMPTY) is None
    print("DC06_B06_NATIVE_FRAME_NON_PHI_CANONICAL_PASS")


@pytest.mark.parametrize("mutate", [
    lambda f: f[:-1], lambda f: f + b"X",
    lambda f: b"E2", lambda f: b"", lambda f: b"N1",
    lambda f: f[:2] + b"X" + f[3:],
    lambda f: f[:12] + b"Z" + f[13:],
    lambda f: f[:20] + b"F" + f[21:],
    lambda f: f[:84] + b"X" + f[85:],
    lambda f: f[:85] + b"X",
    lambda f: f[:2] + b"0000000000" + f[12:],
    lambda f: f[:12] + b"00000000" + f[20:],
    lambda f: f[:20] + b"A" * 64 + f[84:],
])
def test_b06_malformed_frame_denied(capture, mutate):
    with pytest.raises(NativeInventoryDenied):
        decode_inventory(mutate(encode_inventory(capture)))


@pytest.mark.parametrize("change", [
    {"id": 0}, {"id": 10_000_000_000},
    {"size": 0}, {"size": -1}, {"size": 52_428_801},
    {"mime": "image/gif"}, {"category": "UNKNOWN"},
    {"digest": "A" * 64}, {"digest": "f" * 63},
])
def test_b06_invalid_queue_metadata_denied(capture, change):
    with pytest.raises(NativeInventoryDenied):
        encode_inventory(dataclasses.replace(capture, **change))


def test_b06_adapter_disabled_outside_disposable_windows_vm(monkeypatch):
    from backend.services.imaging_acquisition_native_inventory_v15 import read_native_unassigned

    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    monkeypatch.setenv("DC06_B06_NATIVE_INVENTORY_LAB", "1")
    with pytest.raises(NativeInventoryDenied, match="LAB_DISABLED"):
        read_native_unassigned(r"\\.\pipe\DigitalCrown-LAB-R-" + "0" * 32)
    with pytest.raises(NativeInventoryDenied, match="LAB_DISABLED"):
        read_native_unassigned(r"\\evil\pipe\DigitalCrown-LAB-R-" + "0" * 32)
    print("DC06_B06_NATIVE_ADAPTER_NO_CABINET_PASS")


@pytest.mark.parametrize("invalid", [None, 0, -1, True, "123", 0x100000000])
def test_b06_bs2_native_bridge_requires_trusted_scm_pid(invalid):
    from tools.imaging_gateway.native_product_bridge_v15 import windows_native_bridge
    from tools.imaging_gateway.native_inventory_windows_v15 import _require_server_pid

    with pytest.raises(NativeInventoryDenied, match="NATIVE_PIPE_SERVER_PID_REQUIRED"):
        _require_server_pid(invalid)
    with pytest.raises(NativeInventoryDenied, match="NATIVE_BRIDGE_SERVER_PID_REQUIRED"):
        windows_native_bridge(
            tenant_id=1, workstation_id="DC06B06_LAB_STATION",
            pipe_name=r"\\\\.\\pipe\\DigitalCrown-LAB-R-" + "0" * 32,
            expected_server_pid=invalid,
        )


def test_b06_bs2_native_bridge_constructor_preserves_server_pin():
    from tools.imaging_gateway.native_product_bridge_v15 import windows_native_bridge

    native = windows_native_bridge(
        tenant_id=1, workstation_id="DC06B06_LAB_STATION",
        pipe_name=r"\\\\.\\pipe\\DigitalCrown-LAB-R-" + "0" * 32,
        expected_server_pid=34567,
    )
    assert native.tenant_id == 1
    assert native.workstation_id == "DC06B06_LAB_STATION"
    print("DC06_B06_BS2_BRIDGE_TRUSTED_PID_REQUIRED_FAIL_CLOSED_PASS")
