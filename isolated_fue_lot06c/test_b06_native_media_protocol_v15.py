"""LOT06 B06 — synthetic byte transfer protocol negative FUE, not clinical."""
from dataclasses import replace
import pytest

from tools.imaging_gateway.native_inventory_protocol_v15 import (
    NativeInventoryDenied, UnassignedCapture,
)
from tools.imaging_gateway.native_media_protocol_v15 import (
    DENIED, LAB_MEDIA_MAX, MAX_CHUNK, REQUEST_BYTES,
    encode_request, decode_request, encode_response, decode_response,
)


@pytest.fixture
def capture():
    return UnassignedCapture(
        id=1, digest="a" * 64, size=MAX_CHUNK + 11,
        mime="image/png", category="PHOTO",
    )


def test_b06_binary_protocol_exact_request_and_two_chunks(capture):
    commands = (
        encode_request(capture, 0, MAX_CHUNK),
        encode_request(capture, MAX_CHUNK, 11),
    )
    assert [len(c) for c in commands] == [REQUEST_BYTES] * 2
    assert [decode_request(c) for c in commands] == [
        (1, "a" * 64, 0, MAX_CHUNK), (1, "a" * 64, MAX_CHUNK, 11),
    ]
    assert commands[0].startswith(b"M")
    first = b"\x89PNG" + bytes((i * 17) % 256 for i in range(MAX_CHUNK - 4))
    second = b"\x00\xff" + b"A" * 9
    assert decode_response(encode_response(first), MAX_CHUNK) == first
    assert decode_response(encode_response(second), 11) == second
    assert decode_response(encode_response(first), MAX_CHUNK) + second == first + second
    print("DC06_B06_NATIVE_MEDIA_BINARY_FRAME_TWO_CHUNKS_PASS")


@pytest.mark.parametrize("bad", [
    lambda data: data[:-1],
    lambda data: data + b"\0",
    lambda data: b"X" + data[1:],
    lambda data: data[:1] + b"X" + data[2:],
    lambda data: data[:11] + b"F" + data[12:],
    lambda data: data[:75] + b"A" + data[76:],
    lambda data: data[:83] + b"-" + data[84:],
    lambda data: b"M" + b"0" * 10 + data[11:],
    lambda data: data[:75] + b"99999999" + data[83:],
    lambda data: data[:83] + b"9999",
])
def test_b06_binary_rejects_invalid_request_frames(capture, bad):
    frame = encode_request(capture, 0, 3)
    with pytest.raises(NativeInventoryDenied):
        decode_request(bad(frame))


@pytest.mark.parametrize("delta", [
    {"id": 0}, {"digest": "F" * 64},
    {"size": LAB_MEDIA_MAX + 1},
    {"mime": "image/gif"},
])
def test_b06_encode_request_rejects_untrusted_capture(capture, delta):
    with pytest.raises(NativeInventoryDenied):
        encode_request(replace(capture, **delta), 0, 3)


@pytest.mark.parametrize("offset,count", [
    (-1, 1), (0, 0), (0, MAX_CHUNK + 1),
    (MAX_CHUNK + 11, 1), (MAX_CHUNK + 10, 2),
    (True, 1), (0, False),
])
def test_b06_encode_request_denies_invalid_ranges(capture, offset, count):
    with pytest.raises(NativeInventoryDenied):
        encode_request(capture, offset, count)


@pytest.mark.parametrize("bad", [
    DENIED, b"", b"D00", b"D0000", b"X0002ZZ",
    b"D0002Z", b"D0001AB", b"D0002abc",
    b"DxxxxAB", b"D0002AB!", b"D0002A",
])
def test_b06_binary_response_requires_exact_header_and_length(bad):
    with pytest.raises(NativeInventoryDenied):
        decode_response(bad, 2)


def test_b06_media_adapter_refuses_without_explicit_disposable_lab_flag(monkeypatch, capture):
    monkeypatch.delenv("DC06_B06_NATIVE_MEDIA_LAB", raising=False)
    from tools.imaging_gateway.native_media_windows_v15 import read_native_capture_bytes
    with pytest.raises(NativeInventoryDenied, match="LAB_DISABLED"):
        read_native_capture_bytes(r"\\.\pipe\DigitalCrown-LAB-R-" + "0" * 32, capture)
    print("DC06_B06_NATIVE_MEDIA_NO_CABINET_ACCESS_PASS")


def test_b06_bs2_media_requires_server_pid_before_native_io(monkeypatch, capture):
    from tools.imaging_gateway import native_media_windows_v15 as transport
    from tools.imaging_gateway.native_inventory_windows_v15 import _require_server_pid

    monkeypatch.setenv("DC06_B06_NATIVE_MEDIA_LAB", "1")
    for invalid in (None, 0, -99, True, "42", 0x100000000):
        with pytest.raises(NativeInventoryDenied, match="NATIVE_PIPE_SERVER_PID_REQUIRED"):
            _require_server_pid(invalid)
        with pytest.raises(NativeInventoryDenied, match="NATIVE_PIPE_SERVER_PID_REQUIRED"):
            transport.read_native_capture_bytes(
                r"\\\\.\\pipe\\DigitalCrown-LAB-R-" + "0" * 32,
                capture, expected_server_pid=invalid,
            )
    print("DC06_B06_BS2_MEDIA_MISSING_PIN_PREWRITE_DENIED_PASS")
