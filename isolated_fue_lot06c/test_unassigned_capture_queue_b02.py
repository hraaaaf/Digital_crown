"""B02 FUE: actual AES-GCM/SQLite encrypted unassigned queue without receipt."""
from dataclasses import asdict
import pytest

from tools.imaging_gateway import GatewayError, HotFolder
from tools.imaging_gateway.unassigned_queue_v15 import read_unassigned
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _setup, _counts, synthetic_sqlcipher_bridge,
)


def test_b02_encrypted_unassigned_queue_is_read_only_restartable_and_not_clinical(
    synthetic_sqlcipher_bridge, tmp_path,
):
    (engine, _claim, _device, _station, _media, source, collector, item,
     raw, _private, _challenge, _headers, _app, _key) = _setup(
        synthetic_sqlcipher_bridge, tmp_path,
    )
    assert _counts(engine) == (0, 0, 0)
    before = collector.items()
    queue = read_unassigned(collector)
    assert len(queue) == 1
    capture = queue[0]
    assert (capture.id, capture.digest, capture.size, capture.mime) == (
        item["id"], item["digest"], len(raw), "image/png",
    )
    assert set(asdict(capture)) == {"id", "digest", "size", "mime", "category"}
    assert not (set(asdict(capture)) & {
        "patient", "patient_id", "appointment", "appointment_id", "filename", "staff",
        "source_path", "receipt_id",
    })
    assert collector.items() == before and _counts(engine) == (0, 0, 0)
    encrypted = list(collector.spool.glob("*.dc6"))
    assert len(encrypted) == 1 and raw not in encrypted[0].read_bytes()
    restarted = HotFolder(collector.config)
    assert read_unassigned(restarted) == queue
    assert restarted.read_verified(capture.id) == raw
    assert source.read_bytes() == raw
    print("DC06B02_REAL_AESGCM_UNASSIGNED_QUEUE_RESTART_NO_PATIENT_NO_RECEIPT_PASS")


def test_b02_tampered_ciphertext_fails_closed_and_does_not_issue_receipt(
    synthetic_sqlcipher_bridge, tmp_path,
):
    (engine, _claim, _device, _station, _media, _source, collector, item,
     _raw, _private, _challenge, _headers, _app, _key) = _setup(
        synthetic_sqlcipher_bridge, tmp_path,
    )
    assert read_unassigned(collector)
    file = next(collector.spool.glob("*.dc6"))
    blob = file.read_bytes()
    file.write_bytes(blob[:-1] + bytes([blob[-1] ^ 1]))
    with pytest.raises((GatewayError, ValueError, OSError)):
        read_unassigned(collector)
    assert _counts(engine) == (0, 0, 0)
    print("DC06B02_UNASSIGNED_TAMPER_NO_RECEIPT_PASS")


def test_b02_nonpending_unassigned_queue_is_not_visible_and_limit_rejected(
    synthetic_sqlcipher_bridge, tmp_path,
):
    (engine, _claim, _device, _station, _media, _source, collector, item,
     _raw, _private, _challenge, _headers, _app, _key) = _setup(
        synthetic_sqlcipher_bridge, tmp_path,
    )
    for limit in (0, 26, True, -1, "5"):
        with pytest.raises(GatewayError, match="INVALID_UNASSIGNED_QUEUE_REQUEST"):
            read_unassigned(collector, limit=limit)
    collector.record_transport_failure(item["id"], 1700000000)
    assert read_unassigned(collector) == ()
    assert _counts(engine) == (0, 0, 0)
    print("DC06B02_QUEUE_RETRY_NOT_AUTOMATICALLY_PUBLISHED_PASS")
